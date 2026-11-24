"use strict";
function addReactions(item,id) {
    item.dataset.message = id;
    item.reactions = {};
    const strip = document.createElement("div");
    strip.className = "chat-reactions";
    const more = document.createElement("button");
    more.type = "button"; more.textContent = "+"; more.title = more.ariaLabel = "More reactions";
    more.setAttribute("aria-expanded","false");
    more.onclick = () => {
        const open = more.getAttribute("aria-expanded") !== "true";
        more.setAttribute("aria-expanded",String(open));
        more.textContent = open ? "−" : "+";
        more.title = more.ariaLabel = open ? "Fewer reactions" : "More reactions";
        for (const emoji of extraReactions)
            strip.children[reactions.indexOf(emoji)].hidden = !open && !item.reactions[emoji]?.length;
    };
    for (const emoji of reactions) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = emoji;
        button.hidden = extraReactions.includes(emoji);
        button.title = button.ariaLabel = reactionLabels[emoji] || "React "+emoji;
        button.setAttribute("aria-pressed","false");
        button.onclick = () => {
            if (session?.visible) send(session,{type:"reaction",id,emoji,on:!item.reactions[emoji]?.includes(session.me)});
        };
        strip.append(button);
    }
    strip.append(more);
    item.append(strip);
}
function updateReaction(event) {
    if (!/^[a-f0-9]{32}$/.test(event.id) || !reactions.includes(event.emoji)) return;
    const item = el("messages").querySelector('[data-message="'+event.id+'"]');
    if (!item) return;
    applyReaction(item.reactions,event.emoji,event.from,event.on);
    const users = item.reactions[event.emoji];
    const button = item.lastElementChild.children[reactions.indexOf(event.emoji)];
    button.hidden = extraReactions.includes(event.emoji) && !users.length &&
        item.lastElementChild.lastElementChild.getAttribute("aria-expanded") !== "true";
    button.textContent = event.emoji+(users.length ? " "+users.length : "");
    button.setAttribute("aria-pressed",String(users.includes(session.me)));
}
document.addEventListener("DOMContentLoaded",() => {
    const dialog = el("emoji-dialog"), field = el("text"), search = el("emoji-search"), group = el("emoji-category");
    for (const category of categories) group.add(new Option(category.name));
    let start, end;
    function showChoices() {
        el("emoji-grid").replaceChildren(...choices(group.selectedIndex,search.value).map(item => {
            const button = document.createElement("button");
            button.type = "button"; button.title = button.ariaLabel = item.name; button.textContent = item.text;
            button.onclick = () => {
                if (!session?.visible) return;
                field.setRangeText(item.text,start,end,"end");
                dialog.close(); field.focus();
            };
            return button;
        }));
    }
    el("choose-emoji").onclick = () => {
        start=field.selectionStart; end=field.selectionEnd;
        search.value=""; group.selectedIndex=0; showChoices(); dialog.showModal(); search.focus();
    };
    search.oninput=group.onchange=showChoices;
});
