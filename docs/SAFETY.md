# Laser Safety Guide

LaserGRBL for macOS controls equipment capable of causing permanent eye injury, severe burns, fire, and exposure to hazardous fumes. Software cannot make an unsafe machine safe. The operator is responsible for the machine, workspace, material, firmware configuration, and all required protective systems.

## Minimum safety controls

Do not operate a laser unless all of the following are in place:

- A closed, fire-resistant enclosure suitable for the laser wavelength and power.
- Wavelength-rated eye protection from a reputable manufacturer.
- Effective local exhaust ventilation routed to a safe location.
- A reachable, tested, physical emergency-stop circuit that removes laser power.
- Reliable limit switches, machine grounding, cable strain relief, and a secure work surface.
- A suitable fire extinguisher and a second method for suppressing small material fires.
- Continuous adult supervision for the complete job, including cooldown.

## Material hazards

Never engrave or cut an unknown material. Some plastics, coatings, adhesives, foams, composites, and treated woods can release corrosive or highly toxic gases. PVC and vinyl are common examples of materials that must not be processed with a hobby laser.

Obtain the material safety data sheet and verify laser compatibility before use. When in doubt, do not process the material.

## Before every job

1. Inspect the enclosure, optics, belts, wiring, cooling, air assist, and exhaust.
2. Confirm the correct work origin, units, dimensions, feed rate, and maximum power.
3. Verify that the path stays inside the usable machine area.
4. Remove combustible debris and unnecessary items from the enclosure.
5. Focus the laser according to the manufacturer's instructions.
6. Run a frame or dry test with the laser disabled when possible.
7. Test a small sample at minimum practical power.
8. Keep the emergency stop and extinguisher immediately accessible.

## During a job

- Stay beside the machine and watch the cutting area.
- Stop immediately if flame persists, smoke changes unexpectedly, motion stalls, or the exhaust fails.
- Do not rely on a webcam, remote desktop, software pause, or GRBL reset as the only emergency control.
- Do not bypass enclosure switches or controller alarms.

## Software controls

- **Pause** sends GRBL feed hold (`!`). The controller may decelerate before motion stops.
- **Resume** sends cycle start (`~`). Confirm that the machine is safe before resuming.
- **Abort** sends feed hold followed by soft reset (`Ctrl-X`). This is not a substitute for a hardware emergency stop.
- **STOP / RESET** uses the same software-level sequence. Use the physical emergency stop when immediate power removal is required.
- The low-power laser test requires an explicit checkbox and remains active only while its button is held. Treat even low output as hazardous.

## After a job

- Wait for smoke and hot material to cool before opening the enclosure.
- Confirm the laser output is off.
- Inspect the workpiece and waste area for smoldering material.
- Clean residue according to the machine manufacturer's guidance.
- Disconnect power before servicing electronics or motion components.

This guide is general information, not a replacement for the laser manufacturer's manual, local regulations, workplace procedures, or professional safety advice.

