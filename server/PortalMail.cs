using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

static class PortalMail
{
    internal static async Task<string> Send(IHttpClientFactory clients, IConfiguration config,
        string recipient, string subject, string body, CancellationToken ct)
    {
        using var http = clients.CreateClient();
        http.Timeout = TimeSpan.FromSeconds(25);
        var tenant = Uri.EscapeDataString(config["Mail:TenantId"]!);
        using var credentials = new FormUrlEncodedContent(new Dictionary<string, string> {
            ["client_id"] = config["Mail:ClientId"]!,
            ["client_secret"] = config["Mail:ClientSecret"]!,
            ["scope"] = "https://graph.microsoft.com/.default",
            ["grant_type"] = "client_credentials"
        });
        using var auth = await http.PostAsync($"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token", credentials, ct);
        if (!auth.IsSuccessStatusCode) return "Mail authentication HTTP " + (int)auth.StatusCode;

        using var json = JsonDocument.Parse(await auth.Content.ReadAsStringAsync(ct));
        var sender = Uri.EscapeDataString(config["Mail:Sender"] ?? "support@dmeclinic.com");
        using var request = new HttpRequestMessage(HttpMethod.Post, $"https://graph.microsoft.com/v1.0/users/{sender}/sendMail");
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", json.RootElement.GetProperty("access_token").GetString());
        request.Content = JsonContent.Create(new {
            message = new { subject, body = new { contentType = "Text", content = body },
                toRecipients = new[] { new { emailAddress = new { address = recipient } } } },
            saveToSentItems = true
        });
        using var response = await http.SendAsync(request, ct);
        return response.StatusCode == HttpStatusCode.Accepted ? "" : "Mail send HTTP " + (int)response.StatusCode;
    }
}
