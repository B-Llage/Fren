from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from virtual_pet.battery import BatteryStatus, BatteryStatusSmoother, PiSugarBatteryMonitor


class BatteryMonitorTests(unittest.TestCase):
    def test_read_status_parses_pisugar_responses(self) -> None:
        monitor = PiSugarBatteryMonitor(socket_path=Path("unused"))

        with mock.patch.object(
            monitor,
            "send_command",
            side_effect=["battery: 83.6", "battery_power_plugged: true"],
        ):
            status = monitor.read_status()

        self.assertEqual(status, BatteryStatus(percentage=84, plugged_in=True))

    def test_get_status_keeps_cached_value_when_refresh_fails(self) -> None:
        time_values = iter((10.0, 30.0))
        monitor = PiSugarBatteryMonitor(
            socket_path=Path("unused"),
            poll_interval_seconds=5.0,
            time_func=lambda: next(time_values),
        )

        with mock.patch.object(
            monitor,
            "read_status",
            side_effect=[BatteryStatus(percentage=71, plugged_in=False), None],
        ):
            first_status = monitor.get_status()
            second_status = monitor.get_status()

        self.assertEqual(first_status, BatteryStatus(percentage=71, plugged_in=False))
        self.assertEqual(second_status, BatteryStatus(percentage=71, plugged_in=False))

    def test_parse_response_value_rejects_unexpected_keys(self) -> None:
        self.assertIsNone(PiSugarBatteryMonitor.parse_response_value("model: PiSugar3", "battery"))

    def test_smoother_averages_samples_before_updating_display(self) -> None:
        smoother = BatteryStatusSmoother(sample_size=4, hysteresis_percent=2)

        first = smoother.update(BatteryStatus(percentage=50, plugged_in=False))
        second = smoother.update(BatteryStatus(percentage=51, plugged_in=False))
        third = smoother.update(BatteryStatus(percentage=52, plugged_in=False))
        fourth = smoother.update(BatteryStatus(percentage=54, plugged_in=False))

        self.assertEqual(first, BatteryStatus(percentage=50, plugged_in=False))
        self.assertEqual(second, BatteryStatus(percentage=50, plugged_in=False))
        self.assertEqual(third, BatteryStatus(percentage=50, plugged_in=False))
        self.assertEqual(fourth, BatteryStatus(percentage=52, plugged_in=False))

    def test_smoother_keeps_last_displayed_value_when_raw_status_is_missing(self) -> None:
        smoother = BatteryStatusSmoother(sample_size=4, hysteresis_percent=2)

        smoother.update(BatteryStatus(percentage=63, plugged_in=False))
        cached_status = smoother.update(None)

        self.assertEqual(cached_status, BatteryStatus(percentage=63, plugged_in=False))

    def test_smoother_updates_power_state_without_forcing_percent_jump(self) -> None:
        smoother = BatteryStatusSmoother(sample_size=4, hysteresis_percent=2)

        smoother.update(BatteryStatus(percentage=72, plugged_in=False))
        updated_status = smoother.update(BatteryStatus(percentage=73, plugged_in=True))

        self.assertEqual(updated_status, BatteryStatus(percentage=72, plugged_in=True))


if __name__ == "__main__":
    unittest.main()
