BEGIN;
WITH first_run AS (
 INSERT INTO licensing_migrations(name) VALUES('remote-existing-access-v1') ON CONFLICT DO NOTHING RETURNING name
)
INSERT INTO licenses(id,user_id,product,edition,seats,legacy)
SELECT gen_random_uuid(),u.id,'remote','Existing access',3,true FROM users u,first_run WHERE u.enabled
ON CONFLICT(user_id,product) WHERE legacy DO NOTHING;
COMMIT;
