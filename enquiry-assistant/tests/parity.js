// Runs messages + scripted chats through the JS engine and prints JSON.
// usage: node tests/parity.js data.json cases.json
const fs = require("fs");
const { createEngine } = require("../web_demo/engine.js");
const E = createEngine(JSON.parse(fs.readFileSync(process.argv[2], "utf8")));
const cases = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const out = { messages: cases.messages.map((m) => {
    const r = E.respond(m), c = E.classify(m);
    return [c.category, c.needs_human, r.reply, r.needs_human, r.topic];
  }),
  chats: cases.chats.map((chat) => {
    const conv = new E.Conversation();
    return chat.map((m) => {
      const t = conv.handle(m);
      const e = t.enquiry;
      return [t.reply, t.done, e && [e.kind, e.category, e.name, e.phone, e.items,
        e.fulfilment, e.address, e.postcode, e.needs_human, e.status, e.notes]];
    });
  }),
  phones: cases.phones.map((p) => E.normalisePhone(p)),
  names: cases.names.map((n) => E.parseName(n)),
  postcodes: cases.postcodes.map((p) => E.parsePostcode(p)) };
process.stdout.write(JSON.stringify(out));
