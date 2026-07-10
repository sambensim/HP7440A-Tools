import math
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely import affinity


def geometryFromContours(contours):
    polys = []
    for c in contours:
        if len(c) >= 3:
            p = Polygon(c)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty:
                polys.append(p)
    polys.sort(key=lambda p: p.area, reverse=True)
    geom = None
    for p in polys:
        geom = p if geom is None else geom.symmetric_difference(p)
    return geom


def _collectSegments(geom, out):
    if geom.is_empty or isinstance(geom, Point):
        return
    if isinstance(geom, LineString):
        c = list(geom.coords)
        for i in range(len(c) - 1):
            if c[i] != c[i + 1]:
                out.append((c[i], c[i + 1]))
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            _collectSegments(g, out)


def hatchGeometry(geom, spacing, angle=0.0):
    if geom is None or geom.is_empty:
        return []
    geom = geom.buffer(-spacing / 2.0)
    if geom.is_empty:
        return []
    deg = math.degrees(angle)
    work = affinity.rotate(geom, -deg, origin=(0, 0)) if angle else geom
    minx, miny, maxx, maxy = work.bounds
    rows = []
    y = miny
    while y <= maxy + 1e-9:
        cut = work.intersection(LineString([(minx - spacing, y), (maxx + spacing, y)]))
        segs = []
        _collectSegments(cut, segs)
        segs = [(a, b) if a[0] <= b[0] else (b, a) for a, b in segs]
        segs.sort(key=lambda s: s[0][0])
        if segs:
            rows.append(segs)
        y += spacing
    out = []
    for i, segs in enumerate(rows):
        if i % 2 == 1:
            segs = [(b, a) for a, b in reversed(segs)]
        out.extend(segs)
    if angle:
        ca, sa = math.cos(angle), math.sin(angle)
        out = [((x1 * ca - y1 * sa, x1 * sa + y1 * ca),
                (x2 * ca - y2 * sa, x2 * sa + y2 * ca))
               for (x1, y1), (x2, y2) in out]
    return out


def hatchSegments(boundary, spacing, holes=None, angle=0.0):
    poly = Polygon(boundary, holes or [])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return hatchGeometry(poly, spacing, angle)


def hatchPolylines(geom, spacing, angle=0.0, threshold=None):
    segs = hatchGeometry(geom, spacing, angle)
    if not segs:
        return []
    if threshold is None:
        threshold = spacing * 1.5
    polylines = []
    current = list(segs[0])
    for a, b in segs[1:]:
        gap = math.hypot(a[0] - current[-1][0], a[1] - current[-1][1])
        if gap <= threshold:
            current.append(a)
            current.append(b)
        else:
            polylines.append(current)
            current = [a, b]
    polylines.append(current)
    return polylines


def hatchFillPolylines(boundary, spacing, holes=None, angle=0.0, threshold=None):
    poly = Polygon(boundary, holes or [])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return hatchPolylines(poly, spacing, angle, threshold)


def _collectRings(geom, out):
    if geom.is_empty:
        return
    if isinstance(geom, Polygon):
        out.append(list(geom.exterior.coords))
        for interior in geom.interiors:
            out.append(list(interior.coords))
    elif hasattr(geom, "geoms"):
        for g in geom.geoms:
            _collectRings(g, out)


def contourGeometry(geom, spacing):
    if geom is None or geom.is_empty:
        return []
    out = []
    g = geom.buffer(-spacing / 2.0)
    while not g.is_empty:
        _collectRings(g, out)
        g = g.buffer(-spacing)
    return out


def contourPolylines(boundary, spacing, holes=None):
    poly = Polygon(boundary, holes or [])
    if not poly.is_valid:
        poly = poly.buffer(0)
    return contourGeometry(poly, spacing)