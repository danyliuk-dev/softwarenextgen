using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Net.Mail;
using Npgsql;

static partial class Licenses
{
    public static Guid User(HttpContext c)=>Guid.Parse(c.User.FindFirstValue(ClaimTypes.NameIdentifier)!);
    public static async Task<bool> CanDownload(HttpContext c,Store db,string product) => product!="remote" || c.User.IsInRole("admin") || await Entitled(db,User(c),product,true);
    public static async Task<bool> Entitled(Store db,Guid user,string product,bool updates=false)=> (await db.Rows("SELECT 1 FROM licenses l JOIN users u ON u.id=l.user_id WHERE l.user_id=$1 AND l.product=$2 AND u.enabled AND l.status='active' AND (l.expires_at IS NULL OR l.expires_at>now())"+(updates?" AND (l.updates_until IS NULL OR l.updates_until>now())":"")+" LIMIT 1",user,product)).Count==1;
    internal static string Bearer(HttpContext c){var s=c.Request.Headers.Authorization.ToString();return s.StartsWith("Bearer ")&&s.Length==71?s[7..]:"";}
    static string SelectProducts()=>string.Join("",Portal.Products.Select(p=>"<option value='"+p.Key+"'>"+Ui.E(p.Value.Name)+"</option>"));
    static string Field(string name,string label,string type="text",string value="")=>"<label>"+label+"<input name='"+name+"' type='"+type+"' value='"+Ui.E(value)+"' maxlength='254' required></label>";
    public static void Map(WebApplication app)
    {
        MapAdminList(app);
        app.MapPost("/admin/licenses/device/revoke",async(HttpContext c,Store db)=>{var f=await c.Request.ReadFormAsync();if(!Guid.TryParse(f["id"],out var id))return Results.BadRequest();await db.Exec("UPDATE license_devices SET revoked_at=now() WHERE id=$1 AND revoked_at IS NULL",id);await db.Audit(c.User.Identity!.Name!,"license.device.admin_revoked",id.ToString());return Results.Redirect("/admin/licenses?view=devices");}).RequireAuthorization("Admin");
        app.MapGet("/admin/customers/{id:guid}",async(HttpContext c,Store db,Guid id)=>{
            var rows=await db.Rows("SELECT u.email,COALESCE(c.first_name,''),COALESCE(c.last_name,''),COALESCE(c.kind,'private'),COALESCE(c.organization,'') FROM users u LEFT JOIN customers c ON c.user_id=u.id WHERE u.id=$1",id);if(rows.Count!=1)return Results.NotFound();var r=rows[0];
            return Ui.Page(c,"Edit client","<p>"+Ui.E((string)r[0])+"</p>"+Ui.Form(c,"/admin/customers/"+id,Field("first","First name",value:(string)r[1])+Field("last","Last name",value:(string)r[2])+"<label>Customer type<select name='kind'><option value='private'"+((string)r[3]=="private"?" selected":"")+">Private</option><option value='organization'"+((string)r[3]=="organization"?" selected":"")+">Organization</option></select></label><label>Organization<input name='organization' maxlength='254' value='"+Ui.E((string)r[4])+"'></label><button>Save client</button>"),narrow:true);
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/customers/{id:guid}",async(HttpContext c,Store db,Guid id)=>{
            var f=await c.Request.ReadFormAsync();var first=f["first"].ToString().Trim();var last=f["last"].ToString().Trim();var kind=f["kind"].ToString();var org=f["organization"].ToString().Trim();
            if(first.Length is <1 or >254||last.Length is <1 or >254||org.Length>254||!new[]{"private","organization"}.Contains(kind)||(kind=="organization"&&org.Length==0))return Results.BadRequest();
            var count=await db.Exec("INSERT INTO customers(user_id,first_name,last_name,kind,organization) SELECT id,$2,$3,$4,$5 FROM users WHERE id=$1 ON CONFLICT(user_id) DO UPDATE SET first_name=excluded.first_name,last_name=excluded.last_name,kind=excluded.kind,organization=excluded.organization",id,first,last,kind,kind=="private"?"":org);
            if(count!=1)return Results.NotFound();await db.Audit(c.User.Identity!.Name!,"customer.updated",id.ToString());return Results.Redirect("/admin/licenses");
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/licenses/customer",async(HttpContext c,Store db)=>{
            var f=await c.Request.ReadFormAsync();var email=f["email"].ToString().Trim().ToLowerInvariant();var first=f["first"].ToString().Trim();var last=f["last"].ToString().Trim();var kind=f["kind"].ToString();var org=f["organization"].ToString().Trim();
            if(first.Length is <1 or >254 || last.Length is <1 or >254 || org.Length>254 || !new[]{"private","organization"}.Contains(kind) || (kind=="organization" && org.Length==0) || email.Length>254 || !MailAddress.TryCreate(email,out var address)||address.Address!=email)return Ui.Error(c,"Invalid client","Enter the client's name, email and organization when applicable.","/admin/licenses");
            await using var conn=await db.Source.OpenConnectionAsync();await using var tx=await conn.BeginTransactionAsync();var id=Guid.NewGuid();
            await using(var cmd=new NpgsqlCommand("INSERT INTO users(id,email,role,generation) VALUES($1,$2,'user',$3) ON CONFLICT(email) DO NOTHING RETURNING id",conn,tx)){cmd.Parameters.AddWithValue(id);cmd.Parameters.AddWithValue(email);cmd.Parameters.AddWithValue(Guid.NewGuid());if(await cmd.ExecuteScalarAsync() is null)return Ui.Error(c,"Account already exists","Use the existing account to assign a license.","/admin/licenses");}
            await using(var cmd=new NpgsqlCommand("INSERT INTO customers(user_id,first_name,last_name,kind,organization) VALUES($1,$2,$3,$4,$5)",conn,tx)){foreach(var v in new object[]{id,first,last,kind,kind=="private"?"":org})cmd.Parameters.AddWithValue(v);await cmd.ExecuteNonQueryAsync();}await tx.CommitAsync();await db.Audit(c.User.Identity!.Name!,"customer.created",id.ToString());return Results.Redirect("/admin/licenses");
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/licenses/create",async(HttpContext c,Store db)=>{
            var f=await c.Request.ReadFormAsync();if(!Guid.TryParse(f["user"],out var user)||!Portal.Products.ContainsKey(f["product"].ToString())||!int.TryParse(f["seats"],out var seats)||seats is <1 or >100000||f["edition"].ToString().Length is <1 or >80||!Expiry(f["expires"].ToString(),out var expires))return Results.BadRequest();
            if(!SessionLimit(f,out var sessions))return Results.BadRequest();
            var id=Guid.NewGuid();var n=await db.Exec("INSERT INTO licenses(id,user_id,product,edition,seats,expires_at,session_limit) SELECT $1,id,$3,$4,$5,NULLIF($6,'')::timestamptz,COALESCE(NULLIF($7,0),16) FROM users WHERE id=$2 AND enabled",id,user,f["product"].ToString(),f["edition"].ToString(),seats,expires,sessions);if(n!=1)return Results.BadRequest();await db.Audit(c.User.Identity!.Name!,"license.created",id.ToString());return Results.Redirect("/admin/licenses?view=licenses");
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/licenses/change",async(HttpContext c,Store db)=>{
            var f=await c.Request.ReadFormAsync();if(!Guid.TryParse(f["id"],out var id)||!new[]{"active","suspended","revoked"}.Contains(f["status"].ToString())||!int.TryParse(f["seats"],out var seats)||seats is <1 or >100000||!Expiry(f["expires"].ToString(),out var expires))return Results.BadRequest();
            // The same row lock used by activation serializes seat changes and registrations.
            if(!SessionLimit(f,out var sessions))return Results.BadRequest();
            await db.Exec("UPDATE licenses SET session_limit=COALESCE(NULLIF($5,0),session_limit),status=$2,seats=$3,expires_at=NULLIF($4,'')::timestamptz WHERE id=$1",id,f["status"].ToString(),seats,expires,sessions);await db.Audit(c.User.Identity!.Name!,"license.changed",id.ToString());return Results.Redirect("/admin/licenses?view=licenses");
        }).RequireAuthorization("Admin");
        app.MapGet("/licenses",async(HttpContext c,Store db)=>{
            var rows=await db.Rows("SELECT id,product,edition,status,seats,expires_at FROM licenses WHERE user_id=$1 ORDER BY created_at DESC",User(c));
            var devices=await db.Rows("SELECT d.id,d.name,l.product,d.last_seen FROM license_devices d JOIN licenses l ON l.id=d.license_id WHERE l.user_id=$1 AND d.revoked_at IS NULL",User(c));
            return Ui.Page(c,"My licenses",(rows.Count==0?"<p>No product license has been assigned. Contact your administrator.</p>":string.Join("",rows.Select(r=>"<article class='panel'><h2>"+Ui.E(Portal.Products[(string)r[1]].Name)+"</h2><p>"+Ui.E((string)r[2])+" · "+r[3]+" · "+r[4]+" installations</p><p>Expires: "+(r[5] is DBNull?"Perpetual":Ui.E(r[5].ToString()!))+"</p></article>")))+"<h2>Activated devices</h2>"+string.Join("",devices.Select(r=>"<article class='panel'><h3>"+Ui.E((string)r[1])+"</h3><p>"+Ui.E(Portal.Products[(string)r[2]].Name)+"</p>"+Ui.Form(c,"/licenses/revoke","<input type='hidden' name='id' value='"+r[0]+"'><button>Deactivate device</button>")+"</article>"))+"<p>Offline permissions can remain valid for up to seven days after deactivation. Server access stops immediately.</p>");
        }).RequireAuthorization();
        app.MapPost("/licenses/revoke",async(HttpContext c,Store db)=>{var f=await c.Request.ReadFormAsync();if(!Guid.TryParse(f["id"],out var id))return Results.BadRequest();await db.Exec("UPDATE license_devices d SET revoked_at=now() FROM licenses l WHERE d.license_id=l.id AND d.id=$1 AND l.user_id=$2",id,User(c));await db.Audit(c.User.Identity!.Name!,"license.device.revoked",id.ToString());return Results.Redirect("/licenses");}).RequireAuthorization();
        MapActivation(app);
    }
    static bool Expiry(string input,out string value){value="";if(input=="")return true;if(!DateOnly.TryParseExact(input,"yyyy-MM-dd",out var d))return false;value=d.ToString("yyyy-MM-dd")+"T23:59:59Z";return true;}
    static void MapActivation(WebApplication app)
    {
        app.MapPost("/api/licenses/device",async(HttpContext c,Store db)=>{
            if(c.Request.Headers["X-Nextgen-Client"]!="1")return Results.BadRequest();var i=await c.Request.ReadFromJsonAsync<DeviceInput>();
            if(i is null||i.Product is not ("remote" or "meet")||string.IsNullOrWhiteSpace(i.Name)||i.Name.Length>80||string.IsNullOrEmpty(i.PublicKey)||i.PublicKey.Length>200)return Results.BadRequest();
            try{using var key=ECDsa.Create();key.ImportSubjectPublicKeyInfo(Convert.FromBase64String(i.PublicKey),out var read);if(key.KeySize!=256||read!=Convert.FromBase64String(i.PublicKey).Length||key.ExportParameters(false).Curve.Oid.Value!="1.2.840.10045.3.1.7")return Results.BadRequest();}catch(CryptographicException){return Results.BadRequest();}catch(FormatException){return Results.BadRequest();}
            var token=Auth.Token();var code=Convert.ToHexString(RandomNumberGenerator.GetBytes(5));await db.Exec("DELETE FROM license_devices WHERE license_id IS NULL AND pending_until<now()");
            await db.Exec("INSERT INTO license_devices(id,token_hash,code,product,name,public_key,pending_until) VALUES($1,$2,$3,$4,$5,$6,now()+interval '10 minutes')",Guid.NewGuid(),Auth.Hash(token),code,i.Product,i.Name,i.PublicKey);
            return Results.Json(new{token,code,activationUrl="https://softwarenextgen.com/licenses/activate?code="+code,expiresIn=600});
        }).RequireRateLimiting("auth");
        app.MapGet("/licenses/activate",async(HttpContext c,Store db,string? code)=>{
            code=(code??"").ToUpperInvariant();if(!System.Text.RegularExpressions.Regex.IsMatch(code,"^[A-F0-9]{10}$"))return Results.BadRequest();
            if(c.User.Identity?.IsAuthenticated!=true){c.Response.Cookies.Append("__Host-NextgenLicenseCode",code,new CookieOptions{Secure=true,HttpOnly=true,SameSite=SameSiteMode.Lax,Path="/",MaxAge=TimeSpan.FromMinutes(10)});return Results.Redirect("/login");}
            var d=await db.Rows("SELECT name,product FROM license_devices WHERE code=$1 AND license_id IS NULL AND revoked_at IS NULL AND pending_until>now()",code);if(d.Count!=1)return Ui.Error(c,"Code unavailable","Restart activation from your application.");
            var ls=await db.Rows("SELECT id,edition,seats FROM licenses WHERE user_id=$1 AND product=$2 AND status='active' AND (expires_at IS NULL OR expires_at>now())",User(c),d[0][1]);
            return Ui.Page(c,"Activate software license","<p>"+Ui.E(Portal.Products[(string)d[0][1]].Name)+" on <strong>"+Ui.E((string)d[0][0])+"</strong></p><p>Check this code in your application:</p><pre>"+code+"</pre>"+(ls.Count==0?"<p>No active license is available for this product. Contact your administrator.</p>":Ui.Form(c,"/licenses/activate","<input type='hidden' name='code' value='"+code+"'><label>License<select name='license'>"+string.Join("",ls.Select(r=>"<option value='"+r[0]+"'>"+Ui.E((string)r[1])+" · "+r[2]+" installations</option>"))+"</select></label><label><input type='checkbox' name='confirm' value='yes' required> This is my device and I requested activation</label><button>Activate license</button>")),narrow:true);
        });
        app.MapPost("/licenses/activate",async(HttpContext c,Store db)=>{
            var f=await c.Request.ReadFormAsync();if(f["confirm"]!="yes"||!Guid.TryParse(f["license"],out var id))return Results.BadRequest();
            await using var conn=await db.Source.OpenConnectionAsync();await using var tx=await conn.BeginTransactionAsync();
            await using var cmd=new NpgsqlCommand("SELECT product,seats FROM licenses WHERE id=$1 AND user_id=$2 AND status='active' AND (expires_at IS NULL OR expires_at>now()) FOR UPDATE",conn,tx);cmd.Parameters.AddWithValue(id);cmd.Parameters.AddWithValue(User(c));string product;int seats;await using(var r=await cmd.ExecuteReaderAsync()){if(!await r.ReadAsync())return Results.Forbid();product=r.GetString(0);seats=r.GetInt32(1);}
            await using var count=new NpgsqlCommand("SELECT count(*) FROM license_devices WHERE license_id=$1 AND revoked_at IS NULL",conn,tx);count.Parameters.AddWithValue(id);if((long)(await count.ExecuteScalarAsync())!>=seats)return Ui.Error(c,"Device limit reached","Deactivate an unused device in My licenses, or contact your administrator.","/licenses");
            await using var update=new NpgsqlCommand("UPDATE license_devices SET license_id=$2,approved_at=now() WHERE code=$1 AND product=$3 AND license_id IS NULL AND revoked_at IS NULL AND pending_until>now() AND NOT EXISTS(SELECT 1 FROM license_devices d2 WHERE d2.license_id=$2 AND d2.revoked_at IS NULL AND d2.public_key=license_devices.public_key)",conn,tx);update.Parameters.AddWithValue(f["code"].ToString());update.Parameters.AddWithValue(id);update.Parameters.AddWithValue(product);if(await update.ExecuteNonQueryAsync()!=1)return Ui.Error(c,"Activation unavailable","The code expired, was used, or this device is already active.","/licenses");await tx.CommitAsync();await db.Audit(c.User.Identity!.Name!,"license.activated",id.ToString());return Ui.Page(c,"License activated","<p>Return to your application. Activation completes automatically.</p><a href='/licenses'>My licenses</a>",narrow:true);
        }).RequireAuthorization();
        app.MapGet("/api/licenses/computers",async(HttpContext c,Store db)=>{
            c.Response.Headers.CacheControl="no-store";
            var token=Bearer(c);
            if(token=="" || !await VerifyProof(c,db,token,"computers"))return Results.Unauthorized();
            var rows=await db.Rows("""
                WITH active AS (
                  SELECT d.id,d.name,d.token_hash,l.user_id
                  FROM eligible_license_devices d JOIN licenses l ON l.id=d.license_id
                  JOIN users u ON u.id=l.user_id
                  WHERE l.product='remote' AND l.status='active' AND u.enabled
                    AND (l.expires_at IS NULL OR l.expires_at>now())
                )
                SELECT host.name,r.room FROM active viewer
                JOIN active host ON host.user_id=viewer.user_id AND host.id<>viewer.id
                JOIN remote_computer_routes r ON r.device_id=host.id
                WHERE viewer.token_hash=$1 ORDER BY lower(host.name),host.id
                """,Auth.Hash(token));
            return Results.Json(rows.Select(r=>new {name=(string)r[0],room=(string)r[1]}));
        }).RequireRateLimiting("license");
        app.MapGet("/api/licenses/access",async(HttpContext c,Store db)=>{
            var token=Bearer(c);if(token=="")return Results.Unauthorized();
            var rows=await db.Rows("SELECT l.id,l.session_limit,d.id,l.product FROM eligible_license_devices d JOIN licenses l ON l.id=d.license_id JOIN users u ON u.id=l.user_id WHERE d.token_hash=$1 AND l.product IN ('remote','meet') AND l.status='active' AND u.enabled AND (l.expires_at IS NULL OR l.expires_at>now())",Auth.Hash(token));
            if(rows.Count!=1)return Results.Unauthorized();
            if(c.Request.Query.TryGetValue("room",out var room)){
                if(!System.Text.RegularExpressions.Regex.IsMatch(room.ToString(),"^[0-9a-f]{64}$") || !await VerifyProof(c,db,token,"relay/"+room))return Results.Unauthorized();
                if ((string)rows[0][3]=="remote") await db.Exec("INSERT INTO remote_computer_routes(device_id,room) VALUES($1,$2) ON CONFLICT(device_id) DO UPDATE SET room=EXCLUDED.room",rows[0][2],room.ToString());
            }
            c.Response.Headers["X-License-Id"]=rows[0][0].ToString();
            c.Response.Headers["X-Session-Limit"]=rows[0][1].ToString();
            return Results.Ok();
        }).RequireRateLimiting("license");
        app.MapGet("/api/licenses/challenge",async(HttpContext c,Store db)=>{
            var token=Bearer(c);if(token=="")return Results.Unauthorized();var challenge=Auth.Token();
            var rows=await db.Rows("UPDATE license_devices SET challenge=$2,challenge_until=now()+interval '60 seconds' WHERE token_hash=$1 AND revoked_at IS NULL AND (license_id IS NOT NULL OR pending_until>now()) RETURNING license_id IS NOT NULL",Auth.Hash(token),challenge);
            if(rows.Count!=1)return Results.Unauthorized();return Results.Json(new{authorized=rows[0][0] is true,challenge});
        }).RequireRateLimiting("license");
        app.MapPost("/api/licenses/lease",async(HttpContext c,Store db,IConfiguration config)=>{
            var token=Bearer(c);if(token==""||c.Request.Headers["X-Nextgen-Client"]!="1")return Results.Unauthorized();var i=await c.Request.ReadFromJsonAsync<Proof>();if(i is null||string.IsNullOrEmpty(i.Signature)||i.Signature.Length>200||i.Challenge is null||i.Challenge.Length!=64)return Results.BadRequest();
            // Consume challenge atomically before verifying proof; replay and races cannot mint leases.
            var rows=await db.Rows("UPDATE license_devices d SET challenge=NULL,challenge_until=NULL FROM licenses l,users u WHERE d.id IN (SELECT id FROM eligible_license_devices) AND d.token_hash=$1 AND d.challenge=$2 AND d.challenge_until>now() AND d.license_id=l.id AND l.user_id=u.id AND u.enabled AND d.revoked_at IS NULL AND l.status='active' AND (l.expires_at IS NULL OR l.expires_at>now()) RETURNING d.id,d.public_key,l.id,l.product,l.edition,l.expires_at",Auth.Hash(token),i.Challenge);
            if(rows.Count!=1)return Results.Unauthorized();var row=rows[0];
            try{using var key=ECDsa.Create();key.ImportSubjectPublicKeyInfo(Convert.FromBase64String((string)row[1]),out _);if(!key.VerifyData(Encoding.UTF8.GetBytes("NextgenLicense/v1:"+i.Challenge),Convert.FromBase64String(i.Signature),HashAlgorithmName.SHA256,DSASignatureFormat.Rfc3279DerSequence))return Results.Unauthorized();}catch(CryptographicException){return Results.Unauthorized();}catch(FormatException){return Results.BadRequest();}
            var now=DateTimeOffset.UtcNow;var expires=now.AddDays(7);if(row[5] is DateTime end && new DateTimeOffset(end)<expires)expires=new DateTimeOffset(end);
            var payload=JsonSerializer.SerializeToUtf8Bytes(new{schema=1,issuer="https://softwarenextgen.com",audience="nextgen-license",product=row[3],edition=row[4],licenseId=row[2],deviceId=row[0],deviceKey=Convert.ToHexString(SHA256.HashData(Convert.FromBase64String((string)row[1]))).ToLowerInvariant(),issued=now.ToUnixTimeSeconds(),expires=expires.ToUnixTimeSeconds()});
            using var signer=ECDsa.Create();signer.ImportFromPem(await File.ReadAllTextAsync(config["LicenseSigningKey"]??"/etc/nextgensoftware/license-signing-key.pem"));
            var signature=signer.SignData(payload,HashAlgorithmName.SHA256,DSASignatureFormat.Rfc3279DerSequence);await db.Exec("UPDATE license_devices SET last_seen=now() WHERE id=$1",row[0]);return Results.Json(new{payload=Convert.ToBase64String(payload),signature=Convert.ToBase64String(signature)});
        }).RequireRateLimiting("license");
    }
    static bool SessionLimit(IFormCollection f,out int limit){
        limit=0;
        return !f.ContainsKey("sessions") || (int.TryParse(f["sessions"],out limit) && limit is >=1 and <=1000);
    }
    internal static async Task<bool> VerifyProof(HttpContext c,Store db,string token,string scope){
        var raw=c.Request.Headers["X-Nextgen-Proof"].ToString();
        if(raw.Length>256)return false;
        var parts=raw.Split('.');
        var now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        if(parts.Length!=3 || !long.TryParse(parts[0],out var timestamp) || timestamp<now-60 || timestamp>now+60 ||
           !System.Text.RegularExpressions.Regex.IsMatch(parts[1],"^[a-f0-9]{32}$"))return false;
        var devices=await db.Rows("SELECT id,public_key FROM eligible_license_devices WHERE token_hash=$1",Auth.Hash(token));
        if(devices.Count!=1)return false;
        using var key=ECDsa.Create();
        try {
            key.ImportSubjectPublicKeyInfo(Convert.FromBase64String((string)devices[0][1]),out _);
            var message=Encoding.UTF8.GetBytes($"NextgenRemote/v2/{scope}/{parts[0]}/{parts[1]}");
            if(!key.VerifyData(message,Convert.FromBase64String(parts[2]),HashAlgorithmName.SHA256,DSASignatureFormat.Rfc3279DerSequence))return false;
        } catch(FormatException){return false;} catch(CryptographicException){return false;}
        await db.Exec("DELETE FROM license_proofs WHERE expires_at<now()");
        return await db.Exec("INSERT INTO license_proofs(device_id,nonce,expires_at) VALUES($1,$2,now()+interval '3 minutes') ON CONFLICT DO NOTHING",devices[0][0],parts[1])==1;
    }
    record DeviceInput(string Product,string Name,string PublicKey);
    record Proof(string Challenge,string Signature);
}
