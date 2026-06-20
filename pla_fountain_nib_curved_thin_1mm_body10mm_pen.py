#!/usr/bin/env python3
"""Curved fountain-nib teaching pen: 1 mm nib, 10 mm body width.

v2 — smooth thickness transition from handle (3.2mm) to nib (1.0mm)
      integrated directly into the nib loft, breather hole enlarged to 1.0mm.

The transition is embedded in the nib sections themselves (not a separate
wedge), so the entire nib-to-handle junction is one continuous solid with
no seams.
"""
from math import hypot

from build123d import *


HANDLE_LENGTH = 100.0
NIB_LENGTH = 20.0
HANDLE_WIDTH = 10.0
HANDLE_THICKNESS = 3.2
NIB_SHOULDER_WIDTH = 12.0
NIB_THICKNESS = 1.0
NIB_EDGE_THICKNESS = 0.65
NIB_BOTTOM_Z = -HANDLE_THICKNESS / 2
NIB_CENTER_Z = NIB_BOTTOM_Z + NIB_THICKNESS / 2
NIB_TOP_Z = NIB_BOTTOM_Z + NIB_THICKNESS
REAR_RADIUS = HANDLE_WIDTH / 2

TRANSITION_LENGTH = 11.0  # mm over which handle thickness tapers to nib thickness (extended to cover breather/slit area)

TIP_SLOT_WIDTH = 0.2
INK_GROOVE_WIDTH = 0.55
INK_GROOVE_DEPTH = 0.18
BREATHER_HOLE_DIA = 1.0  # enlarged from 0.5mm for better printing
DECORATIVE_GROOVE_WIDTH = 0.32
DECORATIVE_GROOVE_DEPTH = 0.12
HANG_HOLE_DIA = 4.0


def _make_closed_face(points):
    with BuildLine() as outline:
        for index, point in enumerate(points):
            Line(point, points[(index + 1) % len(points)])
    make_face(outline.wires())


def _slot_polygon(start, end, width):
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length = hypot(dx, dy)
    nx = -dy / length * width / 2
    ny = dx / length * width / 2
    return [
        Vector(sx + nx, sy + ny),
        Vector(ex + nx, ey + ny),
        Vector(ex - nx, ey - ny),
        Vector(sx - nx, sy - ny),
    ]


def _nib_width(x):
    t = max(0.0, min(1.0, x / NIB_LENGTH))
    if t < 0.18:
        return HANDLE_WIDTH + (NIB_SHOULDER_WIDTH - HANDLE_WIDTH) * (t / 0.18)
    taper = (t - 0.18) / 0.82
    return NIB_SHOULDER_WIDTH * (1.0 - taper) + 1.25 * taper


def _nib_section(x):
    """Return a YZ-plane cross-section of the nib at position x.

    At x < TRANSITION_LENGTH the top surface smoothly ramps from the
    handle's full rectangle (z = +1.6) down to the nib's curved crown
    profile.  At x >= TRANSITION_LENGTH the section matches the original
    nib shape.
    """
    width = _nib_width(x)
    bottom = NIB_BOTTOM_Z

    if x < TRANSITION_LENGTH:
        # Transition zone: blend handle rectangle → nib curved profile
        t = x / TRANSITION_LENGTH
        handle_top = HANDLE_THICKNESS / 2
        edge_top = bottom + NIB_EDGE_THICKNESS
        crown_rise = NIB_THICKNESS - NIB_EDGE_THICKNESS
        pts = [(-width / 2, bottom)]
        for index in range(13):
            tp = -1.0 + 2.0 * index / 12
            y = tp * width / 2
            nib_z = edge_top + crown_rise * (1.0 - tp * tp)
            z = handle_top + (nib_z - handle_top) * t
            pts.append((y, z))
        pts.append((width / 2, bottom))
    else:
        edge_top = bottom + NIB_EDGE_THICKNESS
        crown_rise = NIB_THICKNESS - NIB_EDGE_THICKNESS
        pts = [(-width / 2, bottom)]
        for index in range(13):
            tp = -1.0 + 2.0 * index / 12
            y = tp * width / 2
            z = edge_top + crown_rise * (1.0 - tp * tp)
            pts.append((y, z))
        pts.append((width / 2, bottom))

    with BuildSketch(Plane.YZ.offset(x)) as section:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return section.sketch


def _nib_top_z_at(x):
    """Estimate the top-surface Z at the centre (y=0) of the nib at position x."""
    if x < TRANSITION_LENGTH:
        t = x / TRANSITION_LENGTH
        handle_top = HANDLE_THICKNESS / 2
        nib_z = NIB_TOP_Z
        return handle_top + (nib_z - handle_top) * t
    return NIB_TOP_Z


def _cut_top_polygon(points, depth):
    """Cut a shallow groove into the top nib surface."""
    avg_x = sum(p.X for p in points) / len(points)
    surface_z = _nib_top_z_at(avg_x)
    start_z = surface_z + 0.1
    with BuildSketch(Plane.XY.offset(start_z)) as groove:
        _make_closed_face(points)
    extrude(groove.sketch, amount=-(depth + 0.15), mode=Mode.SUBTRACT)


def gen_step():
    with BuildPart() as pen:
        straight_handle = HANDLE_LENGTH - REAR_RADIUS
        with Locations((-straight_handle / 2, 0, 0)):
            Box(straight_handle, HANDLE_WIDTH, HANDLE_THICKNESS)
        with Locations((-straight_handle, 0, 0)):
            Cylinder(REAR_RADIUS, HANDLE_THICKNESS)

        # Nib loft with transition integrated directly into the sections.
        # Use ruled=True for simpler geometry that can handle thin boolean cuts.
        loft(
            [
                _nib_section(x)
                for x in (0.0, 3.0, 6.0, 9.0, 11.0, 15.0, NIB_LENGTH)
            ],
            ruled=True,
        )

        # Breather hole and centre slit.
        # Breather hole at x=7.2 is within the transition zone — make it tall
        # enough to reach through the full handle thickness.
        with Locations((7.2, 0, 0)):
            Cylinder(BREATHER_HOLE_DIA / 2, HANDLE_THICKNESS + 1.0, mode=Mode.SUBTRACT)
        # Centre slit spans from x≈7.8 to 20, crossing both transition and
        # thin-nib zones.  Sketch a tall rectangle and extrude through.
        _slit_x_start = 6.8  # overlap with breather hole at x=7.2 so they connect
        _slit_x_end = 20.0
        _slit_mid_x = (_slit_x_start + _slit_x_end) / 2
        _slit_len = _slit_x_end - _slit_x_start
        with BuildSketch(Plane.XY.offset(HANDLE_THICKNESS / 2 + 1.0)):
            with BuildLine():
                Polyline(
                    (_slit_mid_x - _slit_len / 2, -TIP_SLOT_WIDTH / 2),
                    (_slit_mid_x + _slit_len / 2, -TIP_SLOT_WIDTH / 2),
                    (_slit_mid_x + _slit_len / 2, TIP_SLOT_WIDTH / 2),
                    (_slit_mid_x - _slit_len / 2, TIP_SLOT_WIDTH / 2),
                    close=True,
                )
            make_face()
        extrude(amount=-(HANDLE_THICKNESS + 2.0), mode=Mode.SUBTRACT)

        # Shallow ink groove on the handle top.
        with Locations((-8.0, 0, HANDLE_THICKNESS / 2 - INK_GROOVE_DEPTH / 2)):
            Box(18.0, INK_GROOVE_WIDTH, INK_GROOVE_DEPTH + 0.03, mode=Mode.SUBTRACT)

        # Fine decorative lines on the curved nib surface.
        _cut_top_polygon(
            _slot_polygon((1.0, -4.1), (11.0, -1.6), DECORATIVE_GROOVE_WIDTH),
            DECORATIVE_GROOVE_DEPTH,
        )
        _cut_top_polygon(
            _slot_polygon((1.0, 4.1), (11.0, 1.6), DECORATIVE_GROOVE_WIDTH),
            DECORATIVE_GROOVE_DEPTH,
        )

        with Locations((-94.0, 0, 0)):
            Cylinder(HANG_HOLE_DIA / 2, HANDLE_THICKNESS + 0.6, mode=Mode.SUBTRACT)

    result = pen.part
    result.label = "pla_fountain_nib_curved_thin_1mm_body10mm_pen_v2"
    return result
