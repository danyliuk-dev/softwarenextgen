using System.Net.Mail;
using System.Security.Cryptography;
using System.Text;
using Npgsql;

static class Admin
{
    public static async Task<string> Invite(Store db,Guid userId,string email,Microsoft.AspNetCore.DataProtection.IDataProtector protector)
    {
        await using var conn=await db.Source.OpenConnectionAsync();await using var tx=await conn.BeginTransactionAsync();
        var token = await QueueInvitation(conn, tx, userId, email, protector);
        await tx.CommitAsync();
        return token;
    }
    internal static async Task<string> QueueInvitation(NpgsqlConnection conn, NpgsqlTransaction tx, Guid userId,
        string email, Microsoft.AspNetCore.DataProtection.IDataProtector protector)
    {
        var token=Auth.Token();var id=Guid.NewGuid();
        async Task Run(string sql,params object[] values){await using var command=new NpgsqlCommand(sql,conn,tx);foreach(var value in values)command.Parameters.AddWithValue(value);await command.ExecuteNonQueryAsync();}
        await Run("UPDATE invitations SET used_at=now() WHERE user_id=$1 AND used_at IS NULL",userId);
        await Run("INSERT INTO invitations(id,user_id,token_hash,expires_at) VALUES($1,$2,$3,now()+interval '48 hours')",id,userId,Auth.Hash(token));
        await Run("INSERT INTO mail_outbox(id,invitation_id,recipient,payload) VALUES($1,$2,$3,$4)",Guid.NewGuid(),id,email,Convert.ToBase64String(protector.Protect(Encoding.UTF8.GetBytes(token))));
        return token;
    }
    public static void Map(WebApplication app)
    {
        app.MapGet("/admin",async(HttpContext c,Store db)=>{
            var users = new AdminList(c,"","active","inactive");
            var rows = await users.Load(db,"SELECT id,email,role,enabled,mfa,created_at,CASE WHEN enabled THEN 'active' ELSE 'inactive' END status,CASE WHEN enabled THEN 'Enabled' ELSE 'Blocked' END access,CASE WHEN mfa THEN 'Connected' ELSE 'Pending' END authenticator FROM users");
            var table="<div class='table-wrap'><table><thead><tr><th>Email</th><th>Role</th><th>Status</th><th>2FA</th><th>Date added</th><th>Actions</th></tr></thead><tbody>"+(rows.Count==0?AdminList.Empty(6):"")+string.Join("",rows.Select(r=>"<tr><td>"+Ui.E((string)r[1])+"</td><td>"+r[2]+"</td><td>"+((bool)r[3]?"Enabled":"Blocked")+"</td><td>"+((bool)r[4]?"Connected":"Pending")+"</td><td>"+AdminList.Added(r[5])+"</td><td>"+((string)r[2]=="admin"?"Owner":Ui.Form(c,"/admin/users/"+r[0]+"/toggle","<button class='small secondary'>"+((bool)r[3]?"Block":"Enable")+"</button>")+Ui.Form(c,"/admin/users/"+r[0]+"/invite","<button class='small secondary'>Send password invite</button>"))+"</td></tr>"))+"</tbody></table></div>";
            var delivery = new AdminList(c,"mail","pending","accepted","failed","cancelled");
            var mail = await delivery.Load(db,"SELECT m.recipient,m.status,m.attempts,m.error,i.created_at,m.id,m.next_attempt,m.accepted_at FROM mail_outbox m JOIN invitations i ON i.id=m.invitation_id");
            return Ui.Page(c,"Administration","<nav class='section-nav'><a href='/admin'>Users & invitations</a><a href='/admin/releases'>Product releases</a><a href='/admin/licenses'>Clients & licenses</a></nav><div class='panel'><h2>Invite a user</h2><p>A one-use link lets the recipient choose a password. Assign product licenses under Clients & licenses. Existing 2FA is preserved when resetting a password.</p>"+Ui.Form(c,"/admin/invite","<label>Email address<input type='email' name='email' required maxlength='254' placeholder='name@company.com'></label><button>Send invitation →</button>")+"</div><h2>Users</h2>"+users.Controls("users")+table+users.Paging()+"<h2>Invitation delivery</h2>"+delivery.Controls("invitations")+"<div class='table-wrap'><table><thead><tr><th>Email</th><th>Status</th><th>Attempts</th><th>Details</th><th>Date added</th></tr></thead><tbody>"+(mail.Count==0?AdminList.Empty(5):"")+string.Join("",mail.Select(r=>"<tr><td>"+Ui.E((string)r[0])+"</td><td>"+r[1]+"</td><td>"+r[2]+"</td><td>"+Ui.E((string)r[3])+"</td><td>"+AdminList.Added(r[4])+"</td></tr>"))+"</tbody></table></div>"+delivery.Paging());
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/invite",async(HttpContext c,Store db)=>{
            var email=(await c.Request.ReadFormAsync())["email"].ToString().Trim().ToLowerInvariant();
            if(email.Length>254||!MailAddress.TryCreate(email,out var address)||address.Address!=email)return Ui.Error(c,"Invalid email","Enter a valid email address.","/admin");
            var id=Guid.NewGuid();var added=await db.Exec("INSERT INTO users(id,email,role,generation) VALUES($1,$2,'user',$3) ON CONFLICT(email) DO NOTHING",id,email,Guid.NewGuid());
            if(added==0)return Ui.Error(c,"Account already exists","Use the existing account's invitation action.","/admin");
            await Invite(db,id,email,Auth.Protector(c));await db.Audit(c.User.Identity!.Name!,"user.invited",email);return Results.Redirect("/admin");
        }).RequireAuthorization("Admin").RequireRateLimiting("auth");
        app.MapPost("/admin/users/{id:guid}/invite",async(HttpContext c,Store db,Guid id)=>{
            var rows=await db.Rows("SELECT email FROM users WHERE id=$1 AND role='user' AND enabled",id);if(rows.Count==0)return Results.NotFound();
            // Invalidate all current sessions. Keep existing MFA intact for password recovery.
            await db.Exec("UPDATE users SET generation=$2 WHERE id=$1 AND role='user'",id,Guid.NewGuid());
            await Invite(db,id,(string)rows[0][0],Auth.Protector(c));await db.Audit(c.User.Identity!.Name!,"user.reinvited",(string)rows[0][0]);return Results.Redirect("/admin");
        }).RequireAuthorization("Admin").RequireRateLimiting("auth");
        app.MapPost("/admin/users/{id:guid}/toggle",async(HttpContext c,Store db,Guid id)=>{await db.Exec("UPDATE users SET enabled=NOT enabled,generation=$2 WHERE id=$1 AND role='user'",id,Guid.NewGuid());await db.Audit(c.User.Identity!.Name!,"user.access_toggled",id.ToString());return Results.Redirect("/admin");}).RequireAuthorization("Admin");
        app.MapGet("/admin/releases",async(HttpContext c,Store db)=>{
            var releases = new AdminList(c,"","published","hidden");
            var rows = await releases.Load(db,"SELECT id,product,version,platform,published,filename,created_at,CASE WHEN published THEN 'published' ELSE 'hidden' END status,notes,size,sha256 FROM releases");
            return Ui.Page(c,"Product releases","<nav class='section-nav'><a href='/admin'>Users & invitations</a><a href='/admin/releases'>Product releases</a><a href='/admin/licenses'>Clients & licenses</a></nav><div class='panel'><h2>Publish an installer</h2><p>Files are stored in the private release bucket. Maximum upload: 1 GB. On proxied Cloudflare connections, use the deployment importer for files larger than the plan's request limit.</p><form method='post' action='/admin/releases' enctype='multipart/form-data'>"+Ui.Csrf(c)+"<div class='form-grid'><label>Product<select name='product'><option value='components'>NextgenComponents</option><option value='reports'>NextgenReportEngine</option><option value='meet'>Nextgen Meet</option><option value='remote'>Nextgen Remote</option></select></label><label>Version<input name='version' required maxlength='40'></label><label>Platform<select name='platform'><option>Linux x64</option><option>macOS Apple Silicon</option><option>macOS Intel</option><option>Windows x64</option></select></label><label>Installer<input type='file' name='file' accept='.AppImage,.deb,.dmg,.pkg,.zip,.gz,.exe' required></label></div><label>Release notes<textarea name='notes' maxlength='2000' rows='3'></textarea></label><button>Upload & publish</button></form></div><h2>Versions</h2>"+releases.Controls("releases")+"<div class='table-wrap'><table><thead><tr><th>Product</th><th>Version</th><th>Platform</th><th>File</th><th>Date added</th><th>Visibility</th></tr></thead><tbody>"+(rows.Count==0?AdminList.Empty(6):"")+string.Join("",rows.Select(r=>"<tr><td>"+Ui.E((string)r[1])+"</td><td>"+Ui.E((string)r[2])+"</td><td>"+Ui.E((string)r[3])+"</td><td>"+Ui.E((string)r[5])+"</td><td>"+AdminList.Added(r[6])+"</td><td>"+Ui.Form(c,"/admin/releases/"+r[0]+"/toggle","<button class='small secondary'>"+((bool)r[4]?"Published · hide":"Hidden · publish")+"</button>")+"</td></tr>"))+"</tbody></table></div>"+releases.Paging());
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/releases",async(HttpContext c,Store db,Files files)=>{
            var f=await c.Request.ReadFormAsync();var file=f.Files.GetFile("file");var product=f["product"].ToString();var version=f["version"].ToString();var platform=f["platform"].ToString();var notes=f["notes"].ToString();
            if(!Portal.Products.ContainsKey(product)||!new[]{"Linux x64","macOS Apple Silicon","macOS Intel","Windows x64"}.Contains(platform)||version.Length is <1 or >40||notes.Length>2000||file is null||file.Length is <=0 or >1073741824)return Ui.Error(c,"Invalid release","Check the product, version, platform and installer file.","/admin/releases");
            var filename=Path.GetFileName(file.FileName);
            if(!System.Text.RegularExpressions.Regex.IsMatch(filename,@"^[A-Za-z0-9][A-Za-z0-9._-]{0,179}\.(AppImage|deb|dmg|pkg|zip|gz|exe)$"))return Ui.Error(c,"Invalid filename","Use a supported installer with a simple filename.","/admin/releases");
            await using var stream=file.OpenReadStream();var hash=Convert.ToHexString(await SHA256.HashDataAsync(stream,c.RequestAborted));stream.Position=0;var id=Guid.NewGuid();var key=product+"/"+id+"/"+filename;
            await files.Upload(key,stream,c.RequestAborted);await db.Exec("INSERT INTO releases(id,product,version,platform,filename,storage_name,size,sha256,notes) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)",id,product,version,platform,filename,key,file.Length,hash,notes);await db.Audit(c.User.Identity!.Name!,"release.published",id.ToString());return Results.Redirect("/admin/releases");
        }).RequireAuthorization("Admin");
        app.MapPost("/admin/releases/{id:guid}/toggle",async(HttpContext c,Store db,Guid id)=>{await db.Exec("UPDATE releases SET published=NOT published WHERE id=$1",id);await db.Audit(c.User.Identity!.Name!,"release.visibility_toggled",id.ToString());return Results.Redirect("/admin/releases");}).RequireAuthorization("Admin");
    }
}
