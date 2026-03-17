from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from virtual_pet.battery import BatteryStatus, PiSugarBatteryMonitor


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


if __name__ == "__main__":
    unittest.main()
