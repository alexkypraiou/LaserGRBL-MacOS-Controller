from lasergrbl_macos.grbl import (
    GCodeLine,
    GCodeStreamer,
    GrblLineBuffer,
    StreamState,
    clean_gcode_line,
    normalize_gcode,
    parse_status_report,
)


def test_parses_work_position_status() -> None:
    report = parse_status_report("<Idle|WPos:12.500,-3.250,0.000|FS:1000,120>")

    assert report is not None
    assert report.state == "Idle"
    assert report.work_position == (12.5, -3.25, 0.0)
    assert report.feed_rate == 1000
    assert report.spindle_speed == 120


def test_derives_work_position_from_machine_position_and_offset() -> None:
    report = parse_status_report("<Hold:0|MPos:10.000,20.000,3.000|WCO:2.000,5.000,1.000>")

    assert report is not None
    assert report.state == "Hold"
    assert report.substate == "0"
    assert report.work_position == (8.0, 15.0, 2.0)


def test_rejects_non_status_payload() -> None:
    assert parse_status_report("ok") is None
    assert parse_status_report("<>") is None


def test_line_buffer_handles_fragmented_and_batched_messages() -> None:
    buffer = GrblLineBuffer()

    assert buffer.feed(b"<Idle|WPos:0,0") == []
    assert buffer.feed(b",0>\r\nok\nerror:2\r\n") == ["<Idle|WPos:0,0,0>", "ok", "error:2"]


def test_gcode_cleaning_removes_comments() -> None:
    assert clean_gcode_line("G1 X10 (move right) Y5 ; note") == "G1 X10  Y5"
    assert normalize_gcode(["; header", "G21", "%", "G0 X0 (origin)"]) == [
        GCodeLine(source_index=1, text="G21"),
        GCodeLine(source_index=3, text="G0 X0"),
    ]


def test_streamer_waits_for_acknowledgements() -> None:
    streamer = GCodeStreamer()
    assert streamer.load("G21\nG0 X0\nG1 X10") == 3

    streamer.start()
    first = streamer.next_command()
    assert first is not None and first.text == "G21"
    assert streamer.next_command() is None

    assert streamer.acknowledge()
    second = streamer.next_command()
    assert second is not None and second.text == "G0 X0"
    assert streamer.acknowledge()
    third = streamer.next_command()
    assert third is not None and third.text == "G1 X10"
    assert streamer.acknowledge()
    assert streamer.state == StreamState.COMPLETED
    assert streamer.progress == 1.0


def test_streamer_pauses_and_cancels() -> None:
    streamer = GCodeStreamer()
    streamer.load("G1 X1\nG1 X2")
    streamer.start()
    streamer.pause()
    assert streamer.next_command() is None
    streamer.resume()
    assert streamer.next_command() is not None
    streamer.cancel()
    assert streamer.state == StreamState.CANCELLED
