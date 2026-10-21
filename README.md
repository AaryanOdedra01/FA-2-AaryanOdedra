WaterBuddy

**A simple hydration tracker that turns daily water intake into visible progress.**

WaterBuddy helps users set a daily water goal, record their drinks, and understand their hydration habits through an eight-cell battery, reminders, reports, and habit insights. Its minimal interface uses a dark theme by default, with clear numbers and subtle interaction feedback.

**Created by Aaryan Odedra**  
**IBCP Year 1 · CRS AI · FA-2 Project**

Link to the Streamlit app: https://fa-2-aaryanodedra-w7qcbjiq9mkskcahyyva4f.streamlit.app/

## Project overview

This project develops the WaterBuddy concept from an FA-1 storyboard into an interactive Python application. Streamlit provides the web interface, Python handles the calculations and session data, and original SVG graphics display the battery and progress chart.

The application focuses on four actions: choosing a goal, logging water, checking progress, and reviewing habits. It does not require an account, database connection, or API key.

## Main features

### 1. Personalised daily goals

The setup process has two steps: select an age group, then confirm or adjust the starting goal.

| Battery size | Age group | Starting daily goal |
|---|---|---:|
| Mini Cell | 4–8 years | 1,200 ml |
| Standard | 9–13 years | 1,700 ml |
| Max | 14–64 years | 2,200 ml |
| Eco | 65+ years | 1,800 ml |

Users can set a custom daily goal between 250 and 5,000 ml and change it later in Settings. Changing today's goal recalculates progress without deleting logged refills. Previous daily reports retain their recorded goal.

These values are example presets from the project storyboard, rather than individually assessed medical recommendations.

### 2. Live water battery

An eight-cell battery represents the proportion of the daily goal completed. Cells fill progressively, including a partially filled cell when the total falls between segments. The battery changes to a muted green when the goal is reached.

The dashboard also shows total water logged, the remaining amount, and the daily goal. The percentage continues to reflect the real total above 100%, while the battery stops at full.

For example, logging 2,500 ml against a 2,000 ml goal gives 125% progress, 0 ml remaining, and a full battery.

### 3. Quick and custom logging

Quick buttons add 150 ml, 250 ml, or 500 ml. Users can also enter a custom amount in:

- **Millilitres:** a whole-number amount between 1 and 1,000 ml per refill.
- **Cups:** each project cup represents 250 ml.
- **US fluid ounces:** one US fl oz is approximately 29.57 ml.

Custom amounts are converted once and stored to the nearest whole millilitre. For example, 8 US fl oz logs 237 ml. Fluid ounces measure volume; this app uses US fluid ounces rather than UK fluid ounces or weight ounces.

The display preference can switch between ml and US fl oz. This updates the goal shown beside the battery, dashboard totals, quick-button labels, and timeline amounts. Switching display units does not change the underlying water log.

### 4. Milestone encouragement and congratulations

Messages respond to the user's progress, from the first refill through halfway and nearly complete. Reaching the target displays a congratulatory message. Exceeding it displays a separate message showing how much has been logged above the goal.

Feedback uses short messages and small notifications. The interface has no mascot, confetti, or large celebration animation.

### 5. Drink reminders

Users can enable reminders in **Settings → Drink reminders** and select a 15, 30, 45, 60, 90, or 120-minute interval.

Reminders operate from 8 AM to 8 PM in the selected timezone while the app remains open. Logging water restarts the timer, and reaching the daily goal stops drink reminders. An unanswered reminder stays visible without repeatedly sending the same alert.

A reminder offers three actions: log a 250 ml glass after drinking it, snooze for 10 minutes, or dismiss the reminder. The **Test notification** button previews an in-app alert without waiting for the selected interval.

Optional desktop alerts use the browser's Notifications API. Users must explicitly click **Allow browser alerts** and grant permission for the site. If desktop alerts are unsupported or blocked, in-app reminders remain available.

Both reminder types require the app to stay open. They are not push notifications after the app is closed. The app checks the clock approximately every 30 seconds; browser background throttling can delay checks.

### 6. Habit Insights

The Insights page adds a view of consistency and refill patterns beyond the battery:

| Insight | What it shows |
|---|---|
| Current goal streak | Consecutive completed goal days, counting backwards from today or yesterday if today is still unfinished |
| Personal-best streak | The longest sequence of completed goal days recorded in the session |
| Goals completed | The number of recorded days that reached their target |
| Refills logged | Today's number of water entries |
| Average refill | Today's average amount per entry |
| Refill rhythm | How today's logged water is distributed across four time periods |

The time periods are morning (5 AM–noon), afternoon (noon–5 PM), evening (5–10 PM), and night (10 PM–5 AM). They use the local time recorded with each refill.

Completing a goal counts once per day. Extra water does not earn extra streak days. Missing calendar dates break a streak; an unfinished today keeps yesterday's streak active until the day ends.

**Insights use only the days recorded in the current session. They are not permanent records across visits.**

### 7. Battery reports and CSV export

The Battery report page provides a date selector, daily totals, a refill timeline, and a chart covering the last seven calendar days. The timeline shows each entry's time, amount, running total, and percentage of the day's goal. Text summaries accompany the chart.

Users can download all logged days in the session as a CSV containing the date, timestamp with UTC offset, refill amount, running total, daily goal, and completion percentage. CSV amounts always use ml, regardless of the display preference.

### 8. Undo, reset, and a new day

**Undo last entry** removes the latest refill from today's log. **Reset today's water log** asks for confirmation before clearing all of today's entries. It keeps the daily goal and earlier reports held in the same session.

A new calendar day starts with an empty log in the selected timezone. The previous day is retained in the session's report history. Date checks happen during interactions and the periodic clock check while the app is active.

### 9. Appearance and accessibility

The interface includes dark and light appearance, a larger-text option, reduced motion, keyboard focus indicators, and visible numeric progress so that colour is not the only indicator.

Buttons, tabs, expanders, and inputs use short interaction transitions. Changed battery cells animate from their previous fill to the new value in 360 milliseconds. Nothing animates continuously, and reduced-motion settings disable these effects.

An optional gentle pace guide divides the daily goal across 8 AM–8 PM. It is a visual guide rather than a required drinking schedule.

The default timezone is `Asia/Kolkata`. Other available choices are UTC, London, New York, Los Angeles, and Sydney.

### 10. About sidebar

The About sidebar credits **Created by Aaryan Odedra**, followed by **IBCP Year 1** and **CRS AI · FA-2 Project**. The sidebar keeps these details separate from the main dashboard.

## How to use WaterBuddy

1. Choose an age group and confirm or adjust the daily goal.
2. On Today, log water using a quick button or a custom amount.
3. Check the battery, remaining amount, and progress message.
4. Open Insights to review consistency and refill patterns.
5. Open Battery report to review entries or download the CSV.
6. Use Settings to configure reminders, display units, appearance, accessibility, and timezone.

## Technology and calculations

| Technology | Purpose |
|---|---|
| Python | Validation, unit conversion, progress calculations, logging, streaks, reminders, and CSV export |
| Streamlit | Widgets, page layout, session state, and periodic clock checks |
| CSS | Dark and light styling, responsive layout, and interaction feedback |
| SVG | Original battery and seven-day chart |
| JavaScript | A small local component for optional browser notification permission and delivery |
| tzdata | Timezone support across environments |

The project was tested with Python 3.12 and Streamlit 1.66.0. It uses calculations and conditions; it does not train a machine-learning model.

The core calculations are:

```python
total = sum(entry["amount"] for entry in entries)
remaining = max(0, goal - total)
percentage = total / goal * 100
battery_fill = min(1.0, total / goal)
```

`st.session_state` stores the profile, preferences, entries, reminder state, and daily history. Widget interactions update that state and redraw the interface. A timed `st.fragment` checks the date and reminder schedule without adding water automatically.

## Repository structure

This repository contains a deployment copy and a full development copy of WaterBuddy:

```text
FA-2-AaryanOdedra/
├── README.md
├── WaterBuddy-Streamlit/
│   ├── app.py
│   ├── logic.py
│   ├── notifications.py
│   ├── visuals.py
│   ├── style.css
│   └── requirements.txt
└── WaterBuddy/
    └── Full development package, including supporting files
```

Use **`WaterBuddy-Streamlit/app.py`** as the Streamlit Community Cloud entrypoint. The deployment folder already has its own `requirements.txt` beside the entrypoint.

| File | Responsibility |
|---|---|
| `app.py` | Setup, Today, Insights, Battery report, Settings, sidebar, and reminder interface |
| `logic.py` | Validation, conversions, progress, entries, streaks, date changes, reminder rules, and CSV generation |
| `notifications.py` | Optional desktop alerts through a local Streamlit v2 component |
| `visuals.py` | SVG battery and chart generation |
| `style.css` | Layout, colours, accessibility styling, and transitions |
| `requirements.txt` | Python packages required to run the app |

## Run locally

Clone the repository or download and extract it. Open a terminal in `WaterBuddy-Streamlit`.

On Windows:

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

Open the local address printed in the terminal. Keep the terminal running while using the app; press Ctrl+C to stop it. The full development package also includes a Windows launcher.

## Deploy on Streamlit Community Cloud

At [Streamlit Community Cloud](https://share.streamlit.io/), create an app using these settings:

| Setting | Value |
|---|---|
| Repository | `AaryanOdedra01/FA-2-AaryanOdedra` |
| Branch | `main` |
| Main file path | `WaterBuddy-Streamlit/app.py` |
| Python version | `3.12` |
| Secrets | None required |

Deploy the app, wait for it to load, and test its public URL in a private/incognito window. Keep the resulting `.streamlit.app` URL for submission. Add the actual deployed URL to this README after deployment; this README does not claim that a public app has already been deployed.

### Theme configuration

For the configured Streamlit theme, add **`.streamlit/config.toml` at the repository root**, alongside the root README rather than inside the deployment folder. The application also applies its own interface styling.

```toml
[theme]
base = "dark"
primaryColor = "#94ccff"
backgroundColor = "#0e1116"
secondaryBackgroundColor = "#1b232d"
textColor = "#e7edf5"
font = "sans serif"

[browser]
gatherUsageStats = false

[server]
headless = true
```

Streamlit's official guides explain [repository layout](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) and [deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Data storage and limitations

Water logs and preferences are held in **Streamlit's server-side session memory**, separately for each visitor. They are not saved to a persistent database. Refreshing or reconnecting, closing the session, or restarting the server may clear them.

Daily history and streaks therefore cover the current session only. Download the CSV before closing the app to keep a copy of the water log. Downloading a CSV does not automatically restore it into a future session.

Desktop alerts depend on browser support, permission, and operating-system settings. Reminders do not continue after the app is closed, and background-tab throttling can delay checks. The app provides in-app reminders when desktop notifications are unavailable.

## Validation

The development version passed 17 automated checks covering calculations, goal presets, invalid inputs, unit conversion and rounding, milestone boundaries, undo/reset, midnight rollover, timezone date restoration, reminder timing and snooze, streak gaps, refill patterns, CSV totals, independent sessions, the sidebar credit, and Streamlit interactions.

Browser checks also verified ounce logging, display switching, the test reminder, goal messages, and the Insights page. Browser notification permission remains an explicit user choice; the automated checks do not grant OS notification permission.

If the full package's `tests` directory is available, run this from the `WaterBuddy` development folder after installing the requirements:

```bash
python -m unittest discover -s tests -v
```

## References

- [Streamlit documentation](https://docs.streamlit.io/)
- [Streamlit session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Streamlit timed fragments](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)
- [Streamlit v2 components](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component)
- [MDN Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API/Using_the_Notifications_API)
- [NIST US volume conversions](https://www.nist.gov/pml/owm/metric-si/unit-conversion/approximate-conversions-us-customary-measures-metric)
