from __future__ import annotations

from collections import deque
import logging
import socket
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("virtual_pet")

PISUGAR_SERVER_SOCKET_PATH = Path("/tmp/pisugar-server.sock")
PISUGAR_SOCKET_TIMEOUT_SECONDS = 0.25
PISUGAR_STATUS_POLL_INTERVAL_SECONDS = 15.0
BATTERY_DISPLAY_SAMPLE_SIZE = 4
BATTERY_DISPLAY_HYSTERESIS_PERCENT = 2


@dataclass(frozen=True)
class BatteryStatus:
    percentage: int
    plugged_in: bool | None = None


class BatteryStatusSmoother:
    def __init__(
        self,
        *,
        sample_size: int = BATTERY_DISPLAY_SAMPLE_SIZE,
        hysteresis_percent: int = BATTERY_DISPLAY_HYSTERESIS_PERCENT,
    ) -> None:
        self._sample_size = max(1, int(sample_size))
        self._hysteresis_percent = max(0, int(hysteresis_percent))
        self._percent_samples: deque[int] = deque(maxlen=self._sample_size)
        self._display_status: BatteryStatus | None = None

    def update(self, raw_status: BatteryStatus | None) -> BatteryStatus | None:
        if raw_status is None:
            return self._display_status

        normalized_percentage = max(0, min(100, int(raw_status.percentage)))
        self._percent_samples.append(normalized_percentage)
        averaged_percentage = int(round(sum(self._percent_samples) / len(self._percent_samples)))

        if self._display_status is None:
            self._display_status = BatteryStatus(
                percentage=averaged_percentage,
                plugged_in=raw_status.plugged_in,
            )
            return self._display_status

        displayed_percentage = self._display_status.percentage
        if abs(averaged_percentage - displayed_percentage) >= self._hysteresis_percent:
            displayed_percentage = averaged_percentage

        self._display_status = BatteryStatus(
            percentage=displayed_percentage,
            plugged_in=raw_status.plugged_in,
        )
        return self._display_status


class PiSugarBatteryMonitor:
    def __init__(
        self,
        socket_path: Path = PISUGAR_SERVER_SOCKET_PATH,
        *,
        poll_interval_seconds: float = PISUGAR_STATUS_POLL_INTERVAL_SECONDS,
        time_func=time.monotonic,
        socket_timeout_seconds: float = PISUGAR_SOCKET_TIMEOUT_SECONDS,
    ) -> None:
        self._socket_path = socket_path
        self._poll_interval_seconds = poll_interval_seconds
        self._time_func = time_func
        self._socket_timeout_seconds = socket_timeout_seconds
        self._last_polled_at = 0.0
        self._cached_status: BatteryStatus | None = None

    def get_status(self) -> BatteryStatus | None:
        now = self._time_func()
        if self._cached_status is not None and (now - self._last_polled_at) < self._poll_interval_seconds:
            return self._cached_status

        self._last_polled_at = now
        latest_status = self.read_status()
        if latest_status is not None:
            self._cached_status = latest_status
        return self._cached_status

    def read_status(self) -> BatteryStatus | None:
        battery_percent = self.query_percent("get battery", "battery")
        if battery_percent is None:
            return None

        plugged_in = self.query_bool("get battery_power_plugged", "battery_power_plugged")
        if plugged_in is None:
            plugged_in = self.query_bool("get battery_charging", "battery_charging")

        return BatteryStatus(percentage=battery_percent, plugged_in=plugged_in)

    def query_percent(self, command: str, key: str) -> int | None:
        response = self.send_command(command)
        if response is None:
            return None

        value = self.parse_response_value(response, key)
        if value is None:
            return None

        try:
            return max(0, min(100, int(round(float(value)))))
        except ValueError:
            logger.warning("Failed to parse PiSugar battery percent from '%s'.", response)
            return None

    def query_bool(self, command: str, key: str) -> bool | None:
        response = self.send_command(command)
        if response is None:
            return None

        value = self.parse_response_value(response, key)
        if value is None:
            return None

        if value == "true":
            return True
        if value == "false":
            return False

        logger.warning("Failed to parse PiSugar boolean response from '%s'.", response)
        return None

    def send_command(self, command: str) -> str | None:
        if not self._socket_path.exists():
            return None

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(self._socket_timeout_seconds)
                client.connect(str(self._socket_path))
                client.sendall(f"{command}\n".encode("utf-8"))
                client.shutdown(socket.SHUT_WR)
                chunks: list[bytes] = []
                while True:
                    payload = client.recv(256)
                    if not payload:
                        break
                    chunks.append(payload)
        except (OSError, socket.timeout):
            logger.debug("PiSugar battery query failed for command '%s'.", command, exc_info=True)
            return None

        response_text = b"".join(chunks).decode("utf-8", errors="ignore").strip()
        if not response_text:
            return None

        return response_text.splitlines()[0].strip()

    @staticmethod
    def parse_response_value(response: str, key: str) -> str | None:
        normalized_prefix = f"{key}:"
        if not response.startswith(normalized_prefix):
            return None
        return response.split(":", 1)[1].strip().lower()


def create_battery_monitor(enable_battery_monitor: bool) -> PiSugarBatteryMonitor | None:
    if not enable_battery_monitor:
        return None

    monitor = PiSugarBatteryMonitor()
    if monitor.get_status() is None:
        return None

    logger.info("Initialized PiSugar battery monitor.")
    return monitor
