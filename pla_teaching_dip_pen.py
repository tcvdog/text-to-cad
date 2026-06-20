#!/usr/bin/env python3
"""PLA-friendly one-piece teaching dip pen for 0.4 mm FDM printing."""
from build123d import *


HANDLE_LENGTH = 100.0
NIB_LENGTH = 20.0
HANDLE_WIDTH = 14.0
BODY_THICKNESS = 3.0
REAR_RADIUS = HANDLE_WIDTH / 2

INK_GROOVE_WIDTH = 1.2
TIP_SLOT_WIDTH = 0.9
INK_GROOVE_DEPTH = 0.9
RESERVOIR_RADIUS = 5.0
RESERVOIR_DEPTH = 1.0
HANG_HOLE_DIA = 4.5


def _make_closed_face(points):
    with BuildLine() as outline:
        for index, point in enumerate(points):
            Line(point, points[(index + 1) % len(points)])
    make_face(outline.wires())


def gen_step():
    with BuildPart() as pen:
        # Flat handle with a rounded tail, sized to print flat without supports.
        straight_handle = HANDLE_LENGTH - REAR_RADIUS
        with Locations((-straight_handle / 2, 0, 0)):
            Box(straight_handle, HANDLE_WIDTH, BODY_THICKNESS)
        with Locations((-straight_handle, 0, 0)):
            Cylinder(REAR_RADIUS, BODY_THICKNESS)

        # Broad nib: 20 mm long, blunt enough for PLA, with a printable center slot.
        with BuildSketch(Plane.XY):
            _make_closed_face(
                [
                    Vector(0, -HANDLE_WIDTH / 2),
                    Vector(14.0, -3.6),
                    Vector(NIB_LENGTH, -0.85),
                    Vector(NIB_LENGTH, 0.85),
                    Vector(14.0, 3.6),
                    Vector(0, HANDLE_WIDTH / 2),
                ]
            )
        extrude(amount=BODY_THICKNESS / 2, both=True)

        # Soften only the outer vertical perimeter before cutting print features.
        fillet(pen.edges().filter_by(Axis.Z), radius=0.8)

        # Open ink groove on the top face. It is deliberately wider than two
        # nozzle lines so slicers preserve it on a 0.4 mm setup.
        top_cut_z = BODY_THICKNESS / 2 - INK_GROOVE_DEPTH / 2
        with Locations((-19.0, 0, top_cut_z)):
            Box(58.0, INK_GROOVE_WIDTH, INK_GROOVE_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # Small cup that holds ink after dipping; open to the center groove.
        with Locations((-35.0, 0, BODY_THICKNESS / 2 - RESERVOIR_DEPTH / 2)):
            Cylinder(
                RESERVOIR_RADIUS,
                RESERVOIR_DEPTH + 0.05,
                mode=Mode.SUBTRACT,
            )

        # Through slot at the nib end. This creates two visible tines and helps
        # transfer dipped ink, while staying printable with a 0.4 mm nozzle.
        with Locations((11.8, 0, 0)):
            Box(17.2, TIP_SLOT_WIDTH, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)

        # Optional hanging/storage hole at the back of the teaching model.
        with Locations((-94.0, 0, 0)):
            Cylinder(HANG_HOLE_DIA / 2, BODY_THICKNESS + 0.6, mode=Mode.SUBTRACT)

    result = pen.part
    result.label = "pla_teaching_dip_pen_0p4mm"
    return result

