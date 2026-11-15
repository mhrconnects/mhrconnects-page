"""WhatsApp Business Cloud API channel (Meta).

Sends a notification to the business owner's WhatsApp. Configure with a
`.env` file (Git-ignored; copy .env.example) or real environment variables:

    WHATSAPP_TOKEN            access token from Meta (SECRET)
    WHATSAPP_PHONE_NUMBER_ID  the sending number's ID (not the number itself)
    WHATSAPP_TO               owner's number, international digits, e.g. 447123456789
    WHATSAPP_TEMPLATE         (optional) approved template name; needed to
                              message the owner outside the 24-hour window
    WHATSAPP_LANG             (optional) template language, default en_GB
    WHATSAPP_API_BASE         (optional) default https://graph.facebook.com/v21.0

If the first three are missing, nothing is sent over the network and the
notifier falls back to the demo outbox files.
The token is never written to logs or error messages.
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_API_BASE = "https://graph.facebook.com/v21.0"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
MAX_TEXT = 4096


def load_env(path=ENV_FILE):
    """Read KEY=VALUE lines from a .env file (no libraries needed)."""
    values = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


class WhatsAppChannel:
    name = "whatsapp"

    def __init__(self, token, phone_number_id, to, template=None,
                 lang="en_GB", api_base=DEFAULT_API_BASE, timeout=10):
        digits = re.sub(r"\D", "", to or "")
        if not (token and phone_number_id and 8 <= len(digits) <= 15):
            raise ValueError("WhatsApp settings are incomplete or invalid")
        if not re.fullmatch(r"\d+", str(phone_number_id)):
            raise ValueError("WHATSAPP_PHONE_NUMBER_ID must be digits")
        self._token, self.to = token, digits
        self.phone_number_id = str(phone_number_id)
        self.template, self.lang = template, lang
        self.url = f"{api_base.rstrip('/')}/{self.phone_number_id}/messages"
        self.timeout = timeout

    def _payload(self, text):
        if self.template:
            # Template parameters may not contain newlines/tabs.
            flat = re.sub(r"\s*\n\s*", " | ", text).replace("\t", " ")
            flat = re.sub(r" {2,}", " ", flat)[:1000]
            return {"messaging_product": "whatsapp", "to": self.to,
                    "type": "template",
                    "template": {"name": self.template,
                                 "language": {"code": self.lang},
                                 "components": [{"type": "body", "parameters": [
                                     {"type": "text", "text": flat}]}]}}
        return {"messaging_product": "whatsapp", "to": self.to, "type": "text",
                "text": {"preview_url": False, "body": text[:MAX_TEXT]}}

    def send(self, subject, body):
        data = json.dumps(self._payload(f"{subject}\n{body}")).encode()
        req = urllib.request.Request(self.url, data=data, headers={
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"WhatsApp API error {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError("WhatsApp API unreachable") from None


def whatsapp_from_env(env=None):
    """Build a channel from settings, or return None if not configured."""
    cfg = {**load_env(), **os.environ} if env is None else env
    token, pid, to = (cfg.get("WHATSAPP_TOKEN"), cfg.get("WHATSAPP_PHONE_NUMBER_ID"),
                      cfg.get("WHATSAPP_TO"))
    if not (token and pid and to):
        return None
    return WhatsAppChannel(
        token, pid, to, template=cfg.get("WHATSAPP_TEMPLATE") or None,
        lang=cfg.get("WHATSAPP_LANG") or "en_GB",
        api_base=cfg.get("WHATSAPP_API_BASE") or DEFAULT_API_BASE)
