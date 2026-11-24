"use strict";
function addReactions(item,id) {
    item.dataset.message = id;
    item.reactions = {};
    const strip = document.createElement("div");
    strip.className = "chat-reactions";
    for (const emoji of reactions) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = emoji;
        button.ariaLabel = "React "+emoji;
        button.setAttribute("aria-pressed","false");
        button.onclick = () => {
            if (session?.visible) send(session,{type:"reaction",id,emoji,on:!item.reactions[emoji]?.includes(session.me)});
        };
        strip.append(button);
    }
    item.append(strip);
}
function updateReaction(event) {
    if (!/^[a-f0-9]{32}$/.test(event.id) || !reactions.includes(event.emoji)) return;
    const item = el("messages").querySelector('[data-message="'+event.id+'"]');
    if (!item) return;
    applyReaction(item.reactions,event.emoji,event.from,event.on);
    const users = item.reactions[event.emoji];
    const button = item.lastElementChild.children[reactions.indexOf(event.emoji)];
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
