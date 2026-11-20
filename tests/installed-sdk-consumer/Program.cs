using System.Text.Json;
using NextgenReports.Client;
using var client = ReportClient.Create(new Uri(Environment.GetEnvironmentVariable("NEXTGEN_REPORT_URL") ?? "http://127.0.0.1:5274/"));
using var template = JsonDocument.Parse("""{"version":1,"blocks":[{"type":"text","text":"{{data.message}}"}]}""");
var input = ReportInput.FromObjects(template.RootElement, new { message = "Installed SDK works" });
var session = await client.GetSessionAsync();
if (session.Enabled) throw new Exception("Expected isolated local test engine");
var result = await client.ExportAsync(input, ReportFormat.Pdf);
if (!result.Content.AsSpan(0,5).SequenceEqual("%PDF-"u8)) throw new Exception("Invalid PDF");

Console.WriteLine($"PASS installed NuGet client: {result.Content.Length} PDF bytes");
