// JavaScript port of the Python assistant (classifier + responder + collector).
// Kept in step with the Python code by tests/test_js_parity.py.
// Rules/data are injected (generated from the Python modules by build_web_demo.py).
function createEngine(D) {
  const rx = (p, f) => new RegExp(p, f || "");
  const RULES = {};
  for (const [c, ps] of Object.entries(D.rules)) RULES[c] = ps.map((p) => rx(p));
  const WEAK = D.weak_order.map((p) => rx(p));
  const CHAT = rx("^(?:" + D.chitchat + ")$");
  const TOPICS = D.topics.map(([t, ps]) => [t, ps.map((p) => rx(p))]);
  const DAYPAT = {};
  for (const [d, p] of Object.entries(D.day_patterns)) DAYPAT[d] = rx(p);
  const MENU_WORDS = rx(D.menu_words), CANCEL = rx(D.cancel), POSTCODE = rx(D.postcode);
  const NAME_PREFIX = rx(D.name_prefix, "i");
  const HUMAN = new Set(D.human_categories);
  const kb = D.kb, DAYS = D.days, MAX_INPUT = D.max_input;

  // ---------- classifier ----------
  const normalise = (m) => String(m == null ? "" : m).toLowerCase()
    .replace(/’/g, "'").replace(/\s+/g, " ").trim();

  function classify(message) {
    const text = normalise(message);
    if (CHAT.test(text.replace(/[^a-z0-9' ]/g, "").trim()))
      return { category: "chitchat", needs_human: false };
    const orderText = text.replace("minimum order", "");
    const hits = {};
    for (const cat of D.priority) {
      const subject = cat === "order" ? orderText : text;
      if (RULES[cat].some((r) => r.test(subject))) hits[cat] = true;
    }
    const keys = Object.keys(hits);
    if (!keys.length) {
      if (WEAK.some((r) => r.test(text))) return { category: "order", needs_human: false };
      return { category: "unknown", needs_human: true };
    }
    for (const cat of D.priority)
      if (hits[cat]) return { category: cat, needs_human: HUMAN.has(cat) };
  }

  // ---------- responder ----------
  const isTodo = (v) => typeof v === "string" && v.trim().toUpperCase().startsWith("TODO");
  const ok = (...vs) => vs.every((v) => v && !isTodo(v));
  const sentence = (t) => { t = t.trim(); return t && ".!?".includes(t[t.length - 1]) ? t : t + "."; };
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  function handoff(why) {
    why = why || "that";
    const ph = kb.business.phone;
    const tail = ok(ph) ? ` You can also call us on ${ph}.` : "";
    return `I'll get a team member to confirm ${why} for you.${tail}`;
  }
  function detectTopic(text) {
    for (const [t, ps] of TOPICS) if (ps.some((r) => r.test(text))) return t;
    return null;
  }
  function hoursAnswer(text) {
    const h = kb.opening_hours;
    if (!DAYS.every((d) => ok(h[d]))) return null;
    const asked = DAYS.filter((d) => DAYPAT[d].test(text));
    if (asked.length) {
      const d = asked[0];
      return `On ${cap(d)} we're open ${h[d]}. Closing times are after midnight, so that's the following morning.`;
    }
    const groups = new Map();
    for (const d of DAYS) {
      if (!groups.has(h[d])) groups.set(h[d], []);
      groups.get(h[d]).push(cap(d.slice(0, 3)));
    }
    const parts = [...groups].map(([hh, days]) => `${days.join(", ")}: ${hh}`);
    return "We're open seven days a week. " + parts.join(". ") +
      ". Closing times are after midnight, so that's the following morning.";
  }
  function deliveryAnswer() {
    const o = kb.ordering;
    if (!ok(o.delivery_available, o.delivery_area)) return null;
    const r = [sentence(o.delivery_available), "We cover: " + sentence(o.delivery_area)];
    if (ok(o.delivery_charge)) r.push("Delivery charge: " + sentence(o.delivery_charge));
    if (ok(o.minimum_order)) r.push("Minimum order: " + sentence(o.minimum_order));
    if (ok(o.delivery_time)) r.push(sentence(o.delivery_time));
    return r.join(" ");
  }
  const dietary = (k) => () => (ok(kb.dietary[k]) ? sentence(kb.dietary[k]) : null);
  const ANSWERS = {
    hours: hoursAnswer, delivery: deliveryAnswer,
    collection: () => (ok(kb.ordering.collection_time) ? sentence(kb.ordering.collection_time) : null),
    payment: () => (ok(kb.payments) ? sentence(kb.payments) : null),
    halal: dietary("halal"), vegetarian: dietary("vegetarian"), vegan: dietary("vegan"),
    deals: () => {
      const d = kb.deals || [];
      return !d.length || d.some(isTodo) ? null : "Our current deals:\n- " + d.join("\n- ");
    },
    menu: () => {
      const cats = kb.menu_categories || [], items = kb.menu_highlights || [];
      if (!cats.length || !items.length || items.some(isTodo)) return null;
      const site = kb.business.website || "";
      const more = ok(site) ? ` See the full menu at ${site}.` : "";
      return "Our menu has: " + cats.join(", ") + ". Popular items:\n- " + items.join("\n- ") + "\n" + more.trim();
    },
    contact: (text) => {
      const b = kb.business;
      if (text.includes("email")) return ok(b.email) ? `Our email address is ${b.email}.` : null;
      if (!ok(b.address, b.phone)) return null;
      return `You can find us at ${b.address}. Our phone number is ${b.phone}.`;
    },
  };

  function respond(message) {
    const c = classify(message);
    const text = String(message == null ? "" : message).toLowerCase();
    const phone = kb.business.phone;
    const R = (category, reply, needs_human, topic) => ({ category, reply, needs_human, topic: topic || "" });
    if (c.category === "chitchat") {
      let reply;
      if (/\b(thank|thx|cheers|ta)\b/.test(text)) reply = "You're welcome! Is there anything else I can help with?";
      else if (/\b(bye|goodbye|see you|cya)\b/.test(text)) reply = "Thanks for getting in touch. Bye for now!";
      else if (/\b(ok|okay|k|great|perfect|lovely|nice one)\b/.test(text)) reply = "Great! Is there anything else I can help with?";
      else reply = "Hi! How can I help? You can ask about opening hours, delivery or deals, or tell me what you'd like to order.";
      return R("chitchat", reply, false, "chitchat");
    }
    if (c.category === "allergy") {
      const policy = kb.allergens.policy;
      let reply = ok(policy) ? sentence(policy)
        : "Thanks for asking. For allergy and dietary-safety questions we always want a team member to confirm the answer, so we never guess.";
      reply += " " + handoff("the details");
      return R("allergy", reply, true, "allergy");
    }
    if (c.category === "complaint") {
      let reply = "I'm sorry to hear that. I'm passing this to a team member who will look into it.";
      if (ok(phone)) reply += ` You can also call us on ${phone}.`;
      return R("complaint", reply, true, "complaint");
    }
    if (c.category === "booking") {
      const b = kb.bookings;
      return ok(b.how_to_book) ? R("booking", sentence(b.how_to_book), false, "booking")
                               : R("booking", handoff("booking details"), true, "booking");
    }
    if (c.category === "order") {
      const o = kb.ordering;
      if (ok(o.methods)) {
        let reply = "Happy to help with an order! " + sentence(o.methods);
        if (ok(o.collection_time)) reply += " Collection: " + sentence(o.collection_time);
        return R("order", reply, false, "order");
      }
      return R("order", handoff("your order"), true, "order");
    }
    if (c.category === "faq") {
      const topic = detectTopic(text);
      const answer = topic ? ANSWERS[topic](text) : null;
      return answer ? R("faq", answer, false, topic) : R("faq", handoff(), true, topic || "");
    }
    return R(c.category, handoff(), true, "");
  }

  // ---------- details collector ----------
  const normalisePhone = (text) => {
    let s = String(text || "").replace(/[\s\-().]/g, "");
    if (s.startsWith("+44") || s.startsWith("0044")) {
      const rest = s.startsWith("+44") ? s.slice(3) : s.slice(4);
      s = rest.startsWith("0") ? rest : "0" + rest;
    }
    return /^(?:07\d{9}|0[123]\d{8,9})$/.test(s) ? s : null;
  };
  const parseName = (text) => {
    let raw = String(text || "").trim().replace(/’/g, "'");
    raw = raw.replace(NAME_PREFIX, "").trim();
    if (!/^[A-Za-z][A-Za-z' \-]{1,49}$/.test(raw)) return null;
    return raw === raw.toLowerCase() ? raw.replace(/(^|[^A-Za-z])([a-z])/g, (m, a, b) => a + b.toUpperCase()) : raw;
  };
  const parsePostcode = (text) => {
    const m = POSTCODE.exec(text || "");
    return m ? `${m[1].toUpperCase()} ${m[2].toUpperCase()}` : null;
  };
  const VALIDATORS = {
    items: (t) => (t.length >= 3 && t.length <= 300 ? [t, null] : [null, "Sorry, could you tell me what you'd like to order?"]),
    fulfilment: (t) => {
      const l = t.toLowerCase();
      if (/\bdeliver\w*|\bbring\b/.test(l)) return ["delivery", null];
      if (/\bcollect\w*|\bpick.?up\b|\bcome\b/.test(l)) return ["collection", null];
      return [null, "Sorry, is that for collection or delivery?"];
    },
    name: (t) => { const n = parseName(t); return n ? [n, null] : [null, "Sorry, I didn't catch your name. Could you type it again?"]; },
    phone: (t) => { const p = normalisePhone(t); return p ? [p, null] : [null, "That doesn't look like a UK phone number. Could you check it? For example 07123 456789."]; },
    address: (t) => (parsePostcode(t) && t.length >= 8 ? [t, null]
      : [null, "Please include your full address with the postcode, e.g. 12 High Street, Ashton-under-Lyne OL6 1AA."]),
  };
  const QUESTIONS = {
    items: "What would you like to order?", fulfilment: "Is that for collection or delivery?",
    address: "What's the delivery address (including postcode)?", name: "What's your name?",
    phone: "And the best phone number to reach you on?",
  };
  const LABEL = { items: "order", fulfilment: "collection/delivery choice", address: "delivery address",
    name: "name", phone: "phone number" };
  const nowIso = () => new Date().toISOString().slice(0, 19) + "+00:00";
  const newEnquiry = (kind, category, message, extra) => Object.assign({
    kind, category, message, name: "", phone: "", items: "", fulfilment: "", address: "",
    postcode: "", needs_human: false, status: "complete", notes: [], created_at: nowIso() }, extra || {});

  class Conversation {
    constructor(maxAttempts) { this.max = maxAttempts || 2; this._reset(); }
    _reset() { this.enquiry = null; this.field = null; this.attempts = 0; }
    handle(message) {
      message = String(message == null ? "" : message).trim().slice(0, MAX_INPUT);
      if (this.enquiry) return this._collect(message);
      const r = respond(message);
      if (r.category === "order") return this._startOrder(message);
      if (r.needs_human) return this._startCallback(message, r);
      return { reply: r.reply, done: false, enquiry: null };
    }
    _startOrder(message) {
      const e = newEnquiry("order", "order", message);
      if (MENU_WORDS.test(message.toLowerCase())) e.items = message;
      this.enquiry = e;
      const b = kb.business;
      let intro = "Happy to help! I'll pass your order request to the team.";
      if (ok(b.website, b.phone)) intro += ` (You can also order online at ${b.website} or call ${b.phone}.)`;
      return this._askNext(intro);
    }
    _startCallback(message, r) {
      this.enquiry = newEnquiry("callback", r.category, message, { needs_human: true });
      const note = { allergy: "Allergy/dietary question: staff must answer.", complaint: "Complaint: staff to follow up." }[r.category];
      if (note) this.enquiry.notes.push(note);
      this.field = "name";
      return { reply: `${r.reply} To make sure someone gets back to you, what's your name?`, done: false, enquiry: null };
    }
    _nextField() {
      const e = this.enquiry;
      if (e.kind === "order") {
        if (!e.items) return "items";
        if (!e.fulfilment) return "fulfilment";
        if (e.fulfilment === "delivery" && !e.address) return "address";
      }
      if (!e.name) return "name";
      if (!e.phone) return "phone";
      return null;
    }
    _askNext(prefix) {
      this.field = this._nextField(); this.attempts = 0;
      return { reply: `${prefix} ${QUESTIONS[this.field]}`.trim(), done: false, enquiry: null };
    }
    _collect(text) {
      if (CANCEL.test(text.toLowerCase())) { this._reset(); return { reply: "No problem, I've cancelled that. Message us any time.", done: false, enquiry: null }; }
      const e = this.enquiry, f = this.field;
      const [value, error] = VALIDATORS[f](text);
      if (value === null) {
        this.attempts++;
        if (this.attempts >= this.max) return this._finishIncomplete(f);
        return { reply: error, done: false, enquiry: null };
      }
      e[f] = value;
      let extra = "";
      if (f === "address") { e.postcode = parsePostcode(text); e.notes.push("Delivery area to be confirmed by staff."); }
      if ((f === "items" || f === "name") && classify(value).category === "allergy") {
        e.needs_human = true;
        e.notes.push("Customer mentioned an allergy: staff must confirm.");
        extra = "I've noted your allergy mention; a team member will double-check with you. ";
      }
      if (this._nextField()) return this._askNext(extra.trim());
      return this._finishComplete(extra);
    }
    _finishComplete(extra) {
      const e = this.enquiry; e.status = "complete";
      const phone = kb.business.phone; let reply;
      if (e.kind === "order") {
        const summary = [`Order: ${e.items}`, cap(e.fulfilment)];
        if (e.address) summary.push(`To: ${e.address}`);
        reply = `${extra}Thanks, ${e.name}. I've sent your order request to the team. A team member will contact you on ${e.phone} to confirm. Your order is NOT confirmed until they do.\n` +
          summary.map((s) => `- ${s}`).join("\n");
      } else {
        reply = `${extra}Thanks, ${e.name}. A team member will call you back on ${e.phone}.`;
        if (ok(phone)) reply += ` If it's urgent, call us on ${phone}.`;
      }
      return this._end(reply, e);
    }
    _finishIncomplete(f) {
      const e = this.enquiry; e.status = "incomplete"; e.needs_human = true;
      e.notes.push(`Customer did not give a valid ${LABEL[f]}.`);
      const phone = kb.business.phone;
      let reply = "No problem, I'll pass what I have to the team.";
      if (ok(phone)) reply += ` If it's urgent, please call us on ${phone}.`;
      return this._end(reply, e);
    }
    _end(reply, enquiry) { this._reset(); return { reply, done: true, enquiry }; }
  }

  // ---------- notifier (who gets told) ----------
  function route(e) {
    const urgent = e.category === "allergy" || (e.kind === "order" && e.needs_human);
    if (urgent) return ["whatsapp", "email"];
    return e.kind === "order" ? ["whatsapp"] : ["email"];
  }
  function formatMessage(e) {
    let tag = e.kind === "order" ? "NEW ORDER" : `CALLBACK (${e.category})`;
    if (e.needs_human) tag += " - NEEDS A PERSON";
    if (e.status === "incomplete") tag += " [INCOMPLETE]";
    const lines = [`Enquiry #${e.id} at ${e.created_at}`, `Name: ${e.name || "(not given)"}`, `Phone: ${e.phone || "(not given)"}`];
    if (e.items) lines.push(`Order: ${e.items}`);
    if (e.fulfilment) lines.push(cap(e.fulfilment));
    if (e.address) lines.push(`Address: ${e.address}`);
    lines.push(`Customer said: ${e.message}`);
    e.notes.forEach((n) => lines.push(`Note: ${n}`));
    return [`${tag} - Fire Away Ashton`, lines.join("\n")];
  }
  return { classify, respond, Conversation, route, formatMessage, newEnquiry, normalisePhone, parseName, parsePostcode };
}
if (typeof module !== "undefined") module.exports = { createEngine };
