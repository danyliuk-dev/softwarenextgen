using System.Net.Mail;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

static class MeetInvitations
{
    internal record Invitation(string? Recipient, string? Link);

    internal static async Task<IResult> Send(Invitation input, HttpContext ctx, Store db, IConfiguration config, IHttpClientFactory clients)
    {
        var token = Licenses.Bearer(ctx);
        if (token == "") return Results.Unauthorized();
        var address = input.Recipient;
        var link = input.Link;
        if (address is not { Length: > 0 and <= 254 } || address.Any(char.IsControl) ||
            !MailAddress.TryCreate(address, out var parsed) || parsed.Address != address ||
            link is not { Length: 167 } || !Regex.IsMatch(link, @"\Ahttps://softwarenextgen\.com/meet/join#[0-9a-f]{64}\.[0-9a-f]{64}\z"))
            return Results.BadRequest();

        var scope = Convert.ToHexStringLower(SHA256.HashData(Encoding.UTF8.GetBytes(address + "\n" + link)));
        if (!await Licenses.VerifyProof(ctx, db, token, "meet-invite/" + scope))
            return Results.Unauthorized();
        var licenses = await db.Rows("""
            SELECT l.id FROM eligible_license_devices d JOIN licenses l ON l.id=d.license_id
            JOIN users u ON u.id=l.user_id WHERE d.token_hash=$1 AND l.product='meet'
            AND l.status='active' AND u.enabled AND (l.expires_at IS NULL OR l.expires_at>now())
            """, Auth.Hash(token));
        if (licenses.Count != 1) return Results.Forbid();
        if (config["Mail:Enabled"] != "true") return Results.StatusCode(503);
        var error = await PortalMail.Send(clients, config, address, "Nextgen Meet invitation",
            "You have been invited to a Nextgen Meet video meeting.\n\nJoin the meeting:\n" + link +
            "\n\nOpen the link on your computer. If Nextgen Meet is not installed, the invitation page offers a download.",
            ctx.RequestAborted);
        if (error != "") return Results.StatusCode(502);
        return Results.StatusCode(202);
    }
}
