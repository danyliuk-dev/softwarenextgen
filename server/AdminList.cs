using System.Globalization;
using Microsoft.AspNetCore.Http.Extensions;

// List queries project only administrative display fields, IDs and searchable aliases.
sealed class AdminList(HttpContext context, string prefix, params string[] statuses)
{
    string Key(string name) => prefix + name;
    string Read(string name) => context.Request.Query[Key(name)].ToString().Trim();
    public string Search => Read("q");
    string Status => statuses.Contains(Read("status")) ? Read("status") : "";
    bool Oldest => Read("sort") == "oldest";
    int Page => int.TryParse(Read("page"), out var page) ? Math.Clamp(page, 1, 100000) : 1;
    int total, currentPage;

    public async Task<List<object[]>> Load(Store db, string projection)
    {
        var order = Oldest ? "ASC" : "DESC";
        var sql = $"""
            WITH records AS ({projection}), matches AS (
                SELECT * FROM records r
                WHERE ($1 = '' OR r.status = $1 OR ($1 = 'inactive' AND r.status IN ('expired','suspended','revoked','pending')))
                AND ($2 = '' OR EXISTS (
                    SELECT FROM jsonb_each_text(to_jsonb(r)) f
                    WHERE strpos(lower(f.value),lower($2)) > 0
                       OR (f.value ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T'
                           AND strpos(left(replace(f.value,'T',' '),16) || ' utc',lower($2)) > 0))))
            SELECT m.*,count(*) OVER () FROM matches m
            ORDER BY created_at {order},id {order} LIMIT 25 OFFSET $3
            """;
        currentPage = Page;
        var rows = await db.Rows(sql, Status, Search, (currentPage-1)*25);
        if (rows.Count == 0 && currentPage > 1)
        {
            currentPage = 1;
            rows = await db.Rows(sql, Status, Search, 0);
        }
        total = rows.Count == 0 ? 0 : Convert.ToInt32(rows[0][^1]);
        return rows;
    }

    IEnumerable<KeyValuePair<string,string>> OtherParameters()
    {
        string[] known = ["view","q","status","sort","page","mailq","mailstatus","mailsort","mailpage"];
        return context.Request.Query.Where(p => known.Contains(p.Key) &&
            !new[]{"q","status","sort","page"}.Any(k => p.Key == Key(k)))
            .Select(p => KeyValuePair.Create(p.Key,p.Value.ToString()));
    }
    string Url(int page, bool clear = false)
    {
        var query = new QueryBuilder();
        foreach (var p in OtherParameters()) query.Add(p.Key,p.Value);
        if (!clear)
        {
            if (Search.Length > 0) query.Add(Key("q"),Search);
            if (Status.Length > 0) query.Add(Key("status"),Status);
            if (Oldest) query.Add(Key("sort"),"oldest");
            if (page > 1) query.Add(Key("page"),page.ToString());
        }
        return Ui.E(context.Request.Path + query.ToQueryString());
    }
    static string Option(string value,string label,string selected) =>
        "<option value='"+value+"'"+(value==selected?" selected":"")+">"+label+"</option>";
    public string Controls(string label)
    {
        var hidden = string.Concat(OtherParameters().Select(p => "<input type='hidden' name='"+p.Key+"' value='"+Ui.E(p.Value)+"'>"));
        var options = string.Concat(statuses.Select(s => Option(s,char.ToUpperInvariant(s[0])+s[1..],Status)));
        return "<form method='get' class='admin-filters license-search' aria-label='"+label+" filters'>"+hidden+
            "<label>Search "+label+"<input type='search' name='"+Key("q")+"' value='"+Ui.E(Search)+"'></label>"+
            "<label>Status<select name='"+Key("status")+"'>"+Option("","All",Status)+options+"</select></label>"+
            "<label>Date added<select name='"+Key("sort")+"'>"+Option("newest","Newest first",Oldest?"":"newest")+Option("oldest","Oldest first",Oldest?"oldest":"")+"</select></label>"+
            "<button class='secondary'>Apply</button><a href='"+Url(1,true)+"'>Clear</a></form>";
    }
    public string Paging()
    {
        var pages=Math.Max(1,(total+24)/25);
        return "<div class='license-pagination'><span>"+total+" record"+(total==1?"":"s")+" · Page "+currentPage+" of "+pages+"</span><div>"+
            (currentPage>1?"<a href='"+Url(currentPage-1)+"'>← Previous</a>":"")+
            (currentPage<pages?"<a href='"+Url(currentPage+1)+"'>Next →</a>":"")+"</div></div>";
    }
    public static string Added(object value) => ((DateTime)value).ToString("yyyy-MM-dd HH:mm",CultureInfo.InvariantCulture)+" UTC";
    public static string Empty(int columns) => "<tr><td colspan='"+columns+"'>No matching records.</td></tr>";
}
