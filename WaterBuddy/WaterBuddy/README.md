# WaterBuddy

A Python / Streamlit hydration app based on the WaterBuddy FA-1 storyboard and the FA-2 assignment brief.

## Run on this Windows computer

1. Open this folder in File Explorer.
2. Double-click **Start WaterBuddy.cmd**.
3. Open **http://localhost:8501** if the browser does not open automatically.
4. Keep the terminal window open while you use the app. Press **Ctrl+C** there to stop it.

The launcher can reuse the Python environment prepared with this project in Codex. On another computer, install Python 3.12 or newer from [python.org](https://www.python.org/downloads/) first. The launcher will create a `.venv` folder and install the packages on its first run. The first installation needs internet access. After that, the app runs locally without an internet connection.

If WaterBuddy is already running on port 8501, open the existing browser page. To run a second copy manually, add `--server.port 8502` to the command below and visit that port.

## Run manually in VS Code or a terminal

Open a terminal **inside this WaterBuddy folder**, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Run through Streamlit, rather than running `app.py` directly. No database, account, API key, image download, or Turtle/Tkinter installation is needed.

## What is included

- Two-step setup: choose an age group, then confirm or adjust the goal.
- Minimal charcoal interface, with dark appearance selected by default.
- Eight-cell water battery with partially filled cells, a short refill transition, and a muted green full-charge state.
- Subtle button press, hover, tab selection, expander, and input focus feedback; no mascot or celebration balloons.
- Milestone encouragement, congratulations at the goal, and a separate message showing the amount above your goal.
- Quick `+250 ml`, `+150 ml`, and `+500 ml` buttons.
- Custom logging in millilitres, cups, or **US fluid ounces**; one project cup is 250 ml. Ounce entries are converted once to the nearest whole ml.
- Switch the battery goal, totals, quick buttons, and timeline between ml and US fl oz in Settings.
- Live total, remaining water, and percentage; real totals can exceed the goal while the battery stops at 100%.
- Undo the latest entry and reset today's log with confirmation.
- Automatic new calendar day, with previous logs available in the session's report.
- Daily timeline, seven-day completion chart with text equivalents, and CSV download.
- **Habit insights**: current goal streak, personal-best streak, goals completed, average refill, and time-of-day refill patterns.
- **Drink reminders**: a configurable 15–120 minute interval, test notification, persistent in-app reminder, 10-minute snooze, and optional desktop browser alerts.
- Light/dark appearance, larger text, reduced motion, and optional pace guide.
- A collapsed About sidebar credits **Created by Aaryan Odedra · IBCP Year 1 · CRS AI · FA-2 Project**. These details are not displayed in the main page.
- Separate session state for each visitor; no shared water log.

The four storyboard presets are Mini Cell (4–8 years, 1,200 ml), Standard (9–13, 1,700 ml), Max (14–64, 2,200 ml within the storyboard's range), and Eco (65+, 1,800 ml within its range). The brief gives age groups as examples; this implementation follows the supplied storyboard. These are educational project presets, not individually assessed medical recommendations.

The default timezone is `Asia/Kolkata`; change it in Settings. Enable drink reminders and select an interval in Settings, then use **Test notification** to preview an alert. Logging water restarts the timer. An unanswered reminder stays visible without repeatedly notifying you. You can log a glass directly from it, dismiss it, or snooze it for 10 minutes. Reminders operate from 8 AM–8 PM in your selected timezone and stop once the goal is reached.

For desktop alerts, click **Allow browser alerts** and grant this site notification permission in your browser. Permission is only requested from that explicit click. Browser support and OS notification settings vary; the in-app reminder works if desktop alerts are unavailable or blocked. Both require the app to remain open; these are not background push notifications after closing the app. The clock checks approximately every 30 seconds; background-tab throttling may delay checks. Try the local URL in a desktop browser if the app's embedded browser does not support alerts.

US fluid ounces are a volume measure, not weight ounces or UK fluid ounces. One US fl oz is approximately 29.57 ml. Display amounts use two decimals; stored entries and CSV exports use whole ml so switching display units does not change totals.

Insights use only days present in the current session. Reaching the goal once counts as one completed day; excess water earns no extra streak days. Missing calendar dates break a streak. Today's unfinished goal keeps yesterday's streak active until the day ends. Night/morning/afternoon/evening patterns use each refill's recorded local time.

## Data storage

Logs and preferences live in **Streamlit session memory**. Refreshing/reconnecting, closing the session, or restarting the server may clear them. A midnight reset preserves earlier days only for the current session. Download the CSV report before closing if you want a permanent copy. There is no login, tracking service, or database. Persistent storage across visits is not included in this version.

## Project files and code explanation

| File | Purpose |
|---|---|
| `app.py` | Streamlit widgets, setup, Today, Insights, Battery report, Settings, reminders, and sidebar |
| `logic.py` | Unit conversion, age presets, progress, logging, streaks, reset, rollover, reminder scheduling, CSV |
| `notifications.py` | Small local JavaScript component for explicit browser notification permission and desktop alert delivery |
| `visuals.py` | Original SVG battery and seven-day chart |
| `style.css` | Responsive layout, colours, focus outlines, animations, and accessibility styling |
| `.streamlit/config.toml` | Streamlit theme and telemetry setting |
| `requirements.txt` | Packages needed by both local runs and Streamlit Cloud |
| `tests/test_waterbuddy.py` | Calculation and Streamlit interaction checks |

The main calculation is `percentage = total / goal * 100`; remaining water is `max(0, goal - total)`. Battery fill is limited to `min(1, total / goal)`. `st.session_state.buddy` stores the current profile, settings, entries, and earlier days. Button callbacks change that state and Streamlit redraws the interface. The timer uses `st.fragment` to check the date and reminders without adding water. Goal changes recalculate today's progress and leave existing entries intact. Previous reports retain their own daily goal.

The interface follows the updated preference for a darker, minimal design without the turtle. Battery cells animate from the previous value to the new value in 360 ms when water is logged or undone. Buttons use short press and hover transitions. Nothing animates continuously, and Reduce motion disables these effects. The SVG graphics work on Streamlit Cloud without a desktop display or an image generation service. There is no machine-learning model to train: this app uses Python calculations and conditions.

## Verify the project

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The checks exercise zero/partial/exact/over-goal totals, every age preset, invalid input, ounce/cup conversion and rounding, milestone boundaries, goal feedback, undo/reset, midnight rollover, timezone restoration, reminder timing/snooze/deduplication, streak gaps, refill patterns, CSV totals, separate sessions, the sidebar credit, setup, unit display, report/Insights navigation, and settings forms. Browser permission is intentionally left for the user; automated checks do not grant OS notification permission.

For a quick demonstration, select Max and a 2,200 ml goal. Log 500 + 500 + 250 ml: the app shows **1,250 ml**, **950 ml remaining**, **57%** rounded on the home screen, and a halfway message. Add another 1,000 ml as two refills to see the full-charge state. Undo or use the confirmed reset to remove your demonstration entries.

## Put it on GitHub and Streamlit Community Cloud

The app is ready for deployment; this delivery does **not** create a GitHub repository or a public URL.

1. Sign into [GitHub](https://github.com/) and create a repository such as `WaterBuddy`.
2. Upload the files **inside this folder** so `app.py`, `logic.py`, `visuals.py`, `notifications.py`, `style.css`, and `requirements.txt` sit at the repository root. Include `.streamlit/config.toml` too. Do not upload `.venv`, `.cache`, `__pycache__`, or your water CSV.
3. Sign into [Streamlit Community Cloud](https://share.streamlit.io/) using your GitHub account.
4. Click **Create app**, select the repository and branch, and set the entrypoint to **app.py**. Select Python 3.12 or newer in the advanced settings if offered.
5. Click **Deploy**. Keep the resulting public app URL for your submission.
6. Open that public URL and test setup, a refill, report, and reset.
7. For the assessment submission, place your FA-1 storyboard link and the actual deployed Streamlit URL into the document/PDF requested by your brief. A local `localhost` URL is not a deployed submission link.

If you upload the entire WaterBuddy folder rather than its contents, choose `WaterBuddy/app.py` as the entrypoint and put `.streamlit/config.toml` at the repository root for the theme settings.

Official references: [Streamlit installation](https://docs.streamlit.io/get-started/installation), [session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state), [timed fragments](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment), [app testing](https://docs.streamlit.io/develop/concepts/app-testing), and [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

Notification and conversion references: [Streamlit v2 components](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component), [MDN Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API/Using_the_Notifications_API), and [NIST US volume conversions](https://www.nist.gov/pml/owm/metric-si/unit-conversion/approximate-conversions-us-customary-measures-metric).
