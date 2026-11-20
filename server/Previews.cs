static class Previews
{
    public static string Gallery(IEnumerable<Portal.Doc> docs)
    {
        var components=docs.Where(d=>d.Path.StartsWith("manual/Ng")).ToList();
        return "<section id='component-previews' class='component-catalog'><div class='section-heading'><div><span class='eyebrow'>EXPLORE THE COLLECTION</span><h2>Every component. Ready to try.</h2></div><p>"+components.Count+" live examples, organized by purpose. Choose a component to try it and explore its manual.</p></div><label class='doc-search'>Find a component<input type='search' data-component-search placeholder='Search buttons, grids, charts…'></label><nav class='category-nav' aria-label='Component categories'>"+string.Join("",ComponentCatalog.Groups(components).Select((g,i)=>"<a href='#category-"+i+"'>"+Ui.E(g.Key)+"</a>"))+"</nav><p class='muted' data-component-count>"+components.Count+" components</p>"+string.Join("",ComponentCatalog.Groups(components).Select((g,i)=>"<section class='component-category' id='category-"+i+"' data-component-category><h3 class='category-title'>"+Ui.E(g.Key)+"<span>"+g.Count()+" components</span></h3><div class='component-cards'>"+string.Join("",g.Select(d=>"<article class='component-card' data-component-card><div class='component-card-heading'>"+ComponentCatalog.Thumbnail(d)+"<div><h3>"+Ui.E(ComponentCatalog.Name(d))+"</h3><p>"+Ui.E(d.Title.Contains(" — ")?d.Title.Split(" — ")[1]:d.Title)+"</p></div></div><details data-component-preview><summary>Live preview <span aria-hidden='true'>↗</span></summary><div class='component-demo' data-preview-src='/preview/components/preview/"+Ui.E(ComponentCatalog.Name(d))+"' data-preview-name='"+Ui.E(ComponentCatalog.Name(d))+"'></div></details><a class='component-manual' href='/docs/components/"+d.Path+"'>Documentation & examples →</a></article>"))+"</div></section>"))+"<p data-component-empty hidden>No matching components. Try another search.</p></section>";
    }
    public static string Render(string product,string path,string title)
    {
        if(product=="remote") return "";
        if(product=="components"){
            if(path=="manual/grouped-remote-ranges")return "<section id='live-example' class='preview-panel'><div class='preview-toolbar'><strong>Grouped remote ranges · 10,000 synthetic records</strong><a href='/preview/components/grouped-range' target='_blank' rel='noopener'>Open example ↗</a><button type='button' data-reload-preview>Reset</button></div><iframe class='component-frame' src='/preview/components/grouped-range' title='Grouped remote ranges interactive preview' loading='lazy'></iframe></section>";
            var name=path.Split('/').Last();if(!name.StartsWith("Ng")||!name.All(char.IsAsciiLetterOrDigit))name="NgDataGrid";
            return "<section id='live-example' class='preview-panel'><div class='preview-toolbar'><div><span class='live-dot'></span><strong>Live component preview</strong><span class='preview-subtitle'>Try the controls · demonstration data</span></div><a class='small-link' href='/preview/components/preview/"+name+"' target='_blank' rel='noopener'>Open preview ↗</a><button type='button' class='small secondary' data-reload-preview>Reset</button></div><iframe class='component-frame' src='/preview/components/preview/"+name+"' title='"+Ui.E(name)+" interactive preview' loading='lazy'></iframe></section>";
        }
        return "<section class='preview-panel topic-preview'><div class='preview-toolbar'><div><span class='live-dot'></span><strong>"+Ui.E(title)+" — example</strong><span class='preview-subtitle'>Explore this topic with included sample inputs and engine-generated results</span></div><a href='/report-examples/index.html?topic="+Uri.EscapeDataString(path)+"' target='_blank' rel='noopener'>Open example ↗</a></div><iframe class='report-topic-frame' src='/report-examples/index.html?topic="+Uri.EscapeDataString(path)+"' title='"+Ui.E(title)+" working example' loading='lazy'></iframe></section>";
    }

    public static void Map(WebApplication app)
    {
        app.MapGet("/preview/reports/{sample}/{file}",(string sample,string file)=>{
            if(sample is not("sales" or "charts")||!System.Text.RegularExpressions.Regex.IsMatch(file,@"^(sample\.pdf|page-\d+\.png)$"))return Results.NotFound();
            var path=Path.Combine(app.Environment.ContentRootPath,"previews","reports",sample,file);if(!File.Exists(path))return Results.NotFound();return Results.File(path,file.EndsWith(".pdf")?"application/pdf":"image/png",enableRangeProcessing:true);
        }).AllowAnonymous();
        app.MapGet("/preview/reports/{sample}/manifest",(string sample)=>{
            if(sample is not("sales" or "charts"))return Results.NotFound();
            var directory=Path.Combine(app.Environment.ContentRootPath,"previews","reports",sample);
            return Results.Json(new{pages=Directory.GetFiles(directory,"page-*.png").Select(Path.GetFileName).OrderBy(f=>int.Parse(f!.Split('-')[1].Split('.')[0])).ToArray()});
        }).AllowAnonymous();
    }
}
