using Npgsql;

sealed class Store(NpgsqlDataSource source)
{
    public NpgsqlDataSource Source => source;
    public async Task<int> Exec(string sql, params object[] values)
    {
        await using var c = source.CreateCommand(sql);
        foreach (var v in values) c.Parameters.AddWithValue(v);
        return await c.ExecuteNonQueryAsync();
    }
    public async Task<List<object[]>> Rows(string sql, params object[] values)
    {
        await using var c = source.CreateCommand(sql);
        foreach (var v in values) c.Parameters.AddWithValue(v);
        await using var r = await c.ExecuteReaderAsync();
        var rows = new List<object[]>();
        while (await r.ReadAsync()) { var row = new object[r.FieldCount]; r.GetValues(row); rows.Add(row); }
        return rows;
    }
    public Task Initialize() => Exec("""
        CREATE TABLE IF NOT EXISTS users (
          id uuid PRIMARY KEY, email text NOT NULL UNIQUE, password_hash text NOT NULL DEFAULT '',
          role text NOT NULL CHECK(role IN ('admin','user')), enabled boolean NOT NULL DEFAULT true,
          generation uuid NOT NULL, secret text NOT NULL DEFAULT '', mfa boolean NOT NULL DEFAULT false,
          last_step bigint NOT NULL DEFAULT -1, recovery text[] NOT NULL DEFAULT '{}',
          failures integer NOT NULL DEFAULT 0, locked_until timestamptz,
          created_at timestamptz NOT NULL DEFAULT now());
        CREATE TABLE IF NOT EXISTS invitations (
          id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id), token_hash text NOT NULL UNIQUE,
          expires_at timestamptz NOT NULL, used_at timestamptz, created_at timestamptz NOT NULL DEFAULT now());
        CREATE TABLE IF NOT EXISTS mail_outbox (
          id uuid PRIMARY KEY, invitation_id uuid NOT NULL REFERENCES invitations(id), recipient text NOT NULL,
          payload text NOT NULL, status text NOT NULL DEFAULT 'pending', attempts int NOT NULL DEFAULT 0,
          error text NOT NULL DEFAULT '', next_attempt timestamptz NOT NULL DEFAULT now(), accepted_at timestamptz);
        CREATE TABLE IF NOT EXISTS releases (
          id uuid PRIMARY KEY, product text NOT NULL CHECK(product IN ('components','reports','remote')),
          version text NOT NULL, platform text NOT NULL, filename text NOT NULL, storage_name text NOT NULL UNIQUE,
          size bigint NOT NULL, sha256 text NOT NULL, notes text NOT NULL DEFAULT '', published boolean NOT NULL DEFAULT true,
          created_at timestamptz NOT NULL DEFAULT now());
        CREATE TABLE IF NOT EXISTS remote_update_devices (
          id uuid PRIMARY KEY, token_hash text NOT NULL UNIQUE, code text NOT NULL UNIQUE,
          name text NOT NULL, user_id uuid REFERENCES users(id) ON DELETE CASCADE,
          created_at timestamptz NOT NULL DEFAULT now(), expires_at timestamptz NOT NULL,
          approved_at timestamptz, revoked_at timestamptz);
        CREATE TABLE IF NOT EXISTS customers (
         user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
         first_name text NOT NULL, last_name text NOT NULL,
         kind text NOT NULL CHECK(kind IN ('private','organization')),
         organization text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now());
        CREATE TABLE IF NOT EXISTS licenses (
         id uuid PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id),
         product text NOT NULL CHECK(product IN ('remote','components','reports')),
         edition text NOT NULL DEFAULT 'Standard', seats integer NOT NULL CHECK(seats BETWEEN 1 AND 100000),
         status text NOT NULL DEFAULT 'active' CHECK(status IN ('active','suspended','revoked')),
         expires_at timestamptz, updates_until timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
         legacy boolean NOT NULL DEFAULT false);
        CREATE UNIQUE INDEX IF NOT EXISTS licenses_legacy_unique ON licenses(user_id,product) WHERE legacy;
        CREATE TABLE IF NOT EXISTS license_devices (
         id uuid PRIMARY KEY, token_hash text NOT NULL UNIQUE, code text NOT NULL UNIQUE,
         product text NOT NULL CHECK(product IN ('remote','components','reports')),
         name text NOT NULL, public_key text NOT NULL, license_id uuid REFERENCES licenses(id),
         created_at timestamptz NOT NULL DEFAULT now(), pending_until timestamptz NOT NULL,
         approved_at timestamptz, revoked_at timestamptz, last_seen timestamptz,
         challenge text, challenge_until timestamptz);
        CREATE UNIQUE INDEX IF NOT EXISTS license_device_key_unique ON license_devices(license_id,public_key) WHERE revoked_at IS NULL AND license_id IS NOT NULL;
        CREATE TABLE IF NOT EXISTS licensing_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
        DO $meet$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM licensing_migrations WHERE name='meet-product-1') THEN
            ALTER TABLE releases DROP CONSTRAINT releases_product_check,
              ADD CONSTRAINT releases_product_check CHECK(product IN ('components','reports','remote','meet'));
            ALTER TABLE licenses DROP CONSTRAINT licenses_product_check,
              ADD CONSTRAINT licenses_product_check CHECK(product IN ('components','reports','remote','meet'));
            ALTER TABLE license_devices DROP CONSTRAINT license_devices_product_check,
              ADD CONSTRAINT license_devices_product_check CHECK(product IN ('components','reports','remote','meet'));
            INSERT INTO licensing_migrations(name) VALUES('meet-product-1');
          END IF;
        END $meet$;
        ALTER TABLE licenses ADD COLUMN IF NOT EXISTS session_limit integer NOT NULL DEFAULT 16 CHECK(session_limit BETWEEN 1 AND 1000);
        CREATE TABLE IF NOT EXISTS license_bootstrap_devices (token_hash text PRIMARY KEY);
        WITH migrated AS (
          INSERT INTO licensing_migrations(name) VALUES('proof-bootstrap-042') ON CONFLICT DO NOTHING RETURNING name
        )
        INSERT INTO license_bootstrap_devices(token_hash)
          SELECT d.token_hash FROM license_devices d,migrated WHERE d.revoked_at IS NULL
          UNION SELECT d.token_hash FROM remote_update_devices d,migrated WHERE d.revoked_at IS NULL;
        CREATE TABLE IF NOT EXISTS remote_computer_routes (
          device_id uuid PRIMARY KEY REFERENCES license_devices(id) ON DELETE CASCADE,
          room text NOT NULL CHECK(room ~ '^[0-9a-f]{64}$'));
        CREATE TABLE IF NOT EXISTS license_proofs (
          device_id uuid REFERENCES license_devices(id) ON DELETE CASCADE,
          nonce text NOT NULL, expires_at timestamptz NOT NULL, PRIMARY KEY(device_id,nonce));
        CREATE INDEX IF NOT EXISTS license_proofs_expiry ON license_proofs(expires_at);
        CREATE OR REPLACE VIEW eligible_license_devices AS
          SELECT ranked.* FROM (
            SELECT d.*,row_number() OVER(PARTITION BY license_id ORDER BY approved_at,id) AS seat_number
            FROM license_devices d WHERE license_id IS NOT NULL AND revoked_at IS NULL
          ) ranked JOIN licenses l ON l.id=ranked.license_id WHERE ranked.seat_number<=l.seats;
        CREATE TABLE IF NOT EXISTS audit (
          id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, actor text NOT NULL, action text NOT NULL,
          subject text NOT NULL DEFAULT '', created_at timestamptz NOT NULL DEFAULT now());
        """);
    public Task Audit(string actor, string action, string subject="") => Exec("INSERT INTO audit(actor,action,subject) VALUES($1,$2,$3)", actor, action, subject);
}
