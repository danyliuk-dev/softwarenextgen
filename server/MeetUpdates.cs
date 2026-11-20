using System.Text.RegularExpressions;

static class MeetUpdates
{
    public static void Map(WebApplication app)
    {
        app.MapGet("/api/meet-updates/manifest/{channel}", (string channel, IConfiguration config, HttpContext ctx) => {
            if (channel != "stable" && !Regex.IsMatch(channel, @"\A[0-9]{1,9}\.[0-9]{1,9}\.[0-9]{1,9}\z")) return Results.NotFound();
            var root = config["MeetUpdatesPath"] ?? "/var/lib/nextgensoftware/meet-updates";
            ctx.Response.Headers.CacheControl = "no-store";
            var path = Path.Combine(root, channel + ".json");
            return File.Exists(path) ? Results.File(path, "application/json") : Results.NotFound();
        });
        app.MapGet("/api/meet-updates/package/{sha}/{filename}", async (string sha, string filename, HttpContext ctx, Store db, Files files) => {
            var match = Regex.Match(filename, @"\ANextgenMeet(Host|Client)-[0-9]+\.[0-9]+\.[0-9]+-(linux-x64\.deb|macos-arm64\.dmg|windows-x64\.exe)\z");
            if (!match.Success || !Regex.IsMatch(sha, @"\A[0-9a-f]{64}\z")) { ctx.Response.StatusCode=404; return; }
            if (match.Groups[1].Value == "Host") {
                var token = Licenses.Bearer(ctx);
                if (token == "" || !await Licenses.VerifyProof(ctx, db, token, "meet-package/"+sha)) { ctx.Response.StatusCode=401; return; }
                var seats = await db.Rows("""
                    SELECT d.id FROM eligible_license_devices d JOIN licenses l ON l.id=d.license_id JOIN users u ON u.id=l.user_id
                    WHERE d.token_hash=$1 AND l.product='meet' AND l.status='active' AND u.enabled
                    AND (l.expires_at IS NULL OR l.expires_at>now()) AND (l.updates_until IS NULL OR l.updates_until>now())
                    """, Auth.Hash(token));
                if (seats.Count!=1) { ctx.Response.StatusCode=403; return; }
            }
            var rows=await db.Rows("SELECT storage_name FROM releases WHERE product='meet' AND published AND filename=$1 AND lower(sha256)=$2",filename,sha);
            if (rows.Count!=1) { ctx.Response.StatusCode=404; return; }
            await files.Download(ctx,(string)rows[0][0],filename);
        }).RequireRateLimiting("license");
    }
}
