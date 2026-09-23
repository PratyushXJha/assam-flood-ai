"""Throttled SMS + AI voice-call alert dispatcher.

Messages are queued and released at a low, steady rate per channel (token spacing)
instead of in one burst, so carriers do not rate-limit or block the sender and every
recipient actually gets the alert. Failed sends are retried with backoff.

With Twilio credentials in the environment, recipients whose phone number starts
with '+' get real SMS / calls. Everything else is simulated (dry run) and logged.
"""
import asyncio
import csv
import itertools
import os
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional
from xml.sax.saxutils import escape

from app import config
from app.scenarios.dataset_loader import DATA_DIR

RECIPIENTS_PATH = os.path.join(DATA_DIR, "recipients.csv")
LANG_ROTATION = ("assamese", "hindi", "english")
DEMO_RECIPIENTS_PER_VILLAGE = 4


class RateLimitedError(Exception):
    pass


class SimulatedProvider:
    name = "simulated"

    def __init__(self):
        self._ids = itertools.count(1)

    def send_sms(self, to: str, body: str) -> str:
        return f"SIM-SMS-{next(self._ids):05d}"

    def place_call(self, to: str, script: str, language: str) -> str:
        return f"SIM-CALL-{next(self._ids):05d}"


class TwilioProvider:
    name = "twilio"

    def __init__(self, sid: str, token: str, from_number: str):
        self.sid, self.token, self.from_number = sid, token, from_number
        self.base = f"https://api.twilio.com/2010-04-01/Accounts/{sid}"

    def _post(self, path: str, data: Dict[str, str]) -> str:
        import requests
        res = requests.post(f"{self.base}/{path}", data=data, auth=(self.sid, self.token), timeout=15)
        if res.status_code == 429:
            raise RateLimitedError("Carrier/provider rate limit (HTTP 429)")
        if res.status_code >= 400:
            raise RuntimeError(f"Twilio HTTP {res.status_code}: {res.text[:200]}")
        return res.json().get("sid", "")

    def send_sms(self, to: str, body: str) -> str:
        return self._post("Messages.json", {"To": to, "From": self.from_number, "Body": body})

    def place_call(self, to: str, script: str, language: str) -> str:
        loc = config.VOICE_LOCALES.get(language, config.VOICE_LOCALES["english"])
        say = f'<Say voice="{loc["twilio_voice"]}" language="{loc["twilio_language"]}">{escape(script)}</Say>'
        twiml = f"<Response>{say}<Pause length=\"1\"/>{say}</Response>"  # message is read twice
        return self._post("Calls.json", {"To": to, "From": self.from_number, "Twiml": twiml})


def load_recipients(village_ids: List[str]) -> List[Dict[str, str]]:
    """Recipients from data/recipients.csv (phone,village_id,language) or demo placeholders."""
    if os.path.exists(RECIPIENTS_PATH):
        with open(RECIPIENTS_PATH, encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("village_id") in village_ids]
        return [{"phone": r["phone"].strip(), "village_id": r["village_id"], "language": r.get("language") or "assamese"} for r in rows]
    return [
        {"phone": f"DEMO-{vid[4:]}-{n + 1}", "village_id": vid, "language": LANG_ROTATION[n % 3]}
        for vid in village_ids
        for n in range(DEMO_RECIPIENTS_PER_VILLAGE)
    ]


class AlertDispatcher:
    def __init__(self):
        self.settings = dict(config.DISPATCH_DEFAULTS)
        self.simulator = SimulatedProvider()
        self.live_provider: Optional[TwilioProvider] = None
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_FROM_NUMBER:
            self.live_provider = TwilioProvider(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN, config.TWILIO_FROM_NUMBER)
        self.queues: Dict[str, Deque[Dict[str, Any]]] = {"sms": deque(), "voice": deque()}
        self.jobs: Dict[int, Dict[str, Any]] = {}
        self.feed: List[Dict[str, Any]] = []
        self._job_ids = itertools.count(1)
        self._batch_ids = itertools.count(1)
        self._feed_ids = itertools.count(1)
        self._tasks: List[asyncio.Task] = []

    # ---------- settings ----------
    def interval_seconds(self, channel: str) -> float:
        per_min = self.settings["sms_per_minute" if channel == "sms" else "calls_per_minute"]
        return 60.0 / max(0.1, per_min)

    def update_settings(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        bounds = {"sms_per_minute": (1, 120), "calls_per_minute": (1, 30), "max_retries": (0, 10), "retry_backoff_seconds": (1, 600)}
        for key, (lo, hi) in bounds.items():
            if key in updates and updates[key] is not None:
                val = min(hi, max(lo, float(updates[key])))
                self.settings[key] = int(val) if key == "max_retries" else val
        return self.public_settings()

    def public_settings(self) -> Dict[str, Any]:
        return {**self.settings, "provider": self.live_provider.name if self.live_provider else "simulated (dry run)"}

    # ---------- enqueue ----------
    def enqueue_alerts(self, alert_packages: List[Dict[str, Any]], channels: List[str], zone: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        batch_id = next(self._batch_ids)
        by_village = {a["village_id"]: a for a in alert_packages}
        recipients = load_recipients(list(by_village))
        now = time.time()
        counts = {"sms": 0, "voice": 0}

        for rcpt in recipients:
            pkg = by_village[rcpt["village_id"]]
            lang = rcpt["language"] if rcpt["language"] in pkg["languages"] else "english"
            texts = pkg["languages"][lang]
            for channel in channels:
                if channel == "voice" and not pkg["is_critical"]:
                    continue  # AI calls only for red-zone / critical alerts
                if channel not in self.queues:
                    continue
                job = {
                    "job_id": next(self._job_ids), "batch_id": batch_id, "channel": channel,
                    "to": rcpt["phone"], "village_id": pkg["village_id"], "village_name": pkg["village_name"],
                    "language": lang, "body": texts["sms_body"] if channel == "sms" else texts["voice_script"],
                    "attempts": 0, "status": "queued", "not_before": now, "created_at": now,
                    "sent_at": None, "provider_ref": None, "error": None,
                }
                self.jobs[job["job_id"]] = job
                self.queues[channel].append(job)
                counts[channel] += 1

        for pkg in alert_packages:
            self.feed.append({
                "event_id": next(self._feed_ids), "batch_id": batch_id, "created_at": now,
                "village_id": pkg["village_id"], "village_name": pkg["village_name"], "district": pkg["district"],
                "is_critical": pkg["is_critical"], "zone_id": zone["zone_id"] if zone else None,
                "zone_name": zone["name"] if zone else None,
                "messages": {k: {"sms": v["sms_body"], "voice": v["voice_script"], "locale": v["voice_locale"]} for k, v in pkg["languages"].items()},
            })
        self.feed = self.feed[-200:]

        return {
            "batch_id": batch_id, "villages": len(alert_packages), "recipients": len(recipients),
            "queued": counts,
            "eta_seconds": {ch: round(len(self.queues[ch]) * self.interval_seconds(ch)) for ch in self.queues},
        }

    # ---------- sending ----------
    def _provider_for(self, job: Dict[str, Any]):
        return self.live_provider if (self.live_provider and job["to"].startswith("+")) else self.simulator

    def _pop_ready(self, channel: str) -> Optional[Dict[str, Any]]:
        q, now = self.queues[channel], time.time()
        for _ in range(len(q)):
            job = q.popleft()
            if job["not_before"] <= now:
                return job
            q.append(job)
        return None

    def send_one(self, job: Dict[str, Any]) -> None:
        job["attempts"] += 1
        provider = self._provider_for(job)
        try:
            if job["channel"] == "sms":
                job["provider_ref"] = provider.send_sms(job["to"], job["body"])
            else:
                job["provider_ref"] = provider.place_call(job["to"], job["body"], job["language"])
            job["status"], job["sent_at"], job["error"] = "sent", time.time(), None
        except Exception as exc:  # noqa: BLE001 - any provider failure is retried
            job["error"] = str(exc)
            if job["attempts"] <= self.settings["max_retries"]:
                backoff = self.settings["retry_backoff_seconds"] * (2 ** (job["attempts"] - 1))
                if isinstance(exc, RateLimitedError):
                    backoff *= 2
                job["status"], job["not_before"] = "retrying", time.time() + backoff
                self.queues[job["channel"]].append(job)
            else:
                job["status"] = "failed"

    def drain(self, channel: str, limit: int = 1000) -> int:
        """Send ready jobs immediately, ignoring the rate limit (used by tests / admin flush)."""
        sent = 0
        while sent < limit:
            job = self._pop_ready(channel)
            if not job:
                break
            self.send_one(job)
            sent += 1
        return sent

    async def _worker(self, channel: str) -> None:
        while True:
            job = self._pop_ready(channel)
            if job is None:
                await asyncio.sleep(0.5)
                continue
            await asyncio.to_thread(self.send_one, job)
            await asyncio.sleep(self.interval_seconds(channel))

    def start(self) -> None:
        if self._tasks:
            return
        loop = asyncio.get_running_loop()
        self._tasks = [loop.create_task(self._worker(ch)) for ch in self.queues]

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        self._tasks = []

    # ---------- reporting ----------
    def status(self) -> Dict[str, Any]:
        summary = {}
        for ch in self.queues:
            jobs = [j for j in self.jobs.values() if j["channel"] == ch]
            summary[ch] = {s: sum(1 for j in jobs if j["status"] == s) for s in ("queued", "retrying", "sent", "failed")}
            summary[ch]["pending"] = len(self.queues[ch])
            summary[ch]["interval_seconds"] = round(self.interval_seconds(ch), 2)
            summary[ch]["eta_seconds"] = round(len(self.queues[ch]) * self.interval_seconds(ch))
        recent = sorted(self.jobs.values(), key=lambda j: (j["sent_at"] or 0, j["job_id"]), reverse=True)[:25]
        return {
            "settings": self.public_settings(),
            "channels": summary,
            "worker_running": bool(self._tasks),
            "recent": [{k: j[k] for k in ("job_id", "batch_id", "channel", "to", "village_name", "language", "status", "attempts", "provider_ref", "error", "sent_at")} for j in recent],
        }

    def feed_since(self, since_id: int, village_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return [e for e in self.feed if e["event_id"] > since_id and (not village_id or e["village_id"] == village_id)]

    def reset(self) -> None:
        for q in self.queues.values():
            q.clear()
        self.jobs.clear()


dispatcher = AlertDispatcher()
