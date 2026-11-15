# Going live with WhatsApp alerts

Without any setup, alerts are written to `data/outbox/` (demo mode).
To send real WhatsApp messages to the owner:

1. Create a free Meta developer account and a **Business** app at developers.facebook.com; add the **WhatsApp** product.
2. In WhatsApp > API Setup note the **temporary access token** and the **Phone number ID** of the test number.
   Add the owner's phone as a verified recipient (the test number can only message verified numbers).
3. Copy `.env.example` to `.env` and fill in `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_TO` (e.g. `447123456789`, digits only).
4. Restart the server. Orders now go to WhatsApp; failures are retried automatically.

Notes (check Meta's current rules and pricing, they change):
- Free-form messages only reach the owner if they messaged the business number in the last 24 hours. Otherwise you need an **approved message template** with one body variable; set `WHATSAPP_TEMPLATE`.
- Temporary tokens expire (about 24h). A paying client needs a permanent **System User** token and a verified business.
- `.env` holds secrets. It is ignored by Git. Never commit or share it.
