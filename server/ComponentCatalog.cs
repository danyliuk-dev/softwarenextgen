static class ComponentCatalog
{
    public static readonly (string Name,string[] Topics)[] Categories = [
        ("Buttons & actions", ["NgButton","NgButtonGroup","NgToggleButton","NgChip","NgChipList"]),
        ("Inputs & forms", ["NgTextBox","NgTextArea","NgNumericTextBox","NgCheckBox","NgSwitch","NgRadioGroup","NgAutoComplete","NgComboBox","NgDropDownList","NgMultiSelect","NgForm"]),
        ("Dates & scheduling", ["NgCalendar","NgDateInput","NgDatePicker","NgDateRangePicker","NgDateTimePicker","NgTimePicker","NgScheduler"]),
        ("Data & documents", ["NgDataGrid","grid-editing","grid-export","remote-grouped-data","remote-ranges","grouped-remote-ranges","virtual-data","NgPivotGrid","NgTreeList","NgSpreadsheet","NgEditor","NgPdfViewer","NgPager"]),
        ("Charts & visualization", ["NgChart","NgArcGauge","NgLinearGauge","NgDiagram","NgMap"]),
        ("Navigation & layout", ["NgBreadcrumb","NgMenu","NgDrawer","NgTabs","NgTreeView","NgStepper","NgWizard"]),
        ("Dialogs & feedback", ["NgDialog","NgNotification","NgTooltip"]),
        ("AI & prompts", ["NgAIPrompt","NgPromptBox"])
    ];
    public static string Name(Portal.Doc doc)=>doc.Path.Split('/').Last();
    public static string Category(Portal.Doc doc)=>Categories.FirstOrDefault(c=>c.Topics.Contains(Name(doc))).Name??(doc.Path.StartsWith("manual/Ng")?"More components":"Guides & getting started");
    public static IEnumerable<IGrouping<string,Portal.Doc>> Groups(IEnumerable<Portal.Doc> docs)=>docs.GroupBy(Category).OrderBy(g=>g.Key=="Guides & getting started"?-1:Array.FindIndex(Categories,c=>c.Name==g.Key));
    public static string Thumbnail(Portal.Doc doc)=>doc.Path.StartsWith("manual/Ng")?"<img class='component-thumbnail' src='/images/components/"+Ui.E(Name(doc))+".svg' alt='' width='64' height='64' loading='lazy'>":"";
    public static string Links(IEnumerable<Portal.Doc> docs,string? current=null)=>string.Join("",Groups(docs).Select(g=>"<section class='doc-category' data-doc-category><h3>"+Ui.E(g.Key)+"</h3><div class='doc-list'>"+string.Join("",g.OrderBy(d=>Array.IndexOf(Categories.FirstOrDefault(c=>c.Name==g.Key).Topics??[],Name(d))).Select(d=>"<a "+(current==d.Path?"aria-current='page'":"")+" href='/docs/components/"+d.Path+"'>"+Thumbnail(d)+"<span class='doc-link-title'>"+Ui.E(d.Title)+"</span><span aria-hidden='true'>→</span></a>"))+"</div></section>"));
}
