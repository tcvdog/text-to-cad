#!/usr/bin/env python3
"""CAD probe part for validating the local build123d -> STEP workflow."""
from build123d import *


LENGTH = 60.0
WIDTH = 35.0
THICKNESS = 8.0
CORNER_FILLET = 3.0
MOUNT_SPACING = 42.0
MOUNT_HOLE_DIA = 4.5
BOSS_DIA = 18.0
BOSS_HEIGHT = 6.0
BORE_DIA = 8.0


def gen_step():
    with BuildPart() as part:
        Box(LENGTH, WIDTH, THICKNESS, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        fillet(part.edges().filter_by(Axis.Z), radius=CORNER_FILLET)

        with Locations((0, 0, THICKNESS / 2)):
            Cylinder(BOSS_DIA / 2, BOSS_HEIGHT)

        with Locations((-MOUNT_SPACING / 2, 0, 0), (MOUNT_SPACING / 2, 0, 0)):
            Hole(MOUNT_HOLE_DIA / 2, depth=THICKNESS + 1)

        with Locations((0, 0, THICKNESS / 2 + BOSS_HEIGHT / 2)):
            Hole(BORE_DIA / 2, depth=BOSS_HEIGHT + THICKNESS + 1)

    result = part.part
    result.label = "cad_probe_mount_plate"
    return result

