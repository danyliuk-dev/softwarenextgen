using System.Globalization;

static partial class Licenses
{
    static string AdminNav=>"<nav class='section-nav'><a href='/admin'>Users & invitations</a><a href='/admin/licenses' aria-current='page'>Clients & licenses</a><a href='/admin/releases'>Releases</a></nav>";
    static string Table(string headings,string rows,int columns)=>"<div class='table-wrap license-table'><table><thead><tr>"+string.Join("",headings.Split('|').Select(h=>"<th>"+h+"</th>"))+"</tr></thead><tbody>"+(rows==""?"<tr><td colspan='"+columns+"' class='license-empty'>No matching records.</td></tr>":rows)+"</tbody></table></div>";
    static string Date(object value)=>value is DateTime d?d.ToString("yyyy-MM-dd",CultureInfo.InvariantCulture):"Perpetual";
    static string ProductSearch => " CASE l.product "+string.Join(" ",Portal.Products.Select(p => "WHEN '"+p.Key+"' THEN '"+p.Value.Name.Replace("'","''")+"'"))+" END AS product_name";
    static void MapAdminList(WebApplication app)
    {
        app.MapGet("/admin/licenses",async(HttpContext c,Store db)=>{
            var view=c.Request.Query["view"].ToString();if(!new[]{"clients","licenses","devices"}.Contains(view))view="clients";
            var statuses = view switch {
                "licenses" => new[]{"active","inactive","suspended","revoked","expired"},
                "devices" => new[]{"active","inactive","pending","expired","revoked"},
                _ => new[]{"active","inactive"}
            };
            var list = new AdminList(c,"",statuses);
            var q = list.Search;
            var users = await db.Rows("SELECT id,email FROM users ORDER BY email");
            var counts = (await db.Rows("SELECT (SELECT count(*) FROM licenses),(SELECT count(*) FROM license_devices)"))[0];
            const string clientFields = "concat_ws(' ',c.first_name,c.last_name,c.organization) AS client_name";
            var projection = view switch {
                "clients" => """
                    SELECT u.id,u.email,coalesce(c.first_name,'') AS first_name,coalesce(c.last_name,'') AS last_name,
                           coalesce(c.kind,'private') AS kind,coalesce(c.organization,'') AS organization,
                           coalesce(c.created_at,u.created_at) AS created_at,CASE WHEN u.enabled THEN 'active' ELSE 'inactive' END status,
                           coalesce(nullif(trim(concat_ws(' ',c.first_name,c.last_name)),''),'Profile not completed') AS display_name
                    FROM users u LEFT JOIN customers c ON c.user_id=u.id
                    """,
                "licenses" => """
                    SELECT l.id,u.email,l.product,l.edition,l.seats,
                           CASE WHEN l.status='active' AND l.expires_at<=now() THEN 'expired' ELSE l.status END status,
                           l.expires_at,(SELECT count(*) FROM license_devices d WHERE d.license_id=l.id AND d.revoked_at IS NULL) AS installations,
                           l.created_at,l.session_limit,l.updates_until,l.legacy,
                           CASE WHEN l.expires_at IS NULL THEN 'Perpetual' END AS duration,
                    """ + ProductSearch + "," + clientFields + " FROM licenses l JOIN users u ON u.id=l.user_id LEFT JOIN customers c ON c.user_id=u.id",
                _ => """
                    SELECT d.id,d.name,coalesce(u.email,'') AS email,d.product,d.last_seen,d.created_at,
                           CASE WHEN d.revoked_at IS NOT NULL THEN 'revoked' WHEN d.license_id IS NOT NULL THEN 'active'
                                WHEN d.pending_until<=now() THEN 'expired' ELSE 'pending' END status,
                           d.approved_at,d.revoked_at,CASE WHEN d.last_seen IS NULL THEN 'Not yet connected' END AS connection,
                    """ + ProductSearch.Replace("l.product","d.product") + "," + clientFields + " FROM license_devices d LEFT JOIN licenses l ON l.id=d.license_id LEFT JOIN users u ON u.id=l.user_id LEFT JOIN customers c ON c.user_id=u.id"
            };
            var shown = await list.Load(db,projection);
            string Tab(string v) => "/admin/licenses?view="+v+"&amp;q="+Ui.E(Uri.EscapeDataString(q));
            var tabs="<nav class='license-tabs' aria-label='Client and license sections'>"+string.Join("",new[]{("clients","Clients",(long)users.Count),("licenses","Licenses",(long)counts[0]),("devices","Devices",(long)counts[1])}.Select(t=>"<a href='"+Tab(t.Item1)+"'"+(view==t.Item1?" aria-current='page'":"")+">"+t.Item2+" <span>"+t.Item3+"</span></a>"))+"</nav>";
            var search=list.Controls(view);
            var create="";string table;
            if(view=="clients"){
                create="<details class='license-create'><summary>Add client</summary><p>Register the client, assign a license, then send an invitation from Users & invitations.</p>"+Ui.Form(c,"/admin/licenses/customer","<div class='form-grid'>"+Field("first","First name")+Field("last","Last name")+Field("email","Email","email")+"<label>Customer type<select name='kind'><option value='private'>Private</option><option value='organization'>Organization</option></select></label><label class='license-wide'>Organization<input name='organization' maxlength='254' placeholder='Required for an organization'></label></div><button>Register client</button>")+"</details>";
                table=Table("Client|Email|Type|Organization|Status|Date added|Actions",string.Join("",shown.Select(r=>"<tr><td><strong>"+Ui.E(string.IsNullOrWhiteSpace(r[2]+" "+r[3])?"Profile not completed":r[2]+" "+r[3])+"</strong></td><td>"+Ui.E((string)r[1])+"</td><td>"+((string)r[4]=="private"?"Private":"Organization")+"</td><td>"+Ui.E((string)r[5])+"</td><td>"+r[7]+"</td><td>"+AdminList.Added(r[6])+"</td><td class='license-actions'><a href='/admin/customers/"+r[0]+"'>Edit</a><a href='/admin/licenses?view=licenses&amp;q="+Ui.E(Uri.EscapeDataString((string)r[1]))+"'>Licenses</a></td></tr>")),7);
            }else if(view=="licenses"){
                create="<details class='license-create'><summary>Issue license</summary>"+Ui.Form(c,"/admin/licenses/create","<div class='form-grid'><label>Client<select name='user'>"+string.Join("",users.Select(r=>"<option value='"+r[0]+"'"+((string)r[1]==q?" selected":"")+">"+Ui.E((string)r[1])+"</option>"))+"</select></label><label>Product<select name='product'>"+SelectProducts()+"</select></label>"+Field("edition","Edition",value:"Standard")+"<label>Concurrent sessions<input type='number' name='sessions' min='1' max='1000' value='16' required></label><label>Installation limit<input type='number' name='seats' min='1' max='100000' value='3' required></label><label>Expires<input type='date' name='expires'><small>Leave blank for a perpetual license.</small></label></div><button>Issue license</button>")+"</details>";
                table=Table("Client|Product / edition|Devices|Status|Expires|Date added|",string.Join("",shown.Select(r=>"<tr><td>"+Ui.E((string)r[1])+"</td><td>"+Ui.E(Portal.Products[(string)r[2]].Name)+"<small>"+Ui.E((string)r[3])+"</small></td><td>"+r[7]+" / "+r[4]+"</td><td><span class='license-status status-"+r[5]+"'>"+r[5]+"</span></td><td>"+Date(r[6])+"</td><td>"+AdminList.Added(r[8])+"</td><td><a href='/admin/licenses/"+r[0]+"'>Edit</a></td></tr>")),7);
            }else{
                table=Table("Device|Client|Product|Last seen|Status|Date added|",string.Join("",shown.Select(r=>"<tr><td><strong>"+Ui.E((string)r[1])+"</strong></td><td>"+Ui.E((string)r[2])+"</td><td>"+Ui.E(Portal.Products[(string)r[3]].Name)+"</td><td>"+(r[4] is DateTime d?d.ToString("yyyy-MM-dd HH:mm",CultureInfo.InvariantCulture)+" UTC":"Not yet connected")+"</td><td>"+r[6]+"</td><td>"+AdminList.Added(r[5])+"</td><td>"+((string)r[6]=="active"?Ui.Form(c,"/admin/licenses/device/revoke","<input type='hidden' name='id' value='"+r[0]+"'><button class='small secondary'>Deactivate</button>"):"")+"</td></tr>")),7);
            }
            var paging=list.Paging();
            return Ui.Page(c,"Clients & licenses",AdminNav+"<section class='license-workspace'>"+tabs+"<div class='license-toolbar'>"+search+"</div>"+create+table+paging+"</section>");
        }).RequireAuthorization("Admin");
        app.MapGet("/admin/licenses/{id:guid}",async(HttpContext c,Store db,Guid id)=>{
            var rows=await db.Rows("SELECT u.email,l.product,l.edition,l.status,l.seats,l.expires_at,l.session_limit FROM licenses l JOIN users u ON u.id=l.user_id WHERE l.id=$1",id);if(rows.Count!=1)return Results.NotFound();var r=rows[0];
            var fields="<input type='hidden' name='id' value='"+id+"'><div class='form-grid'><label>Status<select name='status'>"+string.Join("",new[]{"active","suspended","revoked"}.Select(status=>"<option"+((string)r[3]==status?" selected":"")+">"+status+"</option>"))+"</select></label><label>Concurrent sessions<input type='number' name='sessions' min='1' max='1000' value='"+r[6]+"' required></label><label>Installation limit<input type='number' name='seats' min='1' max='100000' value='"+r[4]+"' required></label><label class='license-wide'>Expires<input type='date' name='expires' value='"+(r[5] is DateTime dt?dt.ToString("yyyy-MM-dd"):"")+"'><small>Leave blank for a perpetual license.</small></label></div><p>Reducing the installation limit keeps the earliest activations eligible. Raising it restores eligibility. Cached offline permissions remain valid until expiry.</p><div class='license-actions'><button>Save changes</button><a href='/admin/licenses?view=licenses'>Cancel</a></div>";
            return Ui.Page(c,"Edit license","<div class='license-editor'><p><strong>"+Ui.E((string)r[0])+"</strong><br>"+Ui.E(Portal.Products[(string)r[1]].Name)+" · "+Ui.E((string)r[2])+"</p>"+Ui.Form(c,"/admin/licenses/change",fields)+"</div>",narrow:true);
        }).RequireAuthorization("Admin");
    }
}
