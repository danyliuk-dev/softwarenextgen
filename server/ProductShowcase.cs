static class ProductShowcase
{
    static readonly (string Slug, string Name, string Category, string Image, string Description, string Link)[] Items =
    [
        ("components", "Nextgen<wbr>Components", "UI components", "/images/home/grid.webp", "Build Blazor and Flutter interfaces with data grids, forms, charts and shared design tokens.", "Explore components"),
        ("reports", "Nextgen<wbr>Report<wbr>Engine", "Reporting", "/images/home/report.webp", "Design templates in Studio, connect data and export paginated reports.", "Explore reporting"),
        ("remote", "Nextgen Remote", "Remote desktop", "/images/remote-overview.svg", "Connect to a desktop, request control and transfer files with the host’s permission.", "Explore remote desktop"),
        ("meet", "Nextgen Meet", "Video meetings", "/images/meet/meeting.webp", "Invite people by link, share a window or your screen, and grant control during a call.", "Explore meetings")
    ];

    public static string Cards() => "<div class='product-grid catalog-grid'>" + string.Concat(Items.Select(p => $"""
        <article class='product-card catalog-card catalog-{p.Slug}'>
          <div class='catalog-preview'><img src='{p.Image}' alt='' loading='lazy'></div>
          <div class='catalog-body'><span class='catalog-category'>{p.Category}</span><h2>{p.Name}</h2><p>{p.Description}</p>
          <a class='catalog-link' href='/products/{p.Slug}'>{p.Link}<span aria-hidden='true'>↗</span></a></div>
        </article>
        """)) + "</div>";

    public static string Meet(string hostDownloads, bool signed) => """
        <div class='meet-intro'>
          <div><p class='meet-lead'>Video meetings and screen sharing for Linux, macOS and Windows.</p>
          <p>Start a call on a licensed host and invite guests with a link or an email. Guests can join for free, choose their camera and audio devices, and chat or exchange files during the call.</p>
          <a class='button' href='#downloads'>Get Nextgen Meet <span aria-hidden='true'>↓</span></a></div>
          <a class='meet-shot' href='/images/meet/meeting.webp' aria-label='Open the full-size meeting screenshot'><img src='/images/meet/meeting.webp' alt='Four participants in a meeting with the participant list open' width='1100' height='740'></a>
        </div>
        <section class='meet-section' aria-labelledby='meet-features'><h2 id='meet-features'>Inside a meeting</h2>
          <div class='meet-gallery'>
            <figure><a class='meet-shot' href='/images/meet/lobby.webp'><img src='/images/meet/lobby.webp' alt='Guest lobby with name and invitation fields' width='1100' height='740' loading='lazy'></a>
            <figcaption><h3>Join by invitation</h3><p>Open the link, enter your name and join. The invitation page offers the guest app if you need to install it.</p></figcaption></figure>
            <figure><a class='meet-shot' href='/images/meet/presentation.webp'><img src='/images/meet/presentation.webp' alt='A shared application fills the meeting stage beside the participant list' width='1100' height='740' loading='lazy'></a>
            <figcaption><h3>Present or work together</h3><p>Choose an application window or share the entire screen. For hands-on collaboration, grant a participant control of the shared desktop and revoke it when finished.</p></figcaption></figure>
          </div>
        </section>
        <section id='downloads' class='meet-section'><h2>Install Nextgen Meet</h2>
          <div class='meet-guest'><h3>Join as a guest</h3><p>Download the free guest app for your computer, then open your invitation.</p>
          <div class='actions'><a class='button secondary' href='/meet/download/linux'>Linux x64 (.deb)</a><a class='button secondary' href='/meet/download/macos'>macOS Apple Silicon</a><a class='button secondary' href='/meet/download/windows'>Windows x64</a></div></div>
          <h3>Host a meeting</h3>
        """ + (signed ? hostDownloads : "<p>Sign in with the account that holds your Meet Host license to download the host app.</p><a class='button' href='/login'>Sign in for Host downloads</a>") + "</section>";
}
