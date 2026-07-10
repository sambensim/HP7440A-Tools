import math
from HersheyFonts import HersheyFonts
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import LineString

_hersheyCache = {}
_ttfCache = {}


def _getHershey(fontName):
    key = fontName or "default"
    if key not in _hersheyCache:
        f = HersheyFonts()
        if fontName:
            f.load_default_font(fontName)
        else:
            f.load_default_font()
        _hersheyCache[key] = f
    return _hersheyCache[key]


def _samePoint(p, q, eps=1e-6):
    return abs(p[0] - q[0]) <= eps and abs(p[1] - q[1]) <= eps


def hersheyPolylines(text, height, fontName=None, kerning=0.0, tolerance=None):
    f = _getHershey(fontName)
    f.normalize_rendering(height)
    f.render_options.spacing = kerning
    polylines = []
    current = None
    for (x1, y1), (x2, y2) in f.lines_for_text(text):
        a, b = (x1, y1), (x2, y2)
        if current is not None and _samePoint(current[-1], a):
            current.append(b)
        else:
            if current is not None:
                polylines.append(current)
            current = [a, b]
    if current is not None:
        polylines.append(current)
    if tolerance:
        polylines = [list(LineString(pl).simplify(tolerance).coords)
                     for pl in polylines if len(pl) >= 2]
    return polylines


def hersheyFontNames():
    return HersheyFonts().default_font_names


class _FlattenPen(BasePen):
    def __init__(self, glyphSet, tolerance):
        super().__init__(glyphSet)
        self._tol = tolerance
        self.contours = []
        self._pts = None

    def _steps(self, pts):
        length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                     for i in range(len(pts) - 1))
        return max(2, min(24, int(math.ceil(math.sqrt(length / (8.0 * self._tol))))))

    def _moveTo(self, pt):
        self._pts = [pt]

    def _lineTo(self, pt):
        self._pts.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._pts[-1]
        n = self._steps([p0, p1, p2, p3])
        for i in range(1, n + 1):
            t = i / n
            m = 1 - t
            self._pts.append((
                m * m * m * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t * t * t * p3[0],
                m * m * m * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t * t * t * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._pts[-1]
        n = self._steps([p0, p1, p2])
        for i in range(1, n + 1):
            t = i / n
            m = 1 - t
            self._pts.append((
                m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if self._pts is not None:
            self.contours.append(self._pts)
            self._pts = None

    def _endPath(self):
        self._closePath()


def _getTtf(path):
    if path not in _ttfCache:
        _ttfCache[path] = TTFont(path)
    return _ttfCache[path]


def _simplifyContour(contour, tolerance):
    ring = contour + [contour[0]]
    simplified = list(LineString(ring).simplify(tolerance).coords)
    return simplified[:-1]


def ttfGlyphContours(text, fontPath, size, kerning=0.0, tolerance=None):
    font = _getTtf(fontPath)
    glyphSet = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    if tolerance is None:
        tolerance = max(size / 200.0, 0.5)
    tolFont = tolerance / scale
    glyphs = []
    x = 0.0
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            x += size * 0.6
            continue
        pen = _FlattenPen(glyphSet, tolFont)
        glyph = glyphSet[name]
        glyph.draw(pen)
        contours = []
        for c in pen.contours:
            if len(c) < 3:
                continue
            scaled = [(px * scale + x, py * scale) for px, py in c]
            xs = [p[0] for p in scaled]
            ys = [p[1] for p in scaled]
            if max(xs) - min(xs) < 2 * tolerance and max(ys) - min(ys) < 2 * tolerance:
                continue
            simplified = _simplifyContour(scaled, tolerance)
            if len(simplified) >= 3:
                contours.append(simplified)
        if contours:
            glyphs.append(contours)
        x += glyph.width * scale + kerning
    return glyphs


def hersheyCharSize(ch, height, fontName=None):
    f = _getHershey(fontName)
    f.normalize_rendering(height)
    pts = [p for seg in f.lines_for_text(ch) for p in seg]
    if not pts:
        return (height * 0.5, 0.0)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(xs) - min(xs), max(ys) - min(ys))


def ttfCharSize(ch, fontPath, size):
    font = _getTtf(fontPath)
    cmap = font.getBestCmap()
    name = cmap.get(ord(ch))
    if name is None:
        return (size * 0.6, 0.0)
    glyphs = ttfGlyphContours(ch, fontPath, size)
    if not glyphs:
        return (font.getGlyphSet()[name].width * size / font["head"].unitsPerEm, 0.0)
    pts = [p for contour in glyphs[0] for p in contour]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (max(xs) - min(xs), max(ys) - min(ys))


def hersheyTextWidth(text, height, fontName=None, kerning=0.0):
    pts = [p for pl in hersheyPolylines(text, height, fontName, kerning) for p in pl]
    if not pts:
        return 0.0
    xs = [p[0] for p in pts]
    return max(xs) - min(xs)


def ttfTextWidth(text, fontPath, size, kerning=0.0):
    pts = [p for glyph in ttfGlyphContours(text, fontPath, size, kerning=kerning)
           for c in glyph for p in c]
    if not pts:
        return 0.0
    xs = [p[0] for p in pts]
    return max(xs) - min(xs)