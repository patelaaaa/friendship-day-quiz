import random
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Friendship Day Mega Quiz Event", page_icon="🎉", layout="wide")

# ---------------------------------------------------------------------------
# Theming — navy & gold, echoing the original site's look, applied on top of
# plain Streamlit widgets so nothing about the functionality changes.
# ---------------------------------------------------------------------------
st.html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
--navy:#06111f; --navy-2:#0e2238; --gold:#e8b85d; --gold-light:#ffd98a;
--cream:#fff8e9; --text:#edf3f8; --muted:#aab9c8; --line:rgba(232,184,93,.35);
}
html, body, [class*="css"]{ font-family:'Inter',system-ui,sans-serif; }
.stApp{
background:
radial-gradient(circle at 15% 0%, rgba(232,184,93,.10), transparent 40rem),
radial-gradient(circle at 85% 15%, rgba(232,184,93,.06), transparent 35rem),
linear-gradient(180deg,#040b14,#071526 40%,#04101d);
}

/* Hero */
.fd-hero{ text-align:center; padding:1.6rem 0 0.4rem 0; }
.fd-hero h1{
font-family:'Cinzel',serif; font-weight:700; letter-spacing:.03em;
font-size:2.6rem; margin-bottom:0.2rem;
background:linear-gradient(180deg,var(--gold-light),var(--gold));
-webkit-background-clip:text; background-clip:text; color:transparent;
text-shadow:0 2px 24px rgba(232,184,93,.25);
}
.fd-hero p{ color:var(--muted); font-size:1.02rem; letter-spacing:.04em; text-transform:uppercase; margin-top:0; }
.fd-rule{ height:1px; margin:0.6rem auto 1.6rem auto; max-width:420px;
background:linear-gradient(90deg,transparent,var(--gold),transparent); }

/* Section headers */
h2{ font-family:'Cinzel',serif !important; color:var(--gold-light) !important;
letter-spacing:.02em; border-bottom:1px solid var(--line); padding-bottom:.5rem; }
h3{ color:var(--gold-light) !important; }

/* Countdown metrics */
div[data-testid="stMetric"]{
background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
border:1px solid var(--line); border-radius:14px; padding:10px 6px; text-align:center;
}
div[data-testid="stMetricValue"]{ color:var(--gold-light) !important; font-family:'Cinzel',serif; }
div[data-testid="stMetricLabel"]{ color:var(--muted) !important; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }

/* Cards: forms + expanders */
div[data-testid="stForm"], details{
background:var(--navy-2) !important; border:1px solid var(--line) !important;
border-radius:16px !important; padding:1.2rem !important;
}
details summary{ color:var(--gold-light) !important; font-weight:600; }

/* Buttons */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button{
border-radius:10px !important; border:1px solid var(--gold) !important;
background:linear-gradient(180deg,var(--gold-light),var(--gold)) !important;
color:#1a1204 !important; font-weight:700 !important; transition:all .15s ease;
}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover{
box-shadow:0 0 18px rgba(232,184,93,.45); transform:translateY(-1px);
}

/* Tables */
div[data-testid="stDataFrame"]{ border:1px solid var(--line); border-radius:12px; overflow:hidden; }

/* Dividers */
hr{ border-color:var(--line) !important; margin:2rem 0 !important; }

/* Captions */
.stCaption, [data-testid="stCaptionContainer"]{ color:var(--muted) !important; }
</style>
""")

APPS_SCRIPT_URL = st.secrets.get("APPS_SCRIPT_URL", "")

if not APPS_SCRIPT_URL:
    st.error(
        "APPS_SCRIPT_URL is not configured.\n\n"
        "Add it to `.streamlit/secrets.toml` locally, or to your app's Secrets "
        "in Streamlit Community Cloud. See README.md for setup steps."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Backend helpers (talks to the Google Apps Script web app)
# ---------------------------------------------------------------------------

def api_get(action: str, **params):
    params["action"] = action
    r = requests.get(APPS_SCRIPT_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def api_post(action: str, **payload):
    payload["action"] = action
    r = requests.post(APPS_SCRIPT_URL, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=15, show_spinner=False)
def load_all():
    return api_get("list_all")


def refresh():
    load_all.clear()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

st.session_state.setdefault("admin", False)
st.session_state.setdefault("admin_password", "")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

st.html("""
<div class="fd-hero">
<h1>🎉 Friendship Day Mega Quiz Event</h1>
<p>Team Registration &amp; Lucky Draw</p>
</div>
<div class="fd-rule"></div>
""")

data = load_all()
if not data.get("ok"):
    st.error(f"Could not load data from the backend: {data.get('error', 'unknown error')}")
    st.stop()

registrations = data["registrations"]
winners = data["winners"]
settings = data["settings"]
closed = str(settings.get("RegistrationClosed", "FALSE")).upper() == "TRUE"

# ---------------------------------------------------------------------------
# Countdown
# ---------------------------------------------------------------------------

try:
    event_dt = datetime.fromisoformat(settings.get("EventDateTime", "2026-08-02T19:00:00+05:30"))
except ValueError:
    event_dt = datetime(2026, 8, 2, 19, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))

now = datetime.now(event_dt.tzinfo)
diff = event_dt - now

if diff.total_seconds() <= 0:
    st.success("🎊 The event has started — enjoy the celebration!")
else:
    days = diff.days
    hrs, rem = divmod(diff.seconds, 3600)
    mins, secs = divmod(rem, 60)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✨ Days", days)
    c2.metric("⏳ Hours", hrs)
    c3.metric("⏱️ Minutes", mins)
    c4.metric("⚡ Seconds", secs)
    st.caption("Countdown updates each time the page reloads or you interact with it.")

st.caption(f"📅 Event: {event_dt.strftime('%d %B %Y, %I:%M %p')} (event timezone)")

st.divider()

# ---------------------------------------------------------------------------
# Registration form
# ---------------------------------------------------------------------------

st.header("📝 Team Registration")

if closed:
    st.warning("Registrations are closed. No new entries can be submitted.")
else:
    with st.form("registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Your Name", max_chars=40)
        starmaker_id = col2.text_input("StarMaker ID", max_chars=40)
        team_member = col1.text_input("Teammate's Name", max_chars=40)
        unique_id = col2.text_input(
            "Registration Unique ID",
            max_chars=20,
            placeholder="FDQ-XXX-XXXX",
            help="One-time unique ID given to you by the organizer.",
        )
        submitted = st.form_submit_button("Submit Registration", use_container_width=True)

        if submitted:
            if not (name and starmaker_id and team_member and unique_id):
                st.error("Please complete all fields, including the unique ID.")
            else:
                res = api_post(
                    "register",
                    name=name.strip(),
                    starmakerId=starmaker_id.strip(),
                    teamMember=team_member.strip(),
                    uniqueId=unique_id.strip().upper(),
                )
                if res.get("ok"):
                    st.success("✓ Registration submitted and added to the Lucky Draw!")
                    st.balloons()
                    refresh()
                    st.rerun()
                else:
                    st.error(res.get("error", "Registration failed. Please try again."))

st.divider()

# ---------------------------------------------------------------------------
# Public registrations table
# ---------------------------------------------------------------------------

st.header("👥 Registered Teams")
st.caption(f"{len(registrations)} team(s) registered so far")

if registrations:
    df_public = pd.DataFrame(registrations)[["name", "starmakerId", "teamMember"]]
    df_public.columns = ["Name", "StarMaker ID", "Teammate"]
    df_public.index = range(1, len(df_public) + 1)
    st.dataframe(df_public, use_container_width=True)
else:
    st.info("No registrations yet. Be the first team to join!")

st.divider()

# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

st.header("🔐 Admin Panel")

if not st.session_state.admin:
    with st.form("admin_login"):
        pwd_input = st.text_input("Lucky Draw & Registration Management Password", type="password")
        login = st.form_submit_button("Unlock Admin Controls")
        if login:
            check = api_get("check_admin", password=pwd_input)
            if check.get("ok"):
                st.session_state.admin = True
                st.session_state.admin_password = pwd_input
                st.rerun()
            else:
                st.error("Invalid management password.")
else:
    pwd = st.session_state.admin_password
    st.success("Admin controls unlocked.")

    colA, colB = st.columns([3, 1])
    with colA:
        new_state = st.toggle("Registrations Closed", value=closed)
        if new_state != closed:
            res = api_post("toggle_closed", adminPassword=pwd, closed=new_state)
            if res.get("ok"):
                refresh()
                st.rerun()
            else:
                st.error(res.get("error"))
    with colB:
        if st.button("Log Out"):
            st.session_state.admin = False
            st.session_state.admin_password = ""
            st.rerun()

    # --- Manage registrations ---
    st.subheader("Manage Registrations")
    if registrations:
        for entry in registrations:
            label = f"{entry['name']} & {entry['teamMember']} — {entry['starmakerId']} ({entry['uniqueId']})"
            with st.expander(label):
                with st.form(f"edit_{entry['entryId']}"):
                    e_name = st.text_input("Name", value=entry["name"], key=f"n_{entry['entryId']}")
                    e_sid = st.text_input("StarMaker ID", value=entry["starmakerId"], key=f"s_{entry['entryId']}")
                    e_team = st.text_input("Teammate", value=entry["teamMember"], key=f"t_{entry['entryId']}")
                    save_col, del_col = st.columns(2)
                    save = save_col.form_submit_button("Save Changes")
                    delete = del_col.form_submit_button("🗑️ Delete Entry")

                    if save:
                        res = api_post(
                            "edit_entry", adminPassword=pwd, entryId=entry["entryId"],
                            name=e_name, starmakerId=e_sid, teamMember=e_team,
                        )
                        if res.get("ok"):
                            st.success("Updated.")
                            refresh()
                            st.rerun()
                        else:
                            st.error(res.get("error"))

                    if delete:
                        res = api_post("delete_entry", adminPassword=pwd, entryId=entry["entryId"])
                        if res.get("ok"):
                            st.success("Deleted.")
                            refresh()
                            st.rerun()
                        else:
                            st.error(res.get("error"))
    else:
        st.info("No registrations to manage.")

    if registrations:
        st.download_button(
            "⬇️ Download Registrations CSV",
            data=pd.DataFrame(registrations).to_csv(index=False),
            file_name="registrations.csv",
            mime="text/csv",
        )

    # --- Lucky draw ---
    st.subheader("🎁 Lucky Draw")
    if st.button("Draw Winner", type="primary", disabled=not registrations):
        winner = random.choice(registrations)
        res = api_post(
            "record_winner",
            adminPassword=pwd,
            winnerName=f"{winner['name']} & {winner['teamMember']}",
            starmakerId=winner["starmakerId"],
            teamMember=winner["teamMember"],
        )
        if res.get("ok"):
            st.success(f"🎉 Winner: {winner['name']} & {winner['teamMember']} ({winner['starmakerId']})")
            st.balloons()
            refresh()
            st.rerun()
        else:
            st.error(res.get("error"))

    st.subheader("Winner History")
    if winners:
        df_w = pd.DataFrame(winners)
        df_w.columns = ["Winner", "StarMaker ID", "Teammate", "Drawn At"]
        st.dataframe(df_w, use_container_width=True)
        dl_col, clr_col = st.columns(2)
        dl_col.download_button(
            "⬇️ Download Winners CSV", data=df_w.to_csv(index=False),
            file_name="winners.csv", mime="text/csv",
        )
        if clr_col.button("Clear Winner History"):
            res = api_post("clear_winners", adminPassword=pwd)
            if res.get("ok"):
                refresh()
                st.rerun()
            else:
                st.error(res.get("error"))
    else:
        st.info("No winners drawn yet.")

st.divider()
st.caption("Friendship Day Mega Quiz Event • Thank you for celebrating friendship with us 💛")
