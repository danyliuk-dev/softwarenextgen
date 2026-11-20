using System.Security.Claims;
using System.Security.Cryptography;
using System.Text.Json;

static class RemoteUpdates
{
    const string ReturnCookie="__Host-NextgenUpdateCode";
    static bool Code(string value)=>System.Text.RegularExpressions.Regex.IsMatch(value,"^[A-F0-9]{10}$");
    public static string AfterLogin(HttpContext c) {
        var licenseCode=c.Request.Cookies["__Host-NextgenLicenseCode"]??"";
        c.Response.Cookies.Delete("__Host-NextgenLicenseCode",new CookieOptions{Secure=true,Path="/"});
        if(Code(licenseCode))return "/licenses/activate?code="+licenseCode;
        var code=c.Request.Cookies[ReturnCookie]??"";
        c.Response.Cookies.Delete(ReturnCookie,new CookieOptions{Secure=true,Path="/"});
        return Code(code)?"/updates/remote/activate?code="+code:"/products";
    }
    static string Bearer(HttpContext c) {
        var h=c.Request.Headers.Authorization.ToString();
        return h.StartsWith("Bearer ")&&h.Length==71?h[7..]:"";
    }
    public static void Map(WebApplication app) {
        app.MapPost("/api/remote-updates/device",async(HttpContext c,Store db)=>{
            if(c.Request.Headers["X-Nextgen-Client"]!="1")return Results.BadRequest();
            var input=await c.Request.ReadFromJsonAsync<DeviceInput>();
            if(input is null||string.IsNullOrWhiteSpace(input.Name)||input.Name.Length>80)return Results.BadRequest();
            var token=Auth.Token();var code=Convert.ToHexString(RandomNumberGenerator.GetBytes(5));
            await db.Exec("DELETE FROM remote_update_devices WHERE user_id IS NULL AND expires_at<now()");
            await db.Exec("INSERT INTO remote_update_devices(id,token_hash,code,name,expires_at) VALUES($1,$2,$3,$4,now()+interval '10 minutes')",Guid.NewGuid(),Auth.Hash(token),code,input.Name);
            return Results.Json(new{token,code,activationUrl="https://softwarenextgen.com/updates/remote/activate?code="+code,expiresIn=600});
        }).RequireRateLimiting("auth");
        app.MapGet("/api/remote-updates/device",async(HttpContext c,Store db)=>{
            var token=Bearer(c);if(token=="")return Results.Unauthorized();
            var rows=await db.Rows("SELECT d.user_id IS NOT NULL, COALESCE(u.enabled,false) FROM remote_update_devices d LEFT JOIN users u ON u.id=d.user_id WHERE d.token_hash=$1 AND d.revoked_at IS NULL AND d.expires_at>now()",Auth.Hash(token));
            if(rows.Count!=1)return Results.Unauthorized();
            if(rows[0][0] is true && rows[0][1] is not true)return Results.Unauthorized();
            return Results.Json(new{authorized=rows[0][0] is true});
        });
        app.MapGet("/updates/remote/activate",async(HttpContext c,Store db,string? code)=>{
            code=(code??"").ToUpperInvariant();if(!Code(code))return Ui.Error(c,"Invalid code","Open the authorization link from Nextgen Remote.");
            if(c.User.Identity?.IsAuthenticated!=true){c.Response.Cookies.Append(ReturnCookie,code,new CookieOptions{Secure=true,HttpOnly=true,SameSite=SameSiteMode.Lax,Path="/",MaxAge=TimeSpan.FromMinutes(10)});return Results.Redirect("/login");}
            var rows=await db.Rows("SELECT name FROM remote_update_devices WHERE code=$1 AND user_id IS NULL AND revoked_at IS NULL AND expires_at>now()",code);
            if(rows.Count!=1)return Ui.Error(c,"Code expired or already used","Start authorization again from Nextgen Remote.");
            return Ui.Page(c,"Authorize automatic updates","<p>Computer: <strong>"+Ui.E((string)rows[0][0])+"</strong></p><p>Confirm this code matches the code shown in your Nextgen Remote window:</p><pre>"+Ui.E(code)+"</pre><p>This allows this computer to download Nextgen Remote updates without signing in again. You can revoke access in your account.</p>"+Ui.Form(c,"/updates/remote/activate","<input type='hidden' name='code' value='"+code+"'><label><input type='checkbox' name='confirm' value='yes' required> I requested this authorization on my computer</label><button>Authorize this computer</button>"),narrow:true);
        });
        app.MapPost("/updates/remote/activate",async(HttpContext c,Store db)=>{
            var form=await c.Request.ReadFormAsync();var code=form["code"].ToString();
            if(!Code(code)||form["confirm"]!="yes")return Results.BadRequest();
            if(!await Licenses.Entitled(db,Guid.Parse(c.User.FindFirstValue(ClaimTypes.NameIdentifier)!),"remote",true))return Ui.Error(c,"License required","Ask your administrator to assign a Nextgen Remote license.","/licenses");
            var changed=await db.Exec("UPDATE remote_update_devices SET user_id=$2,approved_at=now(),expires_at=now()+interval '5 years' WHERE code=$1 AND user_id IS NULL AND revoked_at IS NULL AND expires_at>now()",code,Guid.Parse(c.User.FindFirstValue(ClaimTypes.NameIdentifier)!));
            if(changed!=1)return Ui.Error(c,"Code expired or already used","Start authorization again from Nextgen Remote.");
            await db.Audit(c.User.Identity!.Name!,"remote.updates.authorized",code);
            return Ui.Page(c,"Computer authorized","<p>Return to Nextgen Remote. Automatic updates are now enabled for this computer.</p><a href='/updates/remote/devices'>Manage computers</a>",narrow:true);
        }).RequireAuthorization();
        app.MapGet("/updates/remote/devices",async(HttpContext c,Store db)=>{
            var rows=await db.Rows("SELECT id,name,approved_at FROM remote_update_devices WHERE user_id=$1 AND revoked_at IS NULL ORDER BY approved_at DESC",Guid.Parse(c.User.FindFirstValue(ClaimTypes.NameIdentifier)!));
            var cards=string.Join("",rows.Select(r=>"<article class='panel'><h2>"+Ui.E((string)r[1])+"</h2><p>Authorized "+Ui.E(r[2].ToString()!)+"</p>"+Ui.Form(c,"/updates/remote/revoke","<input type='hidden' name='id' value='"+r[0]+"'><button>Revoke update access</button>")+"</article>"));
            return Ui.Page(c,"Computers with update access",rows.Count==0?"<p>No computers authorized.</p>":cards);
        }).RequireAuthorization();
        app.MapPost("/updates/remote/revoke",async(HttpContext c,Store db)=>{
            var form=await c.Request.ReadFormAsync();if(!Guid.TryParse(form["id"],out var id))return Results.BadRequest();
            await db.Exec("UPDATE remote_update_devices SET revoked_at=now() WHERE id=$1 AND user_id=$2",id,Guid.Parse(c.User.FindFirstValue(ClaimTypes.NameIdentifier)!));
            await db.Audit(c.User.Identity!.Name!,"remote.updates.revoked",id.ToString());return Results.Redirect("/updates/remote/devices");
        }).RequireAuthorization();
        app.MapGet("/api/remote-updates/manifest",(HttpContext c,IConfiguration config)=>{
            var agent=c.Request.Headers.UserAgent.ToString();
            var legacy=agent.StartsWith("NextgenRemote/",StringComparison.Ordinal) && Version.TryParse(agent["NextgenRemote/".Length..],out var version) && version<new Version(0,4,2);
            var file=Path.Combine(config["RemoteUpdatesPath"]??"/var/lib/nextgensoftware/remote-updates",legacy?"bootstrap-042.json":"stable.json");
            c.Response.Headers.Vary="User-Agent";
            return File.Exists(file)?Results.File(file,"application/json"):Results.StatusCode(503);
        });
        app.MapGet("/api/remote-updates/package/{sha}/{filename}",async(HttpContext c,Store db,Files files,string sha,string filename)=>{
            var token=Bearer(c);if(token==""){c.Response.StatusCode=401;return;}
            var devices=await db.Rows("SELECT d.id FROM remote_update_devices d JOIN users u ON u.id=d.user_id WHERE d.token_hash=$1 AND d.revoked_at IS NULL AND d.expires_at>now() AND u.enabled",Auth.Hash(token));
            if(devices.Count==1){
                var owner=await db.Rows("SELECT user_id FROM remote_update_devices WHERE id=$1",devices[0][0]);
                if(!await Licenses.Entitled(db,(Guid)owner[0][0],"remote",true)){c.Response.StatusCode=403;return;}
            }else{
                devices=await db.Rows("SELECT d.id FROM eligible_license_devices d JOIN licenses l ON l.id=d.license_id JOIN users u ON u.id=l.user_id WHERE d.token_hash=$1 AND d.revoked_at IS NULL AND l.product='remote' AND l.status='active' AND u.enabled AND (l.expires_at IS NULL OR l.expires_at>now()) AND (l.updates_until IS NULL OR l.updates_until>now())",Auth.Hash(token));
                if(devices.Count!=1){c.Response.StatusCode=401;return;}
            }
            var rows=await db.Rows("SELECT storage_name,filename,id,version FROM releases WHERE product='remote' AND published AND lower(sha256)=lower($1) AND filename=$2",sha,filename);
            if(rows.Count!=1){c.Response.StatusCode=404;return;}
            // Older installed clients can bootstrap to 0.4.2. Later packages require device proof.
            var bootstrap=(string)rows[0][3]=="0.4.2" && !c.Request.Headers.ContainsKey("X-Nextgen-Proof") && (await db.Rows("SELECT 1 FROM license_bootstrap_devices WHERE token_hash=$1",Auth.Hash(token))).Count==1;
            if(!bootstrap && !await Licenses.VerifyProof(c,db,token,"package/"+sha.ToLowerInvariant())){c.Response.StatusCode=403;return;}
            await db.Audit(devices[0][0].ToString()!,"remote.updates.download",rows[0][2].ToString()!);
            await files.Download(c,(string)rows[0][0],(string)rows[0][1]);
        });
    }
    record DeviceInput(string Name);
}
