from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import requests
from dateutil import tz
from flask import Flask, jsonify, request, send_from_directory
from icalendar import Calendar
import recurring_ical_events

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(ROOT_DIR), "frontend")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
SAMPLE_CONFIG_PATH = os.path.join(ROOT_DIR, "config.sample.json")

app = Flask(__name__, static_url_path="", static_folder=FRONTEND_DIR)

def load_config() -> Dict[str, Any]:
    path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else SAMPLE_CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _iso(dt):
    # Return ISO8601 with timezone if datetime; if date, return YYYY-MM-DD
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)

def _event_to_dict(component) -> Dict[str, Any]:
    """Convert an icalendar Event component to FullCalendar-like dict."""
    summary = str(component.get('SUMMARY', '')) if component.get('SUMMARY') else ""
    # DTSTART / DTEND may be date or datetime (with tzinfo)
    dtstart = component.get('DTSTART').dt if component.get('DTSTART') else None
    dtend = None
    if component.get('DTEND'):
        dtend = component.get('DTEND').dt
    elif component.get('DURATION') and dtstart:
        # If no DTEND, compute from DURATION
        dtend = dtstart + component.get('DURATION').dt
    elif dtstart:
        # No end given; assume 1-hour block if datetime, or next day if all-day date
        if hasattr(dtstart, "hour"):
            dtend = dtstart + timedelta(hours=1)
        else:
            dtend = dtstart

    # Normalize: ensure timezone-aware datetimes if possible
    def ensure_tz(d):
        if hasattr(d, "tzinfo") and d.tzinfo is None:
            return d.replace(tzinfo=timezone.utc)
        return d

    all_day = False
    if dtstart is not None and not hasattr(dtstart, "hour"):  # date object, not datetime
        all_day = True

    if not all_day:
        dtstart = ensure_tz(dtstart)
        dtend = ensure_tz(dtend)

    return {
        "title": summary,
        "start": _iso(dtstart),
        "end": _iso(dtend) if dtend else None,
        "allDay": all_day,
    }

@app.route("/")
def index():
    # Serve the frontend index
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/calendar.html")
def calendar_html():
    return send_from_directory(FRONTEND_DIR, "calendar.html")

@app.route("/manifest.json")
def manifest():
    return send_from_directory(FRONTEND_DIR, "manifest.json")

@app.route("/assets/<path:path>")
def assets_files(path):
    return send_from_directory(os.path.join(FRONTEND_DIR, "assets"), path)

@app.route("/sw.js")
def service_worker():
    return send_from_directory(FRONTEND_DIR, "sw.js")

@app.get("/api/people")
def api_people():
    cfg = load_config()
    people = [{"name": p["name"]} for p in cfg.get("people", [])]
    return jsonify({"people": people})

@app.get("/api/calendar/<name>")
def api_calendar(name: str):
    """Return events for a given person between start/end (YYYY-MM-DD)."""
    cfg = load_config()
    person = next((p for p in cfg.get("people", []) if p["name"].lower() == name.lower()), None)
    if not person:
        return jsonify({"error": f"Person {name} not found"}), 404

    ics_url = person.get("ics_url")
    if not ics_url:
        return jsonify({"error": "No ICS URL configured"}), 400

    # Parse range (FullCalendar passes ISO strings). Provide generous default window if missing.
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    try:
        if start_str:
            range_start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        else:
            range_start = datetime.now(timezone.utc) - timedelta(days=30)
        if end_str:
            range_end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        else:
            range_end = datetime.now(timezone.utc) + timedelta(days=120)
    except Exception:
        range_start = datetime.now(timezone.utc) - timedelta(days=30)
        range_end = datetime.now(timezone.utc) + timedelta(days=120)

    # Fetch ICS
    try:
        resp = requests.get(ics_url, timeout=15)
        resp.raise_for_status()
        ics_text = resp.text
    except Exception as e:
        return jsonify({"error": f"Failed to fetch ICS: {e}"}), 502

    try:
        cal = Calendar.from_ical(ics_text)
        # recurring_ical_events expands RRULEs across a given window
        components = recurring_ical_events.of(cal).between(range_start, range_end)
        events = [_event_to_dict(c) for c in components]
        # Optional: trim extremely long lists
        if len(events) > 1000:
            events = events[:1000]
        return jsonify({"events": events})
    except Exception as e:
        return jsonify({"error": f"Failed to parse ICS: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
