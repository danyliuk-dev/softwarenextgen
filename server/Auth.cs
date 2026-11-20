using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.DataProtection;
using Microsoft.AspNetCore.Identity;
using Npgsql;
using OtpNet;
using QRCoder;

static class Auth
{
    public const string Full = "Member", Pending = "Pending";
    public static string Hash(string value) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value)));
    public static string Token() => Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
    public static IDataProtector Protector(HttpContext c) => c.RequestServices.GetRequiredService<IDataProtectionProvider>().CreateProtector("Nextgen.AccountSecrets.v1");
    static readonly PasswordHasher<string> Hasher = new(new Microsoft.Extensions.Options.OptionsWrapper<PasswordHasherOptions>(new() { IterationCount = 210000 }));
    static readonly string Dummy = Hasher.HashPassword("dummy", Token());
    public static void Configure(WebApplicationBuilder b)
    {
        b.Services.AddAuthentication(Full).AddCookie(Full, o => {
            o.Cookie.Name = "__Host-NextgenMember"; o.Cookie.SecurePolicy = CookieSecurePolicy.Always;
            o.Cookie.HttpOnly = true; o.Cookie.SameSite = SameSiteMode.Lax;
            o.LoginPath = "/login"; o.AccessDeniedPath = "/forbidden";
            o.ExpireTimeSpan = TimeSpan.FromHours(8); o.SlidingExpiration = false;
            o.Events.OnValidatePrincipal = async ctx => {
                var db = ctx.HttpContext.RequestServices.GetRequiredService<Store>();
                var rows = await db.Rows("SELECT generation::text,role FROM users WHERE id::text=$1 AND enabled AND (role='user' OR mfa)", ctx.Principal?.FindFirstValue(ClaimTypes.NameIdentifier) ?? "");
                if (rows.Count != 1 || (string)rows[0][0] != ctx.Principal?.FindFirstValue("generation") || (string)rows[0][1] != ctx.Principal?.FindFirstValue(ClaimTypes.Role)) {
                    ctx.RejectPrincipal(); await ctx.HttpContext.SignOutAsync(Full);
                }
            };
        }).AddCookie(Pending, o => {
            o.Cookie.Name = "__Host-NextgenPending"; o.Cookie.SecurePolicy = CookieSecurePolicy.Always;
            o.Cookie.HttpOnly = true; o.Cookie.SameSite = SameSiteMode.Lax;
            o.ExpireTimeSpan = TimeSpan.FromMinutes(10); o.SlidingExpiration = false;
        });
        b.Services.AddAuthorization(o => o.AddPolicy("Admin", p => p.RequireAuthenticatedUser().RequireRole("admin")));
    }
    static Task Sign(HttpContext c, string scheme, object[] row) => c.SignInAsync(scheme, new ClaimsPrincipal(new ClaimsIdentity(new[] {
        new Claim(ClaimTypes.NameIdentifier, row[0].ToString()!), new Claim(ClaimTypes.Name, (string)row[1]),
        new Claim(ClaimTypes.Role, (string)row[2]), new Claim("generation",row[3].ToString()!)
    }, scheme)));
    public static async Task<object[]?> PendingUser(HttpContext c, Store db)
    {
        var result = await c.AuthenticateAsync(Pending);
        if (!result.Succeeded) return null;
        var rows = await db.Rows("SELECT id,email,role,generation,mfa,secret FROM users WHERE id::text=$1 AND generation::text=$2 AND enabled", result.Principal!.FindFirstValue(ClaimTypes.NameIdentifier)!, result.Principal.FindFirstValue("generation")!);
        return rows.Count == 1 ? rows[0] : null;
    }
    static async Task<IResult> Register(HttpContext c, Store db)
    {
        if (c.User.Identity?.IsAuthenticated == true) return Results.Redirect("/products");
        var form = await c.Request.ReadFormAsync();
        var email = form["email"].ToString().Trim().ToLowerInvariant();
        if (email.Length > 254 || !System.Net.Mail.MailAddress.TryCreate(email, out var address) || address.Address != email)
            return Ui.Error(c, "Invalid email", "Enter a valid email address.", "/register");

        await using var conn = await db.Source.OpenConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();
        await using var create = new NpgsqlCommand("INSERT INTO users(id,email,role,generation) VALUES($1,$2,'user',$3) ON CONFLICT(email) DO NOTHING", conn, tx);
        create.Parameters.AddWithValue(Guid.NewGuid());
        create.Parameters.AddWithValue(email);
        create.Parameters.AddWithValue(Guid.NewGuid());
        await create.ExecuteNonQueryAsync();

        await using var pending = new NpgsqlCommand("SELECT id FROM users WHERE email=$1 AND enabled AND role='user' AND password_hash='' FOR UPDATE", conn, tx);
        pending.Parameters.AddWithValue(email);
        if (await pending.ExecuteScalarAsync() is Guid userId)
        {
            await using var active = new NpgsqlCommand("SELECT 1 FROM invitations WHERE user_id=$1 AND used_at IS NULL AND expires_at>now()", conn, tx);
            active.Parameters.AddWithValue(userId);
            if (await active.ExecuteScalarAsync() is null)
                await Admin.QueueInvitation(conn, tx, userId, email, Protector(c));
        }
        await tx.CommitAsync();
        return Ui.Page(c, "Check your email", "<p>If your account is awaiting setup, look for an email with a link to choose your password. The link is valid for 48 hours.</p><p>Already set a password? <a href='/login'>Sign in</a>.</p>", narrow: true);
    }
    public static void Map(WebApplication app)
    {
        app.MapGet("/register", (HttpContext c) => c.User.Identity?.IsAuthenticated == true
            ? Results.Redirect("/products")
            : Ui.Page(c, "Create a customer account", "<p>We’ll email you a link to choose your password.</p>"
                + Ui.Form(c, "/register", "<label>Email address<input type='email' name='email' autocomplete='email' maxlength='254' required></label><button>Email me a link →</button>")
                + "<p>Already have an account? <a href='/login'>Sign in</a></p>", narrow: true));
        app.MapPost("/register", Register).RequireRateLimiting("auth");
        app.MapGet("/login", (HttpContext c) => c.User.Identity?.IsAuthenticated == true ? Results.Redirect("/products") : Ui.Page(c,"Welcome back", "<p>Sign in to your Software Next Generation account.</p>"+Ui.Form(c,"/login", "<label>Email address<input type='email' name='email' autocomplete='username' required maxlength='254'></label><label>Password<input type='password' name='password' autocomplete='current-password' required maxlength='256'></label><button>Continue →</button>")+"<p class='muted'>New customer? <a href='/register'>Create an account</a>. For a password reset, contact your administrator.</p>", narrow:true));
        app.MapPost("/login", async (HttpContext c, Store db) => {
            var f=await c.Request.ReadFormAsync(); var email=f["email"].ToString().Trim().ToLowerInvariant(); var pass=f["password"].ToString();
            if(pass.Length>256 || email.Length>254)return Ui.Error(c,"Sign-in failed","Check your credentials or try again later.");
            await using var conn=await db.Source.OpenConnectionAsync(); await using var tx=await conn.BeginTransactionAsync();
            await using var cmd=new NpgsqlCommand("SELECT id,email,role,generation,mfa,password_hash,locked_until>now() FROM users WHERE email=$1 AND enabled FOR UPDATE",conn,tx); cmd.Parameters.AddWithValue(email);
            object[]? row=null; await using(var r=await cmd.ExecuteReaderAsync()){if(await r.ReadAsync()){row=new object[r.FieldCount];r.GetValues(row);}}
            var hash=row is null || (string)row[5]==""?Dummy:(string)row[5];
            var ok=Hasher.VerifyHashedPassword(email,hash,pass)!=PasswordVerificationResult.Failed;
            if(row is null || !ok || row[6] is true) {
                if(row is not null) {await using var fail=new NpgsqlCommand("UPDATE users SET failures=CASE WHEN locked_until<=now() THEN 1 ELSE failures+1 END,locked_until=CASE WHEN locked_until>now() THEN locked_until WHEN locked_until<=now() THEN NULL WHEN failures+1>=5 THEN now()+interval '15 minutes' ELSE NULL END WHERE id=$1",conn,tx);fail.Parameters.AddWithValue(row[0]);await fail.ExecuteNonQueryAsync();}
                await tx.CommitAsync();return Ui.Error(c,"Sign-in failed","Check your credentials or try again later.");
            }
            if((string)row[2]=="user") {
                await using var reset=new NpgsqlCommand("UPDATE users SET failures=0,locked_until=NULL WHERE id=$1",conn,tx);reset.Parameters.AddWithValue(row[0]);await reset.ExecuteNonQueryAsync();
                await tx.CommitAsync();await c.SignOutAsync(Pending);await Sign(c,Full,row);await db.Audit(email,"login.success");return Results.Redirect(RemoteUpdates.AfterLogin(c));
            }
            // Administrator lockout spans password and MFA steps.
            await tx.CommitAsync(); await c.SignOutAsync(Full); await Sign(c,Pending,row);
            return Results.Redirect((bool)row[4]?"/verify":"/enroll");
        }).RequireRateLimiting("auth");
        app.MapPost("/logout",async(HttpContext c)=>{await c.SignOutAsync(Full);await c.SignOutAsync(Pending);return Results.Redirect("/");});
        app.MapGet("/accept",(HttpContext c)=>Ui.Page(c,"Create your account", "<p>Choose a password for your Software Next Generation account. Administrators also configure an authenticator app. Your invitation expires after 48 hours.</p>"+Ui.Form(c,"/accept","<input id='invite-token' type='hidden' name='token'><label>New password<input type='password' name='password' autocomplete='new-password' minlength='14' maxlength='256' required></label><label>Confirm password<input type='password' name='confirm' autocomplete='new-password' minlength='14' maxlength='256' required></label><button>Create password →</button>")+"<script src='/invite.js' defer></script>",narrow:true));
        app.MapPost("/accept",async(HttpContext c,Store db)=>{
            var f=await c.Request.ReadFormAsync(); var password=f["password"].ToString();var token=f["token"].ToString();
            if(password.Length<14||password.Length>256||password!=f["confirm"]||token.Length!=64)return Ui.Error(c,"Cannot set password","Use matching passwords of 14–256 characters and open the full invitation link again.");
            await using var conn=await db.Source.OpenConnectionAsync();await using var tx=await conn.BeginTransactionAsync();
            await using var cmd=new NpgsqlCommand("SELECT u.id,u.email,u.role,u.generation,u.mfa FROM users u JOIN invitations i ON i.user_id=u.id WHERE i.token_hash=$1 AND i.used_at IS NULL AND i.expires_at>now() AND u.enabled FOR UPDATE OF u,i",conn,tx);cmd.Parameters.AddWithValue(Hash(token));
            object[] row;await using(var r=await cmd.ExecuteReaderAsync()){if(!await r.ReadAsync())return Ui.Error(c,"Invitation unavailable","This invitation is invalid, expired or already used. For a new customer account, return to registration to request a new link. For account recovery, contact your administrator.","/register");row=new object[r.FieldCount];r.GetValues(row);}
            await using var update=new NpgsqlCommand("UPDATE users SET password_hash=$2,failures=0,locked_until=NULL WHERE id=$1",conn,tx);update.Parameters.AddWithValue(row[0]);update.Parameters.AddWithValue(Hasher.HashPassword((string)row[1],password));await update.ExecuteNonQueryAsync();await using var consume=new NpgsqlCommand("UPDATE invitations SET used_at=now() WHERE user_id=$1 AND used_at IS NULL",conn,tx);consume.Parameters.AddWithValue(row[0]);await consume.ExecuteNonQueryAsync();await tx.CommitAsync();
            await c.SignOutAsync(Full);await Sign(c,(string)row[2]=="admin"?Pending:Full,row);await db.Audit((string)row[1],"invitation.accepted");return Results.Redirect((string)row[2]=="admin"?((bool)row[4]?"/verify":"/enroll"):RemoteUpdates.AfterLogin(c));
        }).RequireRateLimiting("auth");
        app.MapGet("/enroll",async(HttpContext c,Store db)=>{
            var row=await PendingUser(c,db);if(row is null)return Results.Redirect("/login");if((bool)row[4])return Results.Redirect("/verify");
            var secret=(string)row[5];
            if(secret=="") {secret=Protector(c).Protect(Base32Encoding.ToString(RandomNumberGenerator.GetBytes(20)));await db.Exec("UPDATE users SET secret=$2 WHERE id=$1 AND NOT mfa AND secret=''",row[0],secret);row=await PendingUser(c,db);if(row is null)return Results.Redirect("/login");secret=(string)row[5];}
            secret=Protector(c).Unprotect(secret);
            var uri="otpauth://totp/"+Uri.EscapeDataString("Software Next Generation:"+(string)row[1])+"?secret="+secret+"&issuer=Software%20Next%20Generation&algorithm=SHA1&digits=6&period=30";
            using var data=QRCodeGenerator.GenerateQrCode(uri,QRCodeGenerator.ECCLevel.M);using var qr=new PngByteQRCode(data);
            return Ui.Page(c,"Secure your account","<p>Scan this QR code with your authenticator app. Two-factor authentication is required for administrator accounts.</p><img class='qr' alt='Authenticator setup QR code' width='280' height='280' src='data:image/png;base64,"+Convert.ToBase64String(qr.GetGraphic(6))+"'><details><summary>Enter a setup key manually</summary><code id='setup-key'>"+secret+"</code></details>"+Ui.Form(c,"/enroll","<label>Six-digit authenticator code<input name='code' inputmode='numeric' autocomplete='one-time-code' pattern='[0-9]{6}' maxlength='6' required></label><button>Enable 2FA →</button>"),narrow:true);
        });
        app.MapGet("/verify",async(HttpContext c,Store db)=>await PendingUser(c,db) is null?Results.Redirect("/login"):Ui.Page(c,"Verify your sign-in","<p>Enter a code from your authenticator or one unused recovery code.</p>"+Ui.Form(c,"/verify","<label>Verification code<input name='code' autocomplete='one-time-code' maxlength='64' required></label><button>Sign in →</button>"),narrow:true));
        app.MapPost("/enroll",(HttpContext c,Store db)=>Verify(c,db,true)).RequireRateLimiting("auth");
        app.MapPost("/verify",(HttpContext c,Store db)=>Verify(c,db,false)).RequireRateLimiting("auth");
        app.MapGet("/account",async(HttpContext c,Store db)=>{
            var r=await db.Rows("SELECT cardinality(recovery) FROM users WHERE id::text=$1",c.User.FindFirstValue(ClaimTypes.NameIdentifier)!);
            return Ui.Page(c,"Account security","<div class='panel'><span class='badge'>Account protected</span><h2>"+Ui.E(c.User.Identity!.Name!)+"</h2><p>Administrators require a password and authenticator. Customer access is controlled by assigned product licenses.</p><p>Unused recovery codes: <strong>"+r[0][0]+"</strong></p><p><a href='/licenses'>My licenses and activations</a></p><p><a href='/updates/remote/devices'>Manage computers with automatic updates</a></p><p>For account recovery, contact your administrator.</p></div>");
        }).RequireAuthorization();
    }
    static async Task<IResult> Verify(HttpContext c,Store db,bool enroll)
    {
        var pending=await PendingUser(c,db);if(pending is null)return Results.Redirect("/login");
        var code=(await c.Request.ReadFormAsync())["code"].ToString().Trim().Replace(" ","").Replace("-","").ToUpperInvariant();
        if(code.Length>64)return Ui.Error(c,"Verification failed","Invalid code.");
        await using var conn=await db.Source.OpenConnectionAsync();await using var tx=await conn.BeginTransactionAsync();
        await using var cmd=new NpgsqlCommand("SELECT id,email,role,generation,mfa,secret,last_step,recovery,locked_until>now() FROM users WHERE id=$1 AND generation=$2 AND enabled FOR UPDATE",conn,tx);cmd.Parameters.AddWithValue(pending[0]);cmd.Parameters.AddWithValue(pending[3]);
        object[] row;await using(var r=await cmd.ExecuteReaderAsync()){if(!await r.ReadAsync())return Results.Redirect("/login");row=new object[r.FieldCount];r.GetValues(row);}
        if(row[8] is true || (bool)row[4]==enroll || (string)row[5]=="")return Ui.Error(c,"Verification unavailable","Start sign-in again or wait 15 minutes after repeated failures.");
        long step=-1;var valid=code.Length==6&&code.All(char.IsAsciiDigit)&&new Totp(Base32Encoding.ToBytes(Protector(c).Unprotect((string)row[5]))).VerifyTotp(code,out step,new VerificationWindow(1,1))&&step>(long)row[6];
        var hashes=(string[])row[7];var recovery=!enroll&&code.Length==32&&hashes.Contains(Hash(code));
        if(!valid&&!recovery){await using var fail=new NpgsqlCommand("UPDATE users SET failures=CASE WHEN locked_until<=now() THEN 1 ELSE failures+1 END,locked_until=CASE WHEN locked_until<=now() THEN NULL WHEN failures+1>=5 THEN now()+interval '15 minutes' ELSE NULL END WHERE id=$1",conn,tx);fail.Parameters.AddWithValue(row[0]);await fail.ExecuteNonQueryAsync();await tx.CommitAsync();return Ui.Error(c,"Verification failed","Invalid or already used code. Wait for a new code; after repeated failures wait 15 minutes.",enroll?"/enroll":"/verify");}
        string[]? codes=null;
        if(enroll){codes=Enumerable.Range(0,10).Select(_=>Convert.ToHexString(RandomNumberGenerator.GetBytes(16))).ToArray();hashes=codes.Select(Hash).ToArray();}else if(recovery)hashes=hashes.Where(h=>h!=Hash(code)).ToArray();
        await using var update=new NpgsqlCommand("UPDATE users SET mfa=true,last_step=$2,recovery=$3,failures=0,locked_until=NULL WHERE id=$1",conn,tx);update.Parameters.AddWithValue(row[0]);update.Parameters.AddWithValue(valid?step:row[6]);update.Parameters.AddWithValue(hashes);await update.ExecuteNonQueryAsync();await tx.CommitAsync();
        await c.SignOutAsync(Pending);await Sign(c,Full,row);await db.Audit((string)row[1],enroll?"mfa.enabled":"login.success");
        return enroll?Ui.Page(c,"Save your recovery codes","<p>Two-factor authentication is enabled. These codes are shown once. Save them in your password manager. Each code can be used only once.</p><pre id='recovery-codes'>"+string.Join("\n",codes!)+"</pre><a class='button' href='"+Ui.E(RemoteUpdates.AfterLogin(c))+"'>I saved my codes →</a>",narrow:true):Results.Redirect(RemoteUpdates.AfterLogin(c));
    }
}
