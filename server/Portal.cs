using System.Security.Claims;
using System.Text.Json;
static class Portal
{
    public static readonly Dictionary<string,(string Name,string Description)> Products=new(){["meet"]=("Nextgen Meet Host","Host video meetings, share a screen and invite free clients by link."),["remote"]=("Nextgen Remote","Connect to a shared desktop with an access key. View the screen, request control and transfer files while the host decides who can interact."),["components"]=("NextgenComponents","A shared visual language for Blazor and Flutter. Explore reusable components, design tokens and working examples for data-rich applications."),["reports"]=("NextgenReportEngine","Design, preview and export structured reports. Work with JSON templates, parameters, tables, charts and barcodes in a local Studio.")};
    public static string ProductIcon(string product)=>product switch { "components"=>"▦", "reports"=>"▤", "remote"=>"⇄", _=>"□" };
    public record Doc(string Title,string Path);
    static string Root(WebApplication app)=>app.Configuration["DocsPath"]??Path.Combine(app.Environment.ContentRootPath,"manuals");
    static List<Doc> Docs(WebApplication app,string product){var file=Path.Combine(Root(app),product,"index.json");return File.Exists(file)?JsonSerializer.Deserialize<List<Doc>>(File.ReadAllText(file))!:new();}
    static string DownloadCards(IEnumerable<object[]> rows)=>"<div class='downloads'>"+string.Join("",rows.Select(r=>"<article class='panel'><span class='badge'>"+Ui.E((string)r[2])+"</span><h3>Version "+Ui.E((string)r[1])+"</h3><p>"+Ui.E((string)r[6])+"</p><p class='muted'>"+((long)r[4]/1048576.0).ToString("F1",System.Globalization.CultureInfo.InvariantCulture)+" MB</p><a class='button' href='/download/"+r[0]+"'>Download installer ↓</a><details><summary>File details & checksum</summary><p>"+Ui.E((string)r[3])+"</p><code class='checksum'>SHA-256: "+r[5]+"</code></details></article>"))+"</div>";
    public static void Map(WebApplication app)
    {
        app.MapGet("/docs",()=>Results.Redirect("/products"));
        app.MapGet("/products",(HttpContext c)=>Ui.Page(c,"Products & documentation","<p class='lede'>Explore the products, browse their guides and find the installer for your platform.</p>"+ProductShowcase.Cards())).AllowAnonymous();
        app.MapGet("/products/{product}",async(HttpContext c,Store db,string product)=>{
            if(!Products.TryGetValue(product,out var p))return Results.NotFound();
            var signed=c.User.Identity?.IsAuthenticated==true;
            var entitled=signed && await Licenses.CanDownload(c,db,product);
            var rows=entitled?await db.Rows("SELECT id,version,platform,filename,size,sha256,notes FROM releases WHERE product=$1 AND published ORDER BY created_at DESC",product):new List<object[]>();
            if(product=="meet" && entitled && rows.Count>0) {
                var hosts=rows.Where(r=>((string)r[3]).StartsWith("NextgenMeetHost-", StringComparison.Ordinal)).ToList();
                var current=hosts.DistinctBy(r=>(string)r[2]).ToList();
                var archive=rows.Except(current).ToList();
                var downloads=current.Count==0?"<p>Host installers are being prepared.</p>":DownloadCards(current);
                if(archive.Count>0) downloads+="<details class='meet-archive'><summary>All other installer versions</summary>"+DownloadCards(archive)+"</details>";
                return Ui.Page(c,"Nextgen Meet",ProductShowcase.Meet(downloads,true));
            }
            var cards=!signed?"<div class='notice'><p>Explore the documentation and live previews freely. Sign in with your account and an active product license to download installers.</p><a class='button' href='/login'>Sign in to download →</a></div>":!entitled?"<p class='notice'>A product license is required. <a href='/licenses'>View your licenses</a> or contact your administrator.</p>":rows.Count==0?"<p class='notice'>Installers are being prepared. Documentation is available below.</p>":DownloadCards(rows);
            if(product=="meet") return Ui.Page(c,"Nextgen Meet",ProductShowcase.Meet(cards,signed));
            var docs=Docs(app,product);
            var gallery=product=="components"?Previews.Gallery(docs):product=="remote"?"<section class='remote-overview'><img src='/images/remote-overview.svg' width='960' height='380' alt='A host shares its desktop with a viewer through an encrypted connection'><h2>Your screen. Your permission.</h2><p>Start sharing on the host, enter its access key on the viewing device, then request control when needed. The host can allow, revoke or end the session.</p><div class='actions'><a class='button' href='/docs/remote/getting-started'>Start a remote session</a><a class='text-link' href='https://connect.softwarenextgen.com' target='_blank' rel='noopener'>Open browser viewer ↗</a></div><p class='muted'>Current release · Linux x64, macOS Apple Silicon and Windows x64 packages. OS permissions are required. See the installation guide for runtime requirements and signing information.</p></section>":"";
            var guideLinks=product=="components"?ComponentCatalog.Links(docs):"<div class='doc-list'>"+string.Join("",docs.Select(d=>"<a href='/docs/"+product+"/"+d.Path+"'>"+Ui.E(d.Title)+"<span>→</span></a>"))+"</div>";
            return Ui.Page(c,p.Name,"<div class='product-overview'><span class='badge'>PRODUCT DOCUMENTATION</span><p class='lede'>"+p.Description+"</p><div class='product-meta'><span>Linux, macOS & Windows</span><span>Documentation included</span><span>Private downloads</span></div></div><nav class='section-nav'>"+(product=="components"?"<a href='#component-previews'>Component previews</a>":"")+"<a href='#downloads'>Downloads</a><a href='#documentation'>Documentation & manuals</a></nav><section id='downloads'><h2>Install on your computer</h2>"+cards+"</section>"+gallery+"<section id='documentation'><h2>Documentation & manuals</h2><p>Product descriptions, setup instructions, developer references and practical examples.</p><label class='doc-search'>Find a guide<input type='search' data-doc-search placeholder='Search documentation and manuals…'></label><p class='muted' data-doc-count>All guides</p>"+guideLinks+"</section>");
        }).AllowAnonymous();
        app.MapGet("/docs/{product}/{**path}",(HttpContext c,string product,string? path)=>{
            if(!Products.ContainsKey(product))return Results.NotFound();path??="overview";var docs=Docs(app,product);var doc=docs.FirstOrDefault(d=>d.Path==path);if(doc is null)return Results.NotFound();
            var file=Path.Combine(Root(app),product,doc.Path+".html");if(!File.Exists(file))return Results.NotFound();
            var nav="<aside class='docs-nav'><a class='back-link' href='/products/"+product+"'>← "+Products[product].Name+"</a>"+(product=="components"?ComponentCatalog.Links(docs,path):string.Join("",docs.Select(d=>"<a "+(d.Path==path?"aria-current='page'":"")+" href='/docs/"+product+"/"+d.Path+"'>"+Ui.E(d.Title)+"</a>")))+"</aside>";
            return Ui.Page(c,doc.Title,"<div class='docs-layout'>"+nav+"<article class='prose'>"+Previews.Render(product,path,doc.Title)+new System.Text.RegularExpressions.Regex("<h1[^>]*>.*?</h1>",System.Text.RegularExpressions.RegexOptions.Singleline).Replace(File.ReadAllText(file),m=>{var id=System.Text.RegularExpressions.Regex.Match(m.Value,"id=\"([^\"]+)\"");return id.Success?"<span class='doc-title-anchor' id='"+Ui.E(id.Groups[1].Value)+"'></span>":"";},1)+"</article></div>");
        }).AllowAnonymous();
        app.MapGet("/download/{id:guid}",async(HttpContext c,Store db,Files files,Guid id)=>{
            var rows=await db.Rows("SELECT storage_name,filename,product FROM releases WHERE id=$1 AND published",id);if(rows.Count==0){c.Response.StatusCode=404;return;}
            if(!await Licenses.CanDownload(c,db,(string)rows[0][2])){c.Response.StatusCode=403;return;}
            await db.Audit(c.User.Identity!.Name!,"download",id.ToString());await files.Download(c,(string)rows[0][0],(string)rows[0][1]);
        }).RequireAuthorization();
    }
}
