"""Run with: python -m streamlit run app.py"""

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from logic import (AGE_GROUPS, add_water, daily_records, ensure_day, export_csv,
                   format_water, habit_insights, milestone, new_state, pace_target,
                   progress, reminder_due, reset_today, schedule_alert, set_goal,
                   snooze_reminder, to_ml, undo_last)
from notifications import browser_alerts
from visuals import battery_svg, drop_icon, week_chart


st.set_page_config(page_title="WaterBuddy · Charge your body", page_icon="💧", layout="centered", initial_sidebar_state="collapsed")

TIMEZONES = ["Asia/Kolkata", "UTC", "Europe/London", "America/New_York",
             "America/Los_Angeles", "Australia/Sydney"]


def clock():
    zone = st.session_state.get("buddy", {}).get("settings", {}).get("timezone", "Asia/Kolkata")
    return datetime.now(ZoneInfo(zone))


if "buddy" not in st.session_state:
    st.session_state.buddy = new_state(clock())
    st.session_state.setup_step = 1
state = st.session_state.buddy


def water(amount):
    return format_water(amount, state["settings"].get("display_unit", "ml"))


def water_value(amount):
    unit = state["settings"].get("display_unit", "ml")
    if unit == "US fl oz":
        return f'{water(amount).removesuffix(" US fl oz")} <small>US fl oz</small>'
    return f'{amount:,} <small>ml</small>'


def html(markup):
    # st.html deliberately strips inline SVG in its HTML-only sanitizer.
    # Render our own trusted drawings through Markdown's HTML support instead.
    if "<svg" in markup:
        st.markdown(markup, unsafe_allow_html=True)
    else:
        st.html(markup)


def apply_style():
    dark = state["settings"]["theme"] == "Dark"
    colors = ({"page": "#0e1116", "card": "#151a21", "ink": "#e7edf5", "muted": "#98a5b6",
               "line": "#29313c", "soft": "#1b232d", "teal": "#8ac7ff", "cell": "#242e3b",
               "battery-bg": "#11171f", "battery-outline": "#52677e", "selected": "#283341",
               "primary": "#94ccff", "primary-text": "#0d2033"}
              if dark else
              {"page": "#f5f7fa", "card": "#ffffff", "ink": "#203044", "muted": "#5c6d80",
               "line": "#dbe2eb", "soft": "#ecf1f7", "teal": "#256ca7", "cell": "#e3ebf3",
               "battery-bg": "#f6f9fd", "battery-outline": "#8b9fb3", "selected": "#dde9f5",
               "primary": "#256ca7", "primary-text": "#ffffff"})
    variables = ";".join(f"--{key}:{value}" for key, value in colors.items())
    extra = ""
    if state["settings"]["large_text"]:
        extra += 'html {font-size:19px} .intro,.milestone,.log-row,.stat-label,.pace {font-size:16px} .small-note,.foot,.badge {font-size:13px}'
    if state["settings"]["reduce_motion"]:
        extra += '*,*::before,*::after {animation:none !important;transition:none !important} button:hover,button:active,label:active,summary:active {transform:none !important}'
    if dark:
        extra += '.stApp {color-scheme:dark}'
    css = Path(__file__).with_name("style.css").read_text(encoding="utf-8")
    html(f"<style>:root {{{variables}}} {css} {extra}</style>")


def header():
    html(f'<div class="brand-row"><div class="brand">{drop_icon()}<span>WaterBuddy</span></div><div class="small-note">DAILY HYDRATION</div></div>')


def footer():
    html('<div class="foot"><span>Session only · Export your log to keep a copy.</span><span>WaterBuddy</span></div>')


def about_sidebar():
    with st.sidebar:
        st.subheader("About this app")
        st.markdown("Created by **Aaryan Odedra**")
        st.caption("IBCP Year 1")
        st.caption("CRS AI · FA-2 Project")


def notify(message):
    st.session_state.notice = message


def log_water(amount):
    ensure_day(state, clock())
    st.session_state.battery_from = progress(state["entries"], state["goal"])["fill"]
    before = progress(state["entries"], state["goal"])
    celebrate = add_water(state, amount, clock())
    after = progress(state["entries"], state["goal"])
    if after["total"] > state["goal"] and before["total"] <= state["goal"]:
        notify(f"Congratulations! You’re {water(after['total']-state['goal'])} above your goal. Today’s target is complete.")
    elif celebrate:
        notify("Congratulations! You’ve reached your daily water goal.")
    else:
        notify(f"Added {water(amount)}.")


def undo():
    ensure_day(state, clock())
    st.session_state.battery_from = progress(state["entries"], state["goal"])["fill"]
    if undo_last(state):
        notify("Last entry removed.")


def reset():
    st.session_state.battery_from = progress(state["entries"], state["goal"])["fill"]
    reset_today(state, clock())
    st.session_state.confirm_reset = False
    notify("Today’s log is clear. Your goal and earlier days are still here.")


def setup():
    step = st.session_state.setup_step
    html(f'<div class="eyebrow">GET STARTED / 0{step}</div>')
    html('<div class="hero-title">Your daily hydration,<br>at a glance.</div><p class="intro">Set a goal. Log your water. Keep track.</p>')
    if step == 1:
        st.subheader("Pick your battery size")
        age = st.selectbox("Your age group", list(AGE_GROUPS), index=2, key="setup_age")
        st.caption(f"Starting goal: {AGE_GROUPS[age]['goal']:,} ml per day. You can adjust it next.")
        if st.button("Continue to my goal →", type="primary", use_container_width=True):
            st.session_state.chosen_age = age
            st.session_state.setup_goal = AGE_GROUPS[age]["goal"]
            st.session_state.setup_step = 2
            st.rerun()
    else:
        age = st.session_state.chosen_age
        st.subheader("Make the goal yours")
        st.caption(f"{age} · Starting goal: {AGE_GROUPS[age]['goal']:,} ml")
        goal = st.number_input("Daily goal (ml)", min_value=250, max_value=5000, step=50, key="setup_goal")
        html(f'<div class="goal-number">{goal:,} <small>ml / day</small></div><p class="intro">About {goal/250:g} cups of 250 ml.</p>')
        st.caption("Choose a personal daily target that suits you.")
        back, start = st.columns([1, 2])
        if back.button("← Back", use_container_width=True):
            st.session_state.setup_step = 1
            st.rerun()
        if start.button("Let’s start charging →", type="primary", use_container_width=True):
            set_goal(state, age, int(goal))
            state["reminder_anchor"] = clock().isoformat()
            st.rerun()


def stat_cards(p, goal):
    html(f'''<div class="stats">
    <div class="stat"><div class="stat-label">Water logged</div><div class="stat-value">{water_value(p['total'])}</div></div>
    <div class="stat"><div class="stat-label">Left to goal</div><div class="stat-value">{water_value(p['remaining'])}</div></div>
    <div class="stat"><div class="stat-label">Daily goal</div><div class="stat-value">{water_value(goal)}</div></div>
    </div>''')


def timeline(entries, goal, limit=None):
    if not entries:
        html('<div class="empty">Your next glass is a fresh start.<br>Water entries will appear here when you log them.</div>')
        return
    rows, running = [], 0
    for entry in entries:
        running += entry["amount"]
        time = datetime.fromisoformat(entry["time"]).strftime("%I:%M %p").lstrip("0")
        rows.append(f'<div class="log-row"><span class="log-dot"></span><span class="time">{time}</span><span class="amount">+{water(entry["amount"])}</span><span class="running">{water(running)} · {running/goal*100:.0f}%</span></div>')
    rows.reverse()
    if limit:
        rows = rows[:limit]
    html('<div class="timeline">'+''.join(rows)+'</div>')


def today():
    now = clock()
    p = progress(state["entries"], state["goal"])
    label, title, message = milestone(p["percent"])
    if p["total"] > state["goal"]:
        message = f"You’re {water(p['total']-state['goal'])} above your target. Today’s goal is complete."
    previous_fill = st.session_state.pop("battery_from", p["fill"])
    html(f'<div class="eyebrow">{now.strftime("%A, %d %B").upper()}</div>')
    st.title("Today’s hydration")
    html(f'''<div class="hero-card"><div class="card-top"><span class="card-title">Daily progress</span><span class="badge">{label}</span></div>
    <div class="battery-layout"><div class="charge-summary"><div class="charge-number">{p['percent']:.0f}<span>%</span></div><div class="charge-caption">of {water(state['goal'])}</div></div>
    <div class="battery-wrap">{battery_svg(p['fill'], previous_fill=previous_fill)}<div class="battery-ends"><span>EMPTY</span><span>FULL</span></div></div></div>
    <div class="milestone"><strong>{title}</strong> <span>{message}</span></div></div>''')
    stat_cards(p, state["goal"])
    html('<div class="section-heading"><h3>Add water</h3><span>Log what you’ve drunk</span></div>')
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.button(f"+ {water(250)} · one glass", type="primary", use_container_width=True, on_click=log_water, args=(250,))
    c2.button(f"+ {water(150)}", use_container_width=True, on_click=log_water, args=(150,))
    c3.button(f"+ {water(500)}", use_container_width=True, on_click=log_water, args=(500,))
    with st.expander("Add a custom amount"):
        unit = st.radio("Unit", ["Millilitres", "Cups (250 ml)", "US fl oz"], horizontal=True, key="custom_unit")
        with st.form("custom_water", clear_on_submit=False):
            if unit == "Millilitres":
                entered = st.number_input("Millilitres (ml)", 1, 1000, 300, 25, key="custom_ml")
            elif unit == "US fl oz":
                entered = st.number_input("US fluid ounces (fl oz)", 0.1, 33.8, 8.0, 0.5, key="custom_oz")
                st.caption("1 US fl oz ≈ 29.57 ml. Entries are stored to the nearest whole ml.")
            else:
                entered = st.number_input("Number of cups", 0.25, 4.0, 1.0, 0.25, key="custom_cups")
                st.caption("1 cup = 250 ml.")
            if st.form_submit_button("Add water", type="primary", use_container_width=True):
                try:
                    amount = to_ml(entered, unit)
                except ValueError as error:
                    st.error(str(error))
                else:
                    log_water(amount)
                    st.rerun()
    reminder_text = "Drink reminders · off"
    if state["settings"]["reminders"]:
        reminder_text = "Drink reminders · paused (goal reached)" if p["reached"] else f"Drink reminders · every {state['settings']['reminder_minutes']} min"
        if not p["reached"] and state.get("snooze_until"):
            reminder_text = f"Drink reminders · snoozed until {datetime.fromisoformat(state['snooze_until']).strftime('%I:%M %p').lstrip('0')}"
    st.caption(f"{reminder_text} · Configure or test in Settings.")
    if state["settings"]["pace"] and not p["reached"]:
        target = pace_target(now, state["goal"])
        html(f'<div class="pace">◷ Gentle pace guide: around {water(target)} by now, spread across 8 AM–8 PM. Go at your own pace.</div>')
    st.write("")
    html('<div class="section-heading"><h3>Recent refills</h3><span>Latest first</span></div>')
    timeline(state["entries"], state["goal"], limit=4)
    if len(state["entries"]) > 4:
        st.caption(f"Showing your latest 4 of {len(state['entries'])} refills. Open Battery report for all entries.")
    st.button("↶ Undo last entry", disabled=not state["entries"], on_click=undo)


def report():
    html('<div class="eyebrow">Every glass adds up</div>')
    st.title("Your battery report")
    st.caption("Your daily timeline and the last seven calendar days in this session.")
    records = daily_records(state)
    dates = sorted(records, reverse=True)
    day = st.selectbox("Choose a day", dates, format_func=lambda value: datetime.fromisoformat(value).strftime("%d %B %Y") + (" · Today" if value == state["day"] else ""))
    record = records[day]
    p = progress(record["entries"], record["goal"])
    stat_cards(p, record["goal"])
    st.progress(p["fill"], text=f"{p['percent']:.1f}% of goal · {p['cups']:g} cups logged (250 ml each)")
    a, b = st.columns([1.25, 1], gap="large")
    with a:
        st.subheader("Refill timeline")
        timeline(record["entries"], record["goal"])
    with b:
        st.subheader("Last 7 days")
        end = datetime.fromisoformat(state["day"]).date()
        days = [end - timedelta(days=i) for i in range(6, -1, -1)]
        html(week_chart(records, days))
        for d in days:
            r = records.get(d.isoformat())
            total = sum(e["amount"] for e in r["entries"]) if r else 0
            detail = f"{water(total)} / {water(r['goal'])}" if r else "No session record"
            st.caption(f"{d.strftime('%a %d %b')} · {detail}")
    st.write("")
    st.download_button("↓ Download water log (.csv)", export_csv(state), file_name=f"waterbuddy-{state['day']}.csv", mime="text/csv", use_container_width=True)
    st.caption("Includes all logged days in this session. Download before refreshing or closing the app.")


def insights():
    html('<div class="eyebrow">YOUR HABITS, AT A GLANCE</div>')
    st.title("Habit insights")
    st.caption("Your streak and personal best from the days recorded in this session.")
    info = habit_insights(state)
    html(f'''<div class="stats insight-stats">
    <div class="stat"><div class="stat-label">Current goal streak</div><div class="stat-value">{info['current_streak']} <small>{'day' if info['current_streak'] == 1 else 'days'}</small></div></div>
    <div class="stat"><div class="stat-label">Personal best streak</div><div class="stat-value">{info['best_streak']} <small>{'day' if info['best_streak'] == 1 else 'days'}</small></div></div>
    <div class="stat"><div class="stat-label">Goals completed</div><div class="stat-value">{info['goals_met']} <small>{'day' if info['goals_met'] == 1 else 'days'}</small></div></div></div>''')
    if info["current_streak"]:
        st.success(f"Nice consistency! Your goal streak is {info['current_streak']} day{'s' if info['current_streak'] != 1 else ''}.")
    else:
        st.info("Reach your daily goal to start a streak. Completing a goal counts once per day.")
    st.subheader("Your refill rhythm today")
    a, b = st.columns(2)
    a.metric("Refills logged", info["refills"])
    b.metric("Average refill", water(info["average_refill"]))
    total = sum(info["periods"].values())
    for period, amount in info["periods"].items():
        st.progress(amount / total if total else 0, text=f"{period} · {water(amount)}")
    st.caption("Morning 5 AM–noon · Afternoon noon–5 PM · Evening 5–10 PM · Night 10 PM–5 AM. Uses the local time recorded with each refill.")
    st.caption("Streaks reward completing your goal; extra water does not add extra days. An unfinished today keeps yesterday’s streak active until midnight. Export your log before closing this session.")


def test_alert():
    schedule_alert(state, clock(), test=True)
    notify("Test reminder: your water notifications are working.")


def dismiss_alert():
    state["reminder_pending"] = None
    state["browser_event"] = None


def snooze():
    snooze_reminder(state, clock())
    notify("Reminder snoozed for 10 minutes.")


def reminder_settings():
    st.subheader("Drink reminders")
    current = state["settings"]
    with st.form("reminder_settings"):
        enabled = st.toggle("Remind me to drink water", value=current["reminders"], key="enable_reminders")
        options = [15, 30, 45, 60, 90, 120]
        minutes = st.selectbox("Time between reminders", options, index=options.index(current["reminder_minutes"]), format_func=lambda m: f"{m} minutes", key="reminder_interval")
        st.caption("From 8 AM–8 PM in your timezone, while this app is open. Logging water restarts the timer; reaching your goal stops reminders.")
        if st.form_submit_button("Save reminders", type="primary"):
            current.update(reminders=enabled, reminder_minutes=minutes)
            state["reminder_anchor"] = clock().isoformat()
            state["reminder_pending"] = None
            state["snooze_until"] = None
            state["browser_event"] = None
            notify("Drink reminders enabled." if enabled else "Drink reminders paused.")
            st.rerun()
    st.button("Test notification", on_click=test_alert)
    browser_alerts(controls=True, enabled=current["reminders"], key="browser_alert_controls")
    st.caption("Browser alerts are optional. Click Allow browser alerts, then allow this site in your browser. If unavailable, in-app notifications still work. Closing the app stops both.")


def settings():
    html('<div class="eyebrow">Make it feel like you</div>')
    st.title("Your preferences")
    reminder_settings()
    st.subheader("Battery size & daily goal")
    if st.session_state.pop("sync_goal", False) or "edit_goal" not in st.session_state:
        st.session_state.edit_goal = state["goal"]
    with st.form("profile"):
        age = st.selectbox("Age group", list(AGE_GROUPS), index=list(AGE_GROUPS).index(state["age_group"]), key="edit_age")
        st.caption("Starting goals: Mini Cell 1,200 · Standard 1,700 · Max 2,200 · Eco 1,800 ml.")
        use_preset = st.checkbox("Use the selected age group’s preset", value=False)
        goal = st.number_input("Your daily goal (ml)", 250, 5000, step=50, key="edit_goal")
        st.caption("Choose the preset above to replace the number with your age group’s starting goal. Today’s refills stay in your log.")
        if st.form_submit_button("Save daily goal", type="primary"):
            st.session_state.battery_from = progress(state["entries"], state["goal"])["fill"]
            set_goal(state, age, AGE_GROUPS[age]["goal"] if use_preset else int(goal))
            st.session_state.sync_goal = True
            notify("Your daily goal is updated.")
            st.rerun()
    st.subheader("Comfort & accessibility")
    current = state["settings"]
    with st.form("preferences"):
        theme = st.radio("Appearance", ["Light", "Dark"], index=int(current["theme"] == "Dark"), horizontal=True)
        big = st.toggle("Larger text", value=current["large_text"])
        reduced = st.toggle("Reduce motion", value=current["reduce_motion"])
        pace = st.toggle("Show gentle pace guide", value=current["pace"])
        unit_options = ["ml", "US fl oz"]
        display_unit = st.selectbox("Display water amounts in", unit_options, index=unit_options.index(current.get("display_unit", "ml")), key="display_unit")
        zone = st.selectbox("Your timezone", TIMEZONES, index=TIMEZONES.index(current["timezone"]))
        st.caption("Daily goals are set in ml. US fluid ounces are shown to two decimals. Changing timezone can start a new calendar day.")
        if st.form_submit_button("Save preferences", type="primary"):
            current.update(theme=theme, large_text=big, reduce_motion=reduced, pace=pace,
                           display_unit=display_unit, timezone=zone)
            notify("Preferences saved.")
            st.rerun()
    st.subheader("Start fresh")
    st.caption("A new calendar day starts automatically at midnight in your selected timezone. You can also clear today’s entries here.")
    if st.button("Reset today’s water log", disabled=not state["entries"]):
        st.session_state.confirm_reset = True
    if st.session_state.get("confirm_reset"):
        st.warning("Clear all of today’s refills? Your daily goal and previous days will stay. Download your report first if you need a copy.")
        yes, no = st.columns(2)
        yes.button("Yes, clear today", on_click=reset, use_container_width=True)
        if no.button("Keep my entries", use_container_width=True):
            st.session_state.confirm_reset = False
            st.rerun()
    with st.expander("About your data & this project"):
        st.write("WaterBuddy is a Python / Streamlit student project based on your FA-1 storyboard. The four age presets are examples from that design, not individual medical advice.")
        st.write("Your logs and preferences are held in your Streamlit session. There is no account, database, or shared log. Refreshing, reconnecting, a server restart, or closing the session may clear your data. Use the CSV download to keep a copy.")
        st.write("One cup is 250 ml. One US fluid ounce is approximately 29.57 ml. CSV exports always use ml. The optional pace guide divides your goal between 8 AM and 8 PM.")


@st.fragment(run_every="30s")
def session_clock():
    # Timer reruns never log water. They only roll the date or show a reminder.
    now = clock()
    if ensure_day(state, now):
        st.session_state.confirm_reset = False
        notify("A new day, a fresh battery. Yesterday’s report is still available.")
        st.rerun()
    if reminder_due(state, now):
        schedule_alert(state, now)
        st.toast("Time for water. Take a moment for a drink.", icon="💧")
    pending = state.get("reminder_pending")
    if pending:
        if pending["test"]:
            st.info("Test reminder · This is how your water reminder appears.")
            if st.button("Dismiss test reminder", key="dismiss_test"):
                dismiss_alert()
                st.rerun()
        else:
            st.info("Time for water · Take a moment for a drink, then log your refill.")
            a, b, c = st.columns(3)
            if a.button(f"Log {water(250)}", key="reminder_log", use_container_width=True):
                log_water(250)
                st.rerun()
            if b.button("Snooze 10 min", key="snooze", use_container_width=True):
                snooze()
                st.rerun()
            if c.button("Dismiss", key="dismiss", use_container_width=True):
                dismiss_alert()
                st.rerun()
    browser_alerts(event=state.get("browser_event"))


if ensure_day(state, clock()):
    st.session_state.confirm_reset = False
    notify("A new day, a fresh battery. Yesterday’s report is still available.")
apply_style()
about_sidebar()
header()
if state["age_group"] is None:
    setup()
else:
    if st.session_state.get("notice"):
        st.toast(st.session_state.pop("notice"), icon="💧")
    view = st.radio("Navigation", ["Today", "Insights", "Battery report", "Settings"], horizontal=True,
                    label_visibility="collapsed", key="navigation")
    session_clock()
    {"Today": today, "Insights": insights, "Battery report": report, "Settings": settings}[view]()
footer()
