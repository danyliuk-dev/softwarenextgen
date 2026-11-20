using System.Text.RegularExpressions;
static class HomeShowcase
{
    record Example(string Label,string Image,string Demo,string Guide,string Description);
    record Category(string Label,Example[] Examples);
    static readonly Category[] Components = ComponentCatalog.Categories.Select(c=>new Category(c.Name,c.Topics.Where(n=>n.StartsWith("Ng")).Select(n=>new Example(Regex.Replace(n[2..],"([a-z])([A-Z])","$1 $2"),n,"/preview/components/preview/"+n,"/docs/components/manual/"+n,"Explore "+n+" in a working Blazor example, then open its component guide.")).ToArray())).ToArray();
    static Example Report(string topic,string label,string description)=>new(label,"report-"+topic,"/report-examples/index.html?topic="+topic,"/docs/reports/"+topic,description);
    static readonly Category[] Reports = [
        new("Design & authoring",[
            Report("overview","Report preview","Switch between sample reports, browse pages and download generated output."),
            Report("report-authoring-manual","Parameters & preview","Set parameters and generate a matching report preview."),
            Report("template-format","Template format","Inspect valid templates and see structured validation results."),
            Report("toolbox","Dialog Toolbox","Explore report parameter controls and their generated output."),
            Report("agent-authoring","Agent-assisted authoring","Validate an included template and inspect the authoring workflow.")]),
        new("Data & connections",[
            Report("data-import","CSV, TSV & Excel","Import the included data fixtures and inspect their rows."),
            Report("data-preparation","Data preparation","Filter source data and generate regional summaries."),
            Report("data-sources","SQL, JSON & objects","Explore data-source examples and their included files."),
            Report("http-connections","HTTP data","Refresh the included HTTP snapshots and compare report output.")]),
        new("Interaction & logic",[
            Report("drill-down","Drill-down","Choose an order and open its detail report."),
            Report("report-logic-manual","Scripts & events","Explore validation logic and report event examples."),
            Report("report-library","Report library","Save and restore demo versions in this browser.")]),
        new("Export",[
            Report("office-export","Excel & Word","Try export content modes and page ranges."),
            Report("image-export","PNG & SVG","Choose image formats, resolution and pages to export.")]),
        new("SDKs & integration",[
            Report("developer-guide","Developer workflow","Inspect example requests, responses and generated outputs."),
            Report("dotnet-integration",".NET & Blazor","Explore the .NET client and Blazor viewer integration example."),
            Report("flutter-integration","Flutter","Inspect the Flutter client workflow and report response.")]),
        new("Installation & guides",[
            Report("installation","Installation","Choose your platform and follow the first-launch steps."),
            Report("desktop","Desktop Studio","Explore the installed desktop workflow for Linux, macOS and Windows."),
            Report("index","Documentation tour","Find the matching guide and working example for each report task.")])
    ];
    public static string Render()=>"<section id='live-previews' class='home-showcases' aria-labelledby='showcase-heading'><div class='section-heading'><div><span class='eyebrow'>EXPLORE THE POSSIBILITIES</span><h2 id='showcase-heading'>Real tools.<br>See them at work.</h2></div><p>Explore actual product screens, then open a working example. No sign-in needed.</p></div>"+
        Block("components","01 / INTERFACES","NextgenComponents","A better interface. <br>One component at a time.","Explore all 47 components for Blazor and Flutter. Choose a category and a component to see its working Blazor example.","47 components · 8 categories","Explore all components","/products/components#component-previews",Components,3)+
        Block("reports","02 / REPORTING","NextgenReportEngine","Give your data <br>a clearer story.","From data and parameters to paginated reports. Explore all 20 examples across authoring, data, interaction, export, SDKs and installation.","20 working examples · 6 categories","Explore reporting","/products/reports",Reports,0)+"</section>";
    static string Block(string id,string eyebrow,string name,string headline,string copy,string facts,string linkText,string link,Category[] categories,int initial)
    {
        var first=categories[initial].Examples[0];
        var tabs=string.Join("",categories.Select((c,i)=>$"<button type='button' class='showcase-choice' aria-pressed='{(i==initial?"true":"false")}' data-showcase-category='{i}'>{Ui.E(c.Label)}</button>"));
        var options=string.Join("",categories.SelectMany((c,i)=>c.Examples.Select((e,j)=>$"<option value='{Ui.E(e.Image)}' data-category='{i}' data-image='/images/home/{e.Image}.webp' data-demo='{Ui.E(e.Demo)}' data-guide='{Ui.E(e.Guide)}' data-description='{Ui.E(e.Description)}' {(i==initial&&j==0?"selected":"")}>{Ui.E(e.Label)}</option>")));
        return $"""
        <article class='product-showcase showcase-{id}' data-home-showcase aria-labelledby='{id}-showcase-title'>
          <div class='showcase-copy'><span class='eyebrow'>{eyebrow}</span><p class='showcase-product'>{name}</p><h3 id='{id}-showcase-title'>{headline}</h3><p>{copy}</p><p class='showcase-facts'>{facts}</p><a class='text-link' href='{link}'>{linkText} ↗</a></div>
          <div class='showcase-visual'><div class='showcase-choices' role='group' aria-label='{name} categories'>{tabs}</div>
            <div class='showcase-picker'><label for='{id}-showcase-example'>{(id=="components"?"Component":"Example")}</label><select id='{id}-showcase-example' data-showcase-select>{options}</select><span data-showcase-count></span></div>
            <div class='showcase-window'><div class='showcase-window-bar'><span class='showcase-dots' aria-hidden='true'>● ● ●</span><span>{name}</span><span class='showcase-mode' data-showcase-mode>PRODUCT PREVIEW</span></div>
              <div class='showcase-screen' data-showcase-screen><img data-showcase-image src='/images/home/{first.Image}.webp' width='1200' height='800' alt='{name}: {first.Label} working example' loading='lazy'></div>
              <div class='showcase-toolbar'><button type='button' class='button' data-showcase-play aria-expanded='false'>Try live demo <span aria-hidden='true'>↗</span></button><a data-showcase-open href='{first.Demo}' target='_blank' rel='noopener'>Open demo ↗</a><a data-showcase-guide href='{first.Guide}'>Read guide →</a></div>
            </div><p class='showcase-caption' data-showcase-description>{first.Description}</p><span class='showcase-status' data-showcase-status role='status'></span>
          </div>
        </article>
        """;
    }
}
