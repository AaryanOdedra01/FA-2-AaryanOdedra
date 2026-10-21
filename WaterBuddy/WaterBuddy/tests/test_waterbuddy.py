"""Run from the WaterBuddy folder: python -m unittest discover -s tests -v"""

import csv
from datetime import datetime, timedelta
import io
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from logic import (AGE_GROUPS, add_water, ensure_day, export_csv, format_water,
                   habit_insights, milestone, new_state, progress, reminder_due,
                   reset_today, schedule_alert, set_goal, snooze_reminder, to_ml, undo_last)

NOW = datetime(2026, 10, 21, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata"))


class HydrationTests(unittest.TestCase):
    def setUp(self):
        self.state = new_state(NOW)
        set_goal(self.state, list(AGE_GROUPS)[2], 2000)

    def test_calculations_zero_partial_exact_and_over_goal(self):
        for total, remaining, percent, fill in [(0, 2000, 0, 0), (500, 1500, 25, .25),
                                                 (2000, 0, 100, 1), (2500, 0, 125, 1)]:
            with self.subTest(total=total):
                p = progress([{"amount": total}], 2000)
                self.assertEqual((p["remaining"], p["percent"], p["fill"]), (remaining, percent, fill))

    def test_all_age_groups_and_manual_goal(self):
        for label, profile in AGE_GROUPS.items():
            set_goal(self.state, label, profile["goal"])
            self.assertEqual(self.state["goal"], profile["goal"])
        set_goal(self.state, label, 1950)
        self.assertEqual(self.state["goal"], 1950)

    def test_invalid_input_never_changes_log(self):
        for value in [0, -10, 1001, 2.5, True, "250"]:
            with self.assertRaises(ValueError):
                add_water(self.state, value, NOW)
        self.assertEqual(self.state["entries"], [])
        for goal in [0, 249, 5001, True, 1000.5]:
            with self.assertRaises(ValueError):
                set_goal(self.state, list(AGE_GROUPS)[0], goal)

    def test_celebration_once_and_undo(self):
        self.assertFalse(add_water(self.state, 1000, NOW))
        self.assertTrue(add_water(self.state, 1000, NOW))
        self.assertFalse(add_water(self.state, 250, NOW))
        undo_last(self.state)
        undo_last(self.state)
        self.assertFalse(add_water(self.state, 1000, NOW))
        self.assertEqual(progress(self.state["entries"], 2000)["total"], 2000)

    def test_midnight_rollover_archives_and_is_idempotent(self):
        add_water(self.state, 500, NOW)
        tomorrow = NOW + timedelta(days=1)
        self.assertTrue(ensure_day(self.state, tomorrow))
        self.assertFalse(ensure_day(self.state, tomorrow))
        self.assertEqual(self.state["entries"], [])
        self.assertEqual(self.state["history"]["2026-10-21"]["entries"][0]["amount"], 500)
        add_water(self.state, 250, tomorrow)
        ensure_day(self.state, NOW)  # Revisited date after timezone change.
        self.assertEqual(progress(self.state["entries"], 2000)["total"], 500)
        self.assertEqual(self.state["history"]["2026-10-22"]["entries"][0]["amount"], 250)

    def test_reset_keeps_previous_days_and_goal(self):
        add_water(self.state, 500, NOW)
        tomorrow = NOW + timedelta(days=1)
        add_water(self.state, 250, tomorrow)
        reset_today(self.state, tomorrow)
        self.assertEqual(self.state["entries"], [])
        self.assertEqual(self.state["goal"], 2000)
        self.assertIn("2026-10-21", self.state["history"])
        self.assertFalse(undo_last(self.state))

    def test_reminders_obey_time_setting_refills_and_goal(self):
        self.assertFalse(reminder_due(self.state, NOW + timedelta(hours=2)))
        self.state["settings"]["reminders"] = True
        self.assertFalse(reminder_due(self.state, NOW + timedelta(minutes=59)))
        self.assertTrue(reminder_due(self.state, NOW + timedelta(hours=1)))
        add_water(self.state, 250, NOW + timedelta(hours=1))
        self.assertFalse(reminder_due(self.state, NOW + timedelta(hours=1, minutes=1)))
        self.assertFalse(reminder_due(self.state, NOW.replace(hour=22)))
        self.state["goal"] = 250
        self.assertFalse(reminder_due(self.state, NOW + timedelta(hours=2)))

    def test_csv_running_totals_and_goal_snapshots(self):
        add_water(self.state, 250, NOW)
        add_water(self.state, 500, NOW + timedelta(minutes=30))
        ensure_day(self.state, NOW + timedelta(days=1))
        set_goal(self.state, list(AGE_GROUPS)[0], 1200)
        add_water(self.state, 300, NOW + timedelta(days=1))
        rows = list(csv.reader(io.StringIO(export_csv(self.state))))
        self.assertEqual(rows[2][3:], ["750", "2000", "37.5"])
        self.assertEqual(rows[3][3:], ["300", "1200", "25.0"])
        self.assertIn("+05:30", rows[1][1])

    def test_milestone_boundaries(self):
        expected = [(0, "Ready"), (1, "Charging"), (25, "Charging"),
                    (50, "Halfway"), (75, "Nearly there"), (100, "Goal reached"), (101, "Goal exceeded")]
        for percent, label in expected:
            self.assertEqual(milestone(percent)[0], label)

    def test_ounces_and_cups_convert_once_to_whole_ml(self):
        self.assertEqual(to_ml(8, "US fl oz"), 237)
        self.assertEqual(to_ml(33.8, "US fl oz"), 1000)
        self.assertEqual(to_ml(1.5, "Cups (250 ml)"), 375)
        self.assertEqual(to_ml(0.25, "Cups (250 ml)"), 63)
        self.assertEqual(format_water(250, "US fl oz"), "8.45 US fl oz")
        for amount, unit in [(34, "US fl oz"), (float("nan"), "US fl oz"),
                             (None, "Millilitres"), (-1, "US fl oz"), (True, "US fl oz"), (1, "oz")]:
            with self.subTest(amount=amount, unit=unit):
                with self.assertRaises(ValueError):
                    to_ml(amount, unit)

    def test_streaks_gaps_and_over_goal_do_not_inflate_records(self):
        for day, total in [("2026-10-17", 2000), ("2026-10-18", 2500),
                           ("2026-10-19", 500), ("2026-10-20", 2000)]:
            self.state["history"][day] = {"goal": 2000, "entries": [{"amount": total, "time": f"{day}T10:00:00+05:30"}]}
        info = habit_insights(self.state)
        self.assertEqual((info["current_streak"], info["best_streak"], info["goals_met"]), (1, 2, 3))
        add_water(self.state, 1000, NOW)
        add_water(self.state, 1000, NOW)
        add_water(self.state, 500, NOW.replace(hour=14))
        info = habit_insights(self.state)
        self.assertEqual((info["current_streak"], info["best_streak"], info["goals_met"]), (2, 2, 4))
        self.assertEqual(info["refills"], 3)
        self.assertEqual(info["periods"]["Morning"], 2000)
        self.assertEqual(info["periods"]["Afternoon"], 500)
        reset_today(self.state, NOW)
        self.assertEqual(habit_insights(self.state)["current_streak"], 1)

    def test_alert_snooze_pending_and_refill_cancel(self):
        self.state["settings"]["reminders"] = True
        schedule_alert(self.state, NOW)
        self.assertFalse(reminder_due(self.state, NOW + timedelta(hours=1)))
        event_id = self.state["browser_event"]["id"]
        snooze_reminder(self.state, NOW)
        self.assertFalse(reminder_due(self.state, NOW + timedelta(minutes=9, seconds=59)))
        self.assertTrue(reminder_due(self.state, NOW + timedelta(minutes=10)))
        schedule_alert(self.state, NOW + timedelta(minutes=10))
        self.assertNotEqual(self.state["browser_event"]["id"], event_id)
        add_water(self.state, 250, NOW + timedelta(minutes=11))
        self.assertIsNone(self.state["reminder_pending"])
        self.assertIsNone(self.state["snooze_until"])
        self.assertFalse(reminder_due(self.state, NOW + timedelta(minutes=12)))


class InterfaceTests(unittest.TestCase):
    """Exercise Streamlit's actual widgets, callbacks, forms, and reruns."""

    @classmethod
    def setUpClass(cls):
        from streamlit.testing.v1 import AppTest
        cls.AppTest = AppTest

    def app(self):
        app = self.AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["buddy"]["settings"]["theme"], "Dark")
        return app

    def click(self, app, label):
        matches = [b for b in app.button if b.label == label]
        self.assertEqual(len(matches), 1, label)
        matches[0].click().run()
        self.assertFalse(app.exception)

    def start(self):
        app = self.app()
        self.click(app, "Continue to my goal →")
        self.click(app, "Let’s start charging →")
        return app

    def test_setup_logging_custom_cups_undo_and_report(self):
        app = self.start()
        self.click(app, "+ 250 ml · one glass")
        self.click(app, "+ 500 ml")
        app.radio(key="custom_unit").set_value("Cups (250 ml)").run()
        app.number_input(key="custom_cups").set_value(1.5)
        self.click(app, "Add water")
        self.assertEqual(progress(app.session_state["buddy"]["entries"], 2200)["total"], 1125)
        self.click(app, "↶ Undo last entry")
        self.assertEqual(progress(app.session_state["buddy"]["entries"], 2200)["total"], 750)
        app.radio(key="navigation").set_value("Battery report").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("download_button")), 1)

    def test_settings_goal_theme_and_reset_confirmation(self):
        app = self.start()
        self.click(app, "+ 250 ml · one glass")
        app.radio(key="navigation").set_value("Settings").run()
        app.number_input(key="edit_goal").set_value(1950)
        self.click(app, "Save daily goal")
        self.assertEqual(app.session_state["buddy"]["goal"], 1950)
        app.selectbox(key="edit_age").set_value(list(AGE_GROUPS)[0])
        next(c for c in app.checkbox if c.label == "Use the selected age group’s preset").check()
        self.click(app, "Save daily goal")
        self.assertEqual(app.session_state["buddy"]["goal"], 1200)
        self.assertEqual(app.number_input(key="edit_goal").value, 1200)
        appearance = next(r for r in app.radio if r.label == "Appearance")
        appearance.set_value("Light")
        self.click(app, "Save preferences")
        self.assertEqual(app.session_state["buddy"]["settings"]["theme"], "Light")
        self.click(app, "Reset today’s water log")
        self.assertEqual(len(app.session_state["buddy"]["entries"]), 1)
        self.click(app, "Keep my entries")
        self.click(app, "Reset today’s water log")
        self.click(app, "Yes, clear today")
        self.assertEqual(app.session_state["buddy"]["entries"], [])

    def test_independent_sessions_do_not_share_water(self):
        first = self.start()
        self.click(first, "+ 250 ml · one glass")
        second = self.start()
        self.assertEqual(second.session_state["buddy"]["entries"], [])
        self.assertEqual(len(first.session_state["buddy"]["entries"]), 1)

    def test_ounce_logging_display_insights_and_sidebar_credit(self):
        app = self.start()
        self.assertTrue(any("Created by **Aaryan Odedra**" in m.value for m in app.sidebar.markdown))
        app.radio(key="custom_unit").set_value("US fl oz").run()
        app.number_input(key="custom_oz").set_value(8.0)
        self.click(app, "Add water")
        self.assertEqual(app.session_state["buddy"]["entries"][0]["amount"], 237)
        app.radio(key="navigation").set_value("Settings").run()
        app.selectbox(key="display_unit").set_value("US fl oz")
        self.click(app, "Save preferences")
        app.radio(key="navigation").set_value("Today").run()
        self.click(app, "+ 8.45 US fl oz · one glass")
        self.assertEqual(progress(app.session_state["buddy"]["entries"], 2200)["total"], 487)
        app.radio(key="navigation").set_value("Insights").run()
        self.assertFalse(app.exception)
        self.assertEqual(habit_insights(app.session_state["buddy"])["refills"], 2)

    def test_reminder_controls_test_alert_and_snooze(self):
        app = self.start()
        app.radio(key="navigation").set_value("Settings").run()
        next(t for t in app.toggle if t.label == "Remind me to drink water").set_value(True)
        app.selectbox(key="reminder_interval").set_value(15)
        self.click(app, "Save reminders")
        self.assertTrue(app.session_state["buddy"]["settings"]["reminders"])
        self.assertEqual(app.session_state["buddy"]["settings"]["reminder_minutes"], 15)
        self.click(app, "Test notification")
        self.assertTrue(app.session_state["buddy"]["reminder_pending"]["test"])
        self.click(app, "Dismiss test reminder")
        self.assertIsNone(app.session_state["buddy"]["reminder_pending"])
        schedule_alert(app.session_state["buddy"], datetime.now(ZoneInfo("Asia/Kolkata")))
        app.run()
        self.click(app, "Snooze 10 min")
        self.assertIsNone(app.session_state["buddy"]["reminder_pending"])
        self.assertIsNotNone(app.session_state["buddy"]["snooze_until"])


if __name__ == "__main__":
    unittest.main()
