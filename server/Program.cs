using System.Net;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Http.Features;
using Microsoft.AspNetCore.HttpOverrides;
using Npgsql;

var b=WebApplication.CreateBuilder(args);
b.Services.AddSingleton(NpgsqlDataSource.Create(b.Configuration.GetConnectionString("Nextgen")??throw new InvalidOperationException("Nextgen database is required")));
b.Services.AddSingleton<Store>();b.Services.AddHttpClient();b.Services.AddSingleton<Files>();b.Services.AddHostedService<MailWorker>();
b.Services.AddDataProtection().PersistKeysToFileSystem(new DirectoryInfo(b.Configuration["KeysPath"]??"/var/lib/nextgensoftware/keys")).SetApplicationName("NextgenSoftware");
b.Services.AddAntiforgery(o=>{o.Cookie.Name="__Host-NextgenCsrf";o.Cookie.SecurePolicy=CookieSecurePolicy.Always;o.Cookie.SameSite=SameSiteMode.Strict;});
b.Services.Configure<FormOptions>(o=>{o.MultipartBodyLengthLimit=1024L*1024*1024;o.ValueLengthLimit=8192;});
b.WebHost.ConfigureKestrel(o=>o.Limits.MaxRequestBodySize=1024L*1024*1024);
b.Services.Configure<ForwardedHeadersOptions>(o=>{o.ForwardedHeaders=ForwardedHeaders.XForwardedFor|ForwardedHeaders.XForwardedProto;o.KnownProxies.Add(IPAddress.Loopback);});
b.Services.AddRateLimiter(o=>{o.RejectionStatusCode=429;o.AddPolicy("meet-invitations", c => RateLimitPartition.GetFixedWindowLimiter(c.Connection.RemoteIpAddress?.ToString() ?? "unknown", _ => new() { PermitLimit=30, Window=TimeSpan.FromMinutes(15), QueueLimit=0 }));o.AddPolicy("license",c=>RateLimitPartition.GetFixedWindowLimiter(c.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){PermitLimit=120,Window=TimeSpan.FromMinutes(1),QueueLimit=0}));o.AddPolicy("auth",c=>RateLimitPartition.GetFixedWindowLimiter(c.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){PermitLimit=30,Window=TimeSpan.FromMinutes(15),QueueLimit=0}));});
Auth.Configure(b);
var app=b.Build();await app.Services.GetRequiredService<Store>().Initialize();
app.UseForwardedHeaders();
app.Use(async(c,next)=>{
    c.Response.Headers["X-Content-Type-Options"]="nosniff";
    c.Response.Headers["Referrer-Policy"]="no-referrer";
    var demo=c.Request.Path.StartsWithSegments("/report-examples");
    c.Response.Headers["X-Frame-Options"]=demo?"SAMEORIGIN":"DENY";
    c.Response.Headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; object-src 'none'; frame-ancestors "+(demo?"'self'":"'none'")+"; base-uri 'none'; form-action 'self'";
    if (c.Request.Path == "/meet/join" || c.Request.Path == "/meet/join.html")
        c.Response.Headers["Content-Security-Policy"] = c.Response.Headers["Content-Security-Policy"].ToString().Replace("script-src 'self'", "script-src 'self' 'wasm-unsafe-eval'") + "; connect-src 'self' wss://connect.softwarenextgen.com";
    c.Response.Headers["Cache-Control"]="no-store";
    if(c.Request.IsHttps)c.Response.Headers["Strict-Transport-Security"]="max-age=31536000";
    if(c.Request.Path.StartsWithSegments("/api/licenses") || c.Request.Path == "/api/meet/invitations") {
        var limit=c.Features.Get<IHttpMaxRequestBodySizeFeature>();if(limit is {IsReadOnly:false})limit.MaxRequestBodySize=8192;
    }
    try{await next();}catch(BadHttpRequestException){c.Response.StatusCode=400;}catch(Exception ex){app.Logger.LogError("Request failed: {Type}",ex.GetType().Name);if(!c.Response.HasStarted){c.Response.StatusCode=500;await c.Response.WriteAsync("The request could not be completed. Please try again.");}}
});
app.UseStaticFiles();app.UseAuthentication();app.UseAuthorization();app.UseRateLimiter();
app.Use(async(c,next)=>{if(HttpMethods.IsPost(c.Request.Method) && c.Request.Path != "/api/remote-updates/device" && c.Request.Path != "/api/licenses/device" && c.Request.Path != "/api/meet/invitations" && c.Request.Path != "/api/licenses/lease"){try{await c.RequestServices.GetRequiredService<IAntiforgery>().ValidateRequestAsync(c);}catch(AntiforgeryValidationException){c.Response.StatusCode=400;await c.Response.WriteAsync("The form expired. Reload the page and try again.");return;}}await next();});
app.MapGet("/health",()=>Results.Json(new{status="ok",version=typeof(Program).Assembly.GetName().Version?.ToString(3)??"unknown"}));
app.MapGet("/",(HttpContext c)=>Ui.Home(c));
app.MapGet("/forbidden",(HttpContext c)=>Ui.Error(c,"Access denied","This page requires administrator access.","/products",403));
app.MapGet("/privacy",(HttpContext c)=>Ui.Page(c,"Privacy","<div class='prose'><p>Software Next Generation stores your name, email address, organization when provided, password hash, administrator authenticator setup, account status, assigned licenses, device activation public keys and security activity to provide secure product access. Passwords are never stored in plain text.</p><p>Invitations are sent through our email provider. Essential cookies keep you signed in and protect forms. We do not use advertising trackers.</p><p>Contact your administrator to request account deletion or assistance. Downloaded software runs on your computer; consult each product manual for its data handling.</p></div>"));
MeetUpdates.Map(app);Meet.Map(app);Licenses.Map(app);Auth.Map(app);RemoteUpdates.Map(app);Portal.Map(app);Admin.Map(app);Previews.Map(app);
app.Run();
