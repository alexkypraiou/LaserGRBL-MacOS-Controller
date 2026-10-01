from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from time import monotonic

Vector3 = tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class GrblStatus:
    raw: str
    state: str
    substate: str | None = None
    work_position: Vector3 | None = None
    machine_position: Vector3 | None = None
    work_coordinate_offset: Vector3 | None = None
    feed_rate: int | None = None
    spindle_speed: int | None = None


def _parse_vector(value: str) -> Vector3 | None:
    try:
        coordinates = tuple(float(part) for part in value.split(","))
    except ValueError:
        return None
    if len(coordinates) != 3:
        return None
    return coordinates[0], coordinates[1], coordinates[2]


def parse_status_report(payload: str) -> GrblStatus | None:
    payload = payload.strip()
    if not payload.startswith("<") or not payload.endswith(">"):
        return None

    sections = payload[1:-1].split("|")
    if not sections or not sections[0]:
        return None

    state_parts = sections[0].split(":", 1)
    state = state_parts[0]
    substate = state_parts[1] if len(state_parts) == 2 else None
    fields: dict[str, str] = {}

    for section in sections[1:]:
        if ":" not in section:
            continue
        key, value = section.split(":", 1)
        fields[key] = value

    work_position = _parse_vector(fields["WPos"]) if "WPos" in fields else None
    machine_position = _parse_vector(fields["MPos"]) if "MPos" in fields else None
    offset = _parse_vector(fields["WCO"]) if "WCO" in fields else None

    if work_position is None and machine_position is not None and offset is not None:
        work_position = tuple(
            machine_coordinate - coordinate_offset
            for machine_coordinate, coordinate_offset in zip(machine_position, offset, strict=True)
        )

    feed_rate: int | None = None
    spindle_speed: int | None = None
    if "FS" in fields:
        try:
            feed_value, spindle_value = fields["FS"].split(",", 1)
            feed_rate = int(float(feed_value))
            spindle_speed = int(float(spindle_value))
        except ValueError:
            pass

    return GrblStatus(
        raw=payload,
        state=state,
        substate=substate,
        work_position=work_position,
        machine_position=machine_position,
        work_coordinate_offset=offset,
        feed_rate=feed_rate,
        spindle_speed=spindle_speed,
    )


class GrblLineBuffer:
    def __init__(self, maximum_size: int = 65_536) -> None:
        self._buffer = ""
        self.maximum_size = maximum_size

    def feed(self, chunk: bytes | str) -> list[str]:
        if isinstance(chunk, bytes):
            text = chunk.decode("utf-8", errors="replace")
        else:
            text = chunk

        self._buffer += text.replace("\r", "\n")
        if len(self._buffer) > self.maximum_size:
            self._buffer = self._buffer[-self.maximum_size :]

        lines: list[str] = []
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if stripped := line.strip():
                lines.append(stripped)
        return lines

    def clear(self) -> None:
        self._buffer = ""


@dataclass(frozen=True, slots=True)
class GCodeLine:
    source_index: int
    text: str


def clean_gcode_line(line: str) -> str:
    result: list[str] = []
    comment_depth = 0
    for character in line:
        if character == "(":
            comment_depth += 1
        elif character == ")" and comment_depth:
            comment_depth -= 1
        elif character == ";" and comment_depth == 0:
            break
        elif comment_depth == 0:
            result.append(character)
    return "".join(result).strip()


def normalize_gcode(source: str | Iterable[str]) -> list[GCodeLine]:
    lines = source.splitlines() if isinstance(source, str) else source
    normalized: list[GCodeLine] = []
    for source_index, line in enumerate(lines):
        cleaned = clean_gcode_line(line)
        if cleaned and cleaned != "%":
            normalized.append(GCodeLine(source_index=source_index, text=cleaned))
    return normalized


class StreamState(StrEnum):
    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class GCodeStreamer:
    def __init__(self) -> None:
        self.lines: list[GCodeLine] = []
        self.state = StreamState.IDLE
        self.cursor = 0
        self.acknowledged = 0
        self.in_flight: GCodeLine | None = None
        self.error_message: str | None = None
        self.started_at: float | None = None
        self.finished_at: float | None = None

    @property
    def total(self) -> int:
        return len(self.lines)

    @property
    def is_active(self) -> bool:
        return self.state in {StreamState.RUNNING, StreamState.PAUSED}

    @property
    def progress(self) -> float:
        if not self.total:
            return 0.0
        return self.acknowledged / self.total

    @property
    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        endpoint = self.finished_at if self.finished_at is not None else monotonic()
        return max(0.0, endpoint - self.started_at)

    @property
    def estimated_remaining(self) -> float | None:
        if self.acknowledged == 0:
            return None
        remaining = self.total - self.acknowledged
        return (self.elapsed / self.acknowledged) * remaining

    def load(self, source: str | Iterable[str]) -> int:
        if self.is_active:
            raise RuntimeError("Cannot replace G-code while a job is active.")
        self.lines = normalize_gcode(source)
        self.state = StreamState.READY if self.lines else StreamState.IDLE
        self.cursor = 0
        self.acknowledged = 0
        self.in_flight = None
        self.error_message = None
        self.started_at = None
        self.finished_at = None
        return self.total

    def start(self) -> None:
        if not self.lines:
            raise RuntimeError("No G-code is loaded.")
        self.cursor = 0
        self.acknowledged = 0
        self.in_flight = None
        self.error_message = None
        self.started_at = monotonic()
        self.finished_at = None
        self.state = StreamState.RUNNING

    def next_command(self) -> GCodeLine | None:
        if self.state != StreamState.RUNNING or self.in_flight is not None:
            return None
        if self.cursor >= self.total:
            return None
        self.in_flight = self.lines[self.cursor]
        self.cursor += 1
        return self.in_flight

    def acknowledge(self) -> bool:
        if self.in_flight is None:
            return False
        self.in_flight = None
        self.acknowledged += 1
        if self.acknowledged >= self.total:
            self.state = StreamState.COMPLETED
            self.finished_at = monotonic()
        return True

    def pause(self) -> None:
        if self.state == StreamState.RUNNING:
            self.state = StreamState.PAUSED

    def resume(self) -> None:
        if self.state == StreamState.PAUSED:
            self.state = StreamState.RUNNING

    def cancel(self) -> None:
        if self.is_active:
            self.state = StreamState.CANCELLED
            self.in_flight = None
            self.finished_at = monotonic()

    def fail(self, message: str) -> None:
        self.state = StreamState.ERROR
        self.error_message = message
        self.in_flight = None
        self.finished_at = monotonic()
