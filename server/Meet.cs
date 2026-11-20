static class Meet
{
    public static void Map(WebApplication app)
    {
        app.MapPost("/api/meet/invitations", MeetInvitations.Send).RequireRateLimiting("meet-invitations");
        app.MapGet("/meet/join", (IWebHostEnvironment env) =>
            Results.File(Path.Combine(env.WebRootPath, "meet", "join.html"), "text/html; charset=utf-8"));
        app.MapGet("/meet/download/{platform}", async (string platform, HttpContext context, Store db, Files files) =>
        {
            var label = platform switch {
                "linux" => "Linux x64", "windows" => "Windows x64",
                "macos" => "macOS Apple Silicon", _ => null
            };
            if (label is null) { context.Response.StatusCode = 404; return; }
            var rows = await db.Rows("SELECT storage_name, filename FROM releases WHERE product='meet' AND published AND platform=$1 AND starts_with(filename,'NextgenMeetClient-') ORDER BY created_at DESC LIMIT 1", label);
            if (rows.Count == 0) { context.Response.StatusCode = 404; return; }
            await files.Download(context, (string)rows[0][0], (string)rows[0][1]);
        });
    }
}
