# Troubleshooting

## No serial ports appear

1. Reconnect the USB cable and click **Refresh**.
2. Use a data-capable USB cable; charge-only cables do not expose a serial device.
3. Check **System Information → USB** to confirm that macOS sees the controller.
4. Install the driver required by the controller's USB-to-serial chip, if any.
5. Close other applications that may already have the port open.

Common controller chips include CH340, CP210x, and FTDI. Download drivers only from the chip or board manufacturer.

## The port opens but GRBL is not detected

- Confirm that the board is running GRBL 1.1-compatible firmware at 115200 baud.
- Open a serial terminal and send `?`; a healthy controller should return a status frame such as `<Idle|...>`.
- Press the controller reset button and try again.
- Verify that another terminal or sender is not using the same device.

## The machine reports `Alarm`

Read the full alarm line in the Console tab. Correct the physical or configuration problem before unlocking. Typical causes include an incomplete homing cycle, a limit switch, a hard-limit event, or a reset during motion.

Use `$X` only after confirming that movement is safe. Do not use unlock to ignore an active limit condition.

## Jog controls are disabled

Jogging is enabled only while connected, no job is active, and the machine reports `Idle` or `Jog`. Home or unlock the controller as required, then wait for `Idle`.

## A job stops on `error:n`

The application stops streaming when GRBL returns an error. The Console tab retains the exact message and the last transmitted line. Check the GRBL error-code documentation for your firmware version, correct the G-code, reset the controller state, and retry at low power.

## The preview does not match the program

The current preview draws `G0` and `G1` motion. `G2`/`G3` arcs, canned cycles, coordinate-system changes, and controller-specific macros may not be represented. They are still streamed unchanged. Validate advanced programs in a dedicated G-code simulator.

## Image G-code is too large

Reduce one or more of the following:

- Physical width or height.
- Pixels per millimeter.
- Image detail before importing.

The generator rejects extremely large rasters to avoid freezing the interface or producing impractical jobs.

## The image is faint or does not engrave

- Confirm GRBL laser mode with `$32=1`.
- Verify that the controller supports `M4` dynamic laser power.
- Increase the maximum `S` value gradually.
- Reduce feed rate gradually.
- Raise the threshold to include more pixels.
- Confirm focus, material compatibility, and laser wiring.

Make one controlled change at a time and keep power low during testing.

