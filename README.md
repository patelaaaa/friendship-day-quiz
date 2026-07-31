# Friendship Day Mega Quiz Event — Streamlit Edition

A free-to-host rebuild of the original single-page HTML event site. No domain,
no server, no service account. Two free pieces:

- **Streamlit Community Cloud** — hosts the app (`app.py`)
- **Google Sheets + Apps Script** — hosts the data and acts as the API
  (no Google Cloud service account / API key needed)

## What changed vs. the original site

- **Real shared backend.** The original stored everything in each visitor's
  browser `localStorage`, so nobody actually shared data — every phone saw
  its own private copy. Now every registration writes to one Google Sheet
  that everyone reads from.
- **Simplified visuals.** The glowing countdown bar, animated canvas wheel,
  paper-slip lucky-draw box, and confetti were rebuilt as clean, fast
  Streamlit widgets rather than custom HTML/CSS/JS, per your request. All the
  *functionality* (unique-ID-gated registration, duplicate checks, admin
  edit/delete, close registrations, lucky draw + history, CSV export) is
  preserved.
- **One draw mechanism.** The original had two separate lucky-draw flows
  (a spin-the-wheel with its own ID check, and a "paper slip" draw over
  registrations) both keyed off the same 70-ID list. These are merged into
  a single "Draw Winner" flow over registered teams, to avoid asking people
  to spend their one-time ID twice.

## 1. Create the Google Sheet backend

1. Create a new Google Sheet (any name, e.g. "Friendship Day Quiz — Data").
2. Open **Extensions → Apps Script**.
3. Delete the placeholder code and paste in the contents of
   `apps_script/Code.gs` from this repo.
4. In the function dropdown at the top, select **setup**, then click **Run**.
   - The first run will ask you to authorize the script — approve it (it's
     your own script acting on your own sheet).
   - This creates the `Registrations`, `UniqueIDs`, `Winners`, and `Settings`
     tabs, and seeds `UniqueIDs` with the 70 codes from
     `Friendship_Day_70_Unique_IDs.txt`.
5. Set your admin password:
   - **Project Settings** (gear icon) → **Script Properties** → **Add script property**
   - Property: `ADMIN_PASSWORD`, Value: choose a strong password (this
     replaces the old hardcoded `SANDYCHANGE28`).
6. Deploy as a web app:
   - **Deploy → New deployment → select type: Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy**, authorize again if asked, and **copy the Web app URL**
     (ends in `/exec`). You'll need it in step 3.
   - If you ever edit `Code.gs` again, use **Deploy → Manage deployments →
     Edit → New version** so the live URL picks up your changes.

Optional: change the event date/time by editing the `EventDateTime` row in
the `Settings` tab (ISO 8601 format, e.g. `2026-08-02T19:00:00+05:30`).

## 2. Push this project to GitHub

Push everything in this folder (`app.py`, `requirements.txt`,
`apps_script/Code.gs`, `.streamlit/secrets.toml.example`, `.gitignore`,
this `README.md`) to a new GitHub repo. **Do not** commit a real
`secrets.toml` — only the `.example` file.

## 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.
2. **New app** → pick your repo/branch → main file path: `app.py`.
3. Before or after deploying, open **Settings → Secrets** and paste:
   ```toml
   APPS_SCRIPT_URL = "https://script.google.com/macros/s/.../exec"
   ```
   (the URL you copied in step 1.6).
4. Deploy. That's the whole hosting bill: **$0**.

## How the admin panel works

- The password you set in `ADMIN_PASSWORD` (Script Properties) is the same
  one participants/organizers type into the Streamlit app's admin login box.
  It's checked live against the sheet, so you can change it anytime in Apps
  Script without redeploying Streamlit.
- Once unlocked, you can close/reopen registrations, edit or delete any
  entry, run the lucky draw, download CSVs, and clear winner history.

## Local development

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit secrets.toml with your real Apps Script URL
streamlit run app.py
```

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit front end |
| `apps_script/Code.gs` | Backend API bound to the Google Sheet (paste into Apps Script) |
| `requirements.txt` | Python dependencies for Streamlit Cloud |
| `.streamlit/secrets.toml.example` | Template for the one secret the app needs |
| `Friendship_Day_70_Unique_IDs.txt` | Reference copy of the 70 official unique IDs (already baked into `Code.gs`'s `setup()`) |
