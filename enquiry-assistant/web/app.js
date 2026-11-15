const log = document.getElementById("log");
const form = document.getElementById("form");
const msg = document.getElementById("msg");
const btn = form.querySelector("button");
let session = sessionStorage.getItem("session") || "";

function add(text, who) {
  const d = document.createElement("div");
  d.className = "bubble " + who;
  d.textContent = text;            // textContent => no HTML injection
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}

add("Hi! I'm the Fire Away Ashton assistant. Ask about opening hours, delivery or deals, or tell me what you'd like to order.", "bot");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = msg.value.trim();
  if (!text) return;
  add(text, "me");
  msg.value = "";
  btn.disabled = true;
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({session, message: text}),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "error");
    session = data.session;
    sessionStorage.setItem("session", session);
    add(data.reply, "bot");
  } catch (err) {
    add("Sorry, something went wrong. Please call us on 0161 526 4777.", "bot");
  } finally {
    btn.disabled = false;
    msg.focus();
  }
});
