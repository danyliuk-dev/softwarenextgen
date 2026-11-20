using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text.Json;

sealed class Files(IConfiguration config,IHttpClientFactory clients)
{
    public string Bucket=>config["ReleasesBucket"]??throw new InvalidOperationException("Release bucket is required");
    async Task<string> Token(CancellationToken ct)
    {
        using var req=new HttpRequestMessage(HttpMethod.Get,"http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token");req.Headers.Add("Metadata-Flavor","Google");
        using var http=clients.CreateClient();http.Timeout=TimeSpan.FromSeconds(10);
        using var r=await http.SendAsync(req,ct);r.EnsureSuccessStatusCode();using var json=JsonDocument.Parse(await r.Content.ReadAsStringAsync(ct));return json.RootElement.GetProperty("access_token").GetString()!;
    }
    public async Task Upload(string key,Stream stream,CancellationToken ct)
    {
        using var req=new HttpRequestMessage(HttpMethod.Post,"https://storage.googleapis.com/upload/storage/v1/b/"+Uri.EscapeDataString(Bucket)+"/o?uploadType=media&ifGenerationMatch=0&name="+Uri.EscapeDataString(key));
        req.Headers.Authorization=new AuthenticationHeaderValue("Bearer",await Token(ct));req.Content=new StreamContent(stream);req.Content.Headers.ContentType=new("application/octet-stream");
        using var http=clients.CreateClient();http.Timeout=TimeSpan.FromMinutes(30);using var r=await http.SendAsync(req,ct);r.EnsureSuccessStatusCode();
    }
    public async Task Download(HttpContext c,string key,string filename)
    {
        using var req=new HttpRequestMessage(HttpMethod.Get,"https://storage.googleapis.com/storage/v1/b/"+Uri.EscapeDataString(Bucket)+"/o/"+Uri.EscapeDataString(key)+"?alt=media");
        req.Headers.Authorization=new AuthenticationHeaderValue("Bearer",await Token(c.RequestAborted));
        var range=c.Request.Headers.Range.ToString();if(range!=""){if(!System.Text.RegularExpressions.Regex.IsMatch(range,@"^bytes=\d*-\d*$")){c.Response.StatusCode=416;return;}req.Headers.TryAddWithoutValidation("Range",range);}
        using var http=clients.CreateClient();http.Timeout=TimeSpan.FromMinutes(30);using var r=await http.SendAsync(req,HttpCompletionOption.ResponseHeadersRead,c.RequestAborted);
        if(!r.IsSuccessStatusCode){c.Response.StatusCode=r.StatusCode==System.Net.HttpStatusCode.RequestedRangeNotSatisfiable?416:502;return;}
        c.Response.StatusCode=(int)r.StatusCode;c.Response.ContentType="application/octet-stream";c.Response.ContentLength=r.Content.Headers.ContentLength;
        c.Response.Headers.ContentDisposition=new ContentDispositionHeaderValue("attachment"){FileName=filename,FileNameStar=filename}.ToString();c.Response.Headers.AcceptRanges="bytes";
        if(r.Content.Headers.ContentRange!=null)c.Response.Headers.ContentRange=r.Content.Headers.ContentRange.ToString();
        await r.Content.CopyToAsync(c.Response.Body,c.RequestAborted);
    }
}
