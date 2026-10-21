"""WaterBuddy's calculations and session data, kept separate from the interface."""

from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import csv
import io

ML_PER_US_FL_OZ = Decimal("29.5735295625")


def to_ml(amount, unit: str) -> int:
    """Convert to whole ml once, avoiding cumulative unit-conversion rounding."""
    factors = {"Millilitres": Decimal(1), "Cups (250 ml)": Decimal(250),
               "US fl oz": ML_PER_US_FL_OZ}
    if unit not in factors or isinstance(amount, bool):
        raise ValueError("Choose millilitres, cups, or US fluid ounces.")
    try:
        value = Decimal(str(amount)) * factors[unit]
        if not value.is_finite() or value <= 0 or value > 1000:
            raise ValueError("Each refill must be between 1 and 1,000 ml.")
        result = int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        if result < 1:
            raise ValueError("Each refill must be at least 1 ml.")
        return result
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid amount of water.") from None


def format_water(ml: int, unit: str = "ml") -> str:
    if unit == "US fl oz":
        return f"{Decimal(ml)/ML_PER_US_FL_OZ:,.2f} US fl oz"
    return f"{ml:,} ml"

# These are the four example presets in the student's FA-1 storyboard.
# They are project defaults, not individual medical recommendations.
AGE_GROUPS = {
    "Mini Cell · 4–8 years": {"goal": 1200, "name": "Mini Cell", "ages": "4–8 years"},
    "Standard · 9–13 years": {"goal": 1700, "name": "Standard", "ages": "9–13 years"},
    "Max · 14–64 years": {"goal": 2200, "name": "Max", "ages": "14–64 years"},
    "Eco · 65+ years": {"goal": 1800, "name": "Eco", "ages": "65+ years"},
}


def new_state(now: datetime) -> dict:
    return {
        "age_group": None,
        "goal": 2200,
        "day": now.date().isoformat(),
        "entries": [],
        "history": {},
        "celebrated": False,
        "reminder_anchor": now.isoformat(),
        "reminder_pending": None,
        "snooze_until": None,
        "browser_event": None,
        "settings": {
            "theme": "Dark", "large_text": False, "reduce_motion": False,
            "reminders": False, "reminder_minutes": 60,
            "pace": False, "timezone": "Asia/Kolkata", "display_unit": "ml",
        },
    }


def progress(entries: list, goal: int) -> dict:
    if isinstance(goal, bool) or not isinstance(goal, int) or goal <= 0:
        raise ValueError("The daily goal must be a positive whole number.")
    total = sum(entry["amount"] for entry in entries)
    percent = total / goal * 100
    return {"total": total, "remaining": max(0, goal - total),
            "percent": percent, "fill": min(1.0, max(0.0, total / goal)),
            "cups": total / 250, "reached": total >= goal}


def ensure_day(state: dict, now: datetime) -> bool:
    """Archive the old day once; a new calendar day starts with an empty log."""
    today = now.date().isoformat()
    if state["day"] == today:
        return False
    state["history"][state["day"]] = {
        "goal": state["goal"], "entries": deepcopy(state["entries"])
    }
    state["day"] = today
    # Changing timezone can revisit a date already seen in this session.
    # Restore that date rather than replacing its existing log with an empty one.
    previous = state["history"].pop(today, None)
    state["entries"] = previous["entries"] if previous else []
    if previous:
        state["goal"] = previous["goal"]
    state["celebrated"] = False
    state["reminder_anchor"] = now.isoformat()
    state["reminder_pending"] = None
    state["snooze_until"] = None
    state["browser_event"] = None
    return True


def set_goal(state: dict, age_group: str, goal: int) -> None:
    if age_group not in AGE_GROUPS:
        raise ValueError("Please choose one of the four age groups.")
    if isinstance(goal, bool) or not isinstance(goal, int) or not 250 <= goal <= 5000:
        raise ValueError("Choose a daily goal from 250 to 5,000 ml.")
    state["age_group"] = age_group
    state["goal"] = goal
    # A goal edit should not create a second celebration for the same day.


def add_water(state: dict, amount: int, now: datetime) -> bool:
    """Return True only when this entry crosses the goal for the first time."""
    if isinstance(amount, bool) or not isinstance(amount, int) or not 1 <= amount <= 1000:
        raise ValueError("Log a whole number from 1 to 1,000 ml.")
    ensure_day(state, now)
    before = progress(state["entries"], state["goal"])
    state["entries"].append({"amount": amount, "time": now.isoformat()})
    state["reminder_anchor"] = now.isoformat()
    state["reminder_pending"] = None
    state["snooze_until"] = None
    state["browser_event"] = None
    after = progress(state["entries"], state["goal"])
    celebrate = not before["reached"] and after["reached"] and not state["celebrated"]
    if celebrate:
        state["celebrated"] = True
    return celebrate


def undo_last(state: dict) -> bool:
    if not state["entries"]:
        return False
    state["entries"].pop()
    return True


def reset_today(state: dict, now: datetime) -> None:
    ensure_day(state, now)
    state["entries"] = []
    state["celebrated"] = False
    state["reminder_anchor"] = now.isoformat()
    state["reminder_pending"] = None
    state["snooze_until"] = None
    state["browser_event"] = None


def milestone(percent: float) -> tuple:
    if percent > 100:
        return "Goal exceeded", "Beyond your goal. Well done!", "You’ve logged more than your daily target. Your goal is already complete."
    if percent >= 100:
        return "Goal reached", "Congratulations!", "Daily goal complete. That’s a habit worth celebrating."
    if percent >= 75:
        return "Nearly there", "Almost there.", "Your daily goal is within reach."
    if percent >= 50:
        return "Halfway", "Halfway there.", "Steady progress, one glass at a time."
    if percent >= 25:
        return "Charging", "A good start.", "Log your next refill when you’re ready."
    if percent > 0:
        return "Charging", "First refill logged.", "Every glass adds up."
    return "Ready", "Ready when you are.", "Log your first glass below."


def pace_target(now: datetime, goal: int) -> int:
    """A simple optional 08:00–20:00 guide, not a notification or requirement."""
    hour = now.hour + now.minute / 60
    fraction = min(1.0, max(0.0, (hour - 8) / 12))
    return round(goal * fraction / 50) * 50


def reminder_due(state: dict, now: datetime) -> bool:
    settings = state["settings"]
    if not settings["reminders"] or not 8 <= now.hour < 20:
        return False
    if progress(state["entries"], state["goal"])["reached"]:
        return False
    if state.get("reminder_pending"):
        return False
    if state.get("snooze_until"):
        return now >= datetime.fromisoformat(state["snooze_until"])
    elapsed = (now - datetime.fromisoformat(state["reminder_anchor"])).total_seconds()
    return elapsed >= settings["reminder_minutes"] * 60


def schedule_alert(state: dict, now: datetime, test: bool = False) -> None:
    state["reminder_pending"] = {"test": test}
    state["reminder_anchor"] = now.isoformat()
    state["snooze_until"] = None
    state["browser_event"] = {
        "id": f"{now.isoformat()}-{'test' if test else 'drink'}",
        "title": "WaterBuddy · Test reminder" if test else "WaterBuddy · Time for water",
        "body": "Your water reminders are working." if test else "Take a moment for a drink. Log it when you’re ready.",
    }


def snooze_reminder(state: dict, now: datetime) -> None:
    state["reminder_pending"] = None
    state["browser_event"] = None
    state["snooze_until"] = (now + timedelta(minutes=10)).isoformat()


def habit_insights(state: dict) -> dict:
    """Streaks reward reaching goals, with no extra points for excess volume."""
    records = daily_records(state)
    achieved = sorted(date.fromisoformat(day) for day, record in records.items()
                      if progress(record["entries"], record["goal"])["reached"])
    best, run, previous = 0, 0, None
    for day in achieved:
        run = run + 1 if previous and day - previous == timedelta(days=1) else 1
        best = max(best, run)
        previous = day
    completed = set(achieved)
    cursor = date.fromisoformat(state["day"])
    # An unfinished day does not break yesterday's streak before midnight.
    if cursor not in completed:
        cursor -= timedelta(days=1)
    current = 0
    while cursor in completed:
        current += 1
        cursor -= timedelta(days=1)
    entries = state["entries"]
    periods = {"Morning": 0, "Afternoon": 0, "Evening": 0, "Night": 0}
    for entry in entries:
        hour = datetime.fromisoformat(entry["time"]).hour
        period = "Morning" if 5 <= hour < 12 else "Afternoon" if hour < 17 and hour >= 12 else "Evening" if 17 <= hour < 22 else "Night"
        periods[period] += entry["amount"]
    return {"current_streak": current, "best_streak": best, "goals_met": len(achieved),
            "refills": len(entries), "average_refill": round(sum(e["amount"] for e in entries)/len(entries)) if entries else 0,
            "periods": periods}


def daily_records(state: dict) -> dict:
    records = deepcopy(state["history"])
    records[state["day"]] = {"goal": state["goal"], "entries": deepcopy(state["entries"])}
    return records


def export_csv(state: dict) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Date", "Time (with UTC offset)", "Amount (ml)", "Running total (ml)",
                     "Daily goal (ml)", "Goal achieved (%)"])
    for day, record in sorted(daily_records(state).items()):
        running = 0
        for entry in record["entries"]:
            running += entry["amount"]
            writer.writerow([day, entry["time"], entry["amount"], running,
                             record["goal"], round(running / record["goal"] * 100, 1)])
    return output.getvalue()
