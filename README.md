# Family Calendar (Free Web App)

This is a minimal, **100% free** full‑stack app (Flask + vanilla JS + FullCalendar) that
lets you view friends’/family members’ iCloud shared calendars (.ics) in one place.
It works great on iPhone as a PWA (Add to Home Screen).

## How it works
- Each person shares an **iCloud public calendar** link (.ics) with you.
- The backend fetches & parses the .ics and expands recurring events.
- The frontend renders events with FullCalendar.
- No App Store, no Apple Developer fees.

## Quick start (local)
1. Install Python 3.11+
2. In a terminal:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp config.sample.json config.json
   # Edit config.json and put real iCloud .ics URLs
   python app.py
   ```
3. Open http://localhost:5000 in your browser.
4. On iPhone Safari: Share → Add to Home Screen (PWA install).

## Deploy (free)
- **Render** (free): create a new web service, connect this repo, set build command to:
  ```
  pip install -r backend/requirements.txt
  ```
  and start command:
  ```
  gunicorn app:app --chdir backend --bind 0.0.0.0:$PORT
  ```
  Make sure `backend/config.json` is added through a Render **private file** or **environment variable** + mounted file.

- **Netlify/Vercel (frontend only)**: If you split frontend hosting, set the backend origin in the JS fetch URLs.

## Configure people (backend/config.json)
```json
{
  "people": [
    {"name": "Lilly", "ics_url": "https://example.com/lilly.ics"},
    {"name": "Mom", "ics_url": "https://example.com/mom.ics"}
  ]
}
```
> Do **NOT** commit real .ics URLs to a public repo. Treat them as secrets.

## iCloud: get a public .ics link
- iPhone Calendar → Calendars → tap (i) next to a calendar → toggle **Public Calendar** → **Share Link**.
- Or on iCloud.com → Calendar → (icon) share → **Public Calendar** → copy the URL.
> Best practice: have family create a separate calendar for “shareable” events to avoid exposing private details.

## Notes
- Timezones: The backend tries to preserve ICS-provided timezones. All‑day events are handled as allDay.
- Recurring events: Expanded over the requested range using `recurring-ical-events`.
- Privacy: public .ics links can be accessed by anyone who has the URL. Share them carefully.
- Scaling: fine for <20 users on free tiers.

## License
MIT (for this template). FullCalendar is loaded from CDN under its license.
