const list = document.getElementById("list");
const tabs = document.getElementById("tabs");
let view = "open";

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;   // textContent => no HTML injection
  return e;
}

function card(r) {
  const c = el("div", "card " + r.kind + (r.handled ? " done" : ""));
  const top = el("div", "top");
  top.append(el("span", "tag", r.kind === "order" ? "ORDER" : "CALLBACK: " + r.category));
  if (r.needs_human) top.append(el("span", "tag human", "NEEDS A PERSON"));
  if (r.status === "incomplete") top.append(el("span", "tag", "INCOMPLETE"));
  top.append(el("span", "", new Date(r.created_at).toLocaleString()));
  c.append(top, el("div", "name", r.name || "(no name)"));
  if (r.phone) {
    const p = el("div", "row");
    if (/^\d+$/.test(r.phone)) {
      const a = el("a", "", r.phone); a.href = "tel:" + r.phone; p.append(a);
    } else p.textContent = r.phone;
    c.append(p);
  }
  if (r.items) c.append(el("div", "row", "Order: " + r.items));
  if (r.fulfilment) c.append(el("div", "row", r.fulfilment[0].toUpperCase() + r.fulfilment.slice(1)));
  if (r.address) c.append(el("div", "row", "Address: " + r.address));
  c.append(el("div", "row", "Customer said: " + r.message));
  r.notes.forEach(n => c.append(el("div", "note", "Note: " + n)));
  if (!r.handled) {
    const b = el("button", "", "Mark handled");
    b.onclick = async () => {
      b.disabled = true;
      await fetch("/api/admin/handled", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-Requested-With": "admin"},
        body: JSON.stringify({id: r.id}),
      });
      load();
    };
    c.append(b);
  }
  return c;
}

async function load() {
  try {
    const r = await fetch("/api/admin/enquiries?view=" + view);
    if (!r.ok) throw new Error();
    const rows = await r.json();
    list.replaceChildren(...(rows.length ? rows.map(card) : [el("div", "empty", "Nothing here.")]));
  } catch (e) {
    list.replaceChildren(el("div", "empty", "Could not load enquiries."));
  }
}

tabs.addEventListener("click", (e) => {
  if (!e.target.dataset.view) return;
  view = e.target.dataset.view;
  tabs.querySelectorAll("button").forEach(b => b.classList.toggle("on", b === e.target));
  load();
});
load();
setInterval(load, 15000);
