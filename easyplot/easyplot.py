from easyplot.optimize_verify_estimate import OVE
from easyplot.plot_preview import preview
import math
import easyplot.pen_definition
import easyplot.shape_fill
import easyplot.fonts
from enum import Enum

class FILLMODE(Enum):
    NONE = 0
    LINE = 1
    CONTOUR = 3

BOUNDS = [10300, 7650]
UNITS_PER_mm = 1.0 / 0.025 #1 plotter unit == 0.025 mm
UNITS_PER_INCH = 25.4 * UNITS_PER_mm
instructions = []
currentPos = [0,0]
carriage : easyplot.pen_definition.PenCarriage = easyplot.pen_definition.PenCarriage()
currentPenIndex = 0
fillMode = FILLMODE.NONE
lineFillAngle = 0
fillPen = None
currentDrawSpeed = 40
fillSpeed = 10

def init(penCarriage : easyplot.pen_definition.PenCarriage = easyplot.pen_definition.ALL_BLACK, carriageIndex = 3, startX = 0, startY = 0):
    global instructions, carriage
    carriage = penCarriage
    instructions.append("IN;")
    switchPen(carriageIndex)
    penUp()
    set(startX, startY)

def debugPrint():
    global instructions
    print(instructions[-5:])

def switchPen(carriageIndex : int = None):
    if carriageIndex == None:
        return
    if carriageIndex not in carriage.getUsedSlots():
        print("ERROR: " + str(carriageIndex) + "not in carriage (loaded slots: " + str(carriage.getUsedSlots()) + ")")
    global currentPenIndex
    currentPenIndex = carriageIndex
    instructions.append("SP" + str(carriageIndex + 1) + ";")

def set(x, y):
    global instructions, currentPos
    currentPos = [int(x), int(y)]
    instructions.append("PA " + str(int(x)) + ", " + str(int(y)) + ";")

def move(x, y):
    global instructions, currentPos
    currentPos = [currentPos[0] + int(x),currentPos[1] + int(y)]
    instructions.append("PR " + str(int(x)) + ", " + str(int(y)) + ";")

def penDown():
    global instructions
    instructions.append("PD;")

def penUp():
    global instructions
    instructions.append("PU;")

def end(show = True, outputPath = "output.txt"):
    global instructions, carriage
    instructions.append("SP;")
    instructions = OVE(instructions, carriage)
    if len(instructions) != 0:
        with open(outputPath, "w") as f:
            f.write('\n'.join(instructions))
            if show:
                preview(instructions, carriage)

def getPos():
    global currentPos
    return currentPos

def line(x1, y1, x2, y2):
    penUp()
    set(x1, y1)
    penDown()
    set(x2, y2)
    penUp()


def point(x, y):
    penUp()
    set(x, y)
    penDown()
    penUp()

def bezier(startx, starty, c1x, c1y, c2x, c2y, endx, endy, stepSize = 80):
    steps = round(estimateBezierLength(startx, starty, c1x, c1y, c2x, c2y, endx, endy) / stepSize)
    penUp()
    set(startx, starty)
    penDown()
    for i in range(steps):
        p = (i+1) / steps
        x = (1 - p) ** 3 * startx \
            + 3 * (1 - p) ** 2 * p * c1x \
            + 3 * (1 - p) * p ** 2 * c2x \
            + p ** 3 * endx
        y = (1 - p) ** 3 * starty \
            + 3 * (1 - p) ** 2 * p * c1y \
            + 3 * (1 - p) * p ** 2 * c2y \
            + p ** 3 * endy
        set(x, y)
    penUp()

def estimateBezierLength(startx, starty, c1x, c1y, c2x, c2y, endx, endy):
    dist = 0
    for t in range(100):
        p = t/100
        x = (1 - p) ** 3 * startx \
            + 3 * (1 - p) ** 2 * p * c1x \
            + 3 * (1 - p) * p ** 2 * c2x \
            + p ** 3 * endx
        y = (1 - p) ** 3 * starty \
            + 3 * (1 - p) ** 2 * p * c1y \
            + 3 * (1 - p) * p ** 2 * c2y \
            + p ** 3 * endy
        dist += math.hypot(x, y)
    return dist


def _fillSpacing():
    global currentPenIndex
    if currentPenIndex not in carriage.getUsedSlots():
        print("ERROR: invalid slot " + str(currentPenIndex) + ". available slots: " + str(carriage.getUsedSlots()))
        return
    return carriage.getSlot(currentPenIndex).pixel_width

def polyline(points):
    penUp()
    set(points[0][0], points[0][1])
    penDown()
    for px, py in points[1:]:
        set(px, py)
    penUp()

def fillPolygon(boundary, holes=None, angle=0.0):
    from shapely.geometry import Polygon
    _fillPolygonGeom(Polygon(boundary, holes or []), angle)

def fillPolygonContour(boundary, holes=None):
    from shapely.geometry import Polygon
    _fillPolygonContourGeom(Polygon(boundary, holes or []))

def _fillWith(boundary):
    global fillMode
    if fillMode == FILLMODE.CONTOUR:
        fillPolygonContour(boundary)
    elif fillMode == FILLMODE.LINE:
        global lineFillAngle
        fillPolygon(boundary, None, lineFillAngle)

def arc(x, y, r, rads, stepSize = 40):
    rads = min(rads, 2 * math.pi)
    steps = max(round((rads * r) / stepSize), 16)
    pts = [(x + r, y)]
    for i in range(steps):
        p = ((i + 1) / steps)
        pts.append((x + math.cos(p * rads) * r, y + math.sin(p * rads) * r))
    _fillWith(pts if rads >= 2 * math.pi else pts + [(x, y)])
    polyline(pts)

def circle(x, y, r, stepSize = 40):
    arc(x, y, r, 2 * math.pi, stepSize)

def rect(x, y, w, h):
    _fillWith([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    penUp()
    set(x, y)
    penDown()
    move(w, 0)
    move(0, h)
    move(-w, 0)
    move(0, -h)
    penUp()

def square(x, y, s):
    rect(x, y, s, s)

class JUSTIFY(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

fillSpacingCoef = 1.0
fontName = None
fontHeight_mm = 10.0
fontJustify = JUSTIFY.LEFT
fontKerning_mm = 0.0

def setFillMode(mode : FILLMODE, penSlotFill = None, lineAngle = 0, fillSpacing = 0.75, speed = fillSpeed):
    global fillMode, lineFillAngle, fillPen, fillSpacingCoef, fillSpeed
    fillPen = penSlotFill
    fillMode = mode
    lineFillAngle = lineAngle
    fillSpacingCoef = fillSpacing
    fillSpeed = speed

def setFont(font = None, height_mm = 10.0, justification : JUSTIFY = JUSTIFY.LEFT, kerning_mm = 0.0):
    global fontName, fontHeight_mm, fontJustify, fontKerning_mm
    fontName = font
    fontHeight_mm = height_mm
    fontJustify = justification
    fontKerning_mm = kerning_mm

def _isTtf(font):
    return font is not None and (font.endswith(".ttf") or font.endswith(".otf"))

def text(s, x, y):
    h = fontHeight_mm * UNITS_PER_mm
    k = fontKerning_mm * UNITS_PER_mm
    tol = None
    pen = carriage.getSlot(currentPenIndex)
    if pen != 0:
        tol = pen.pixel_width / 5.0
    if _isTtf(fontName):
        w = easyplot.fonts.ttfTextWidth(s, fontName, h, k)
    else:
        w = easyplot.fonts.hersheyTextWidth(s, h, fontName, k)
    if fontJustify == JUSTIFY.CENTER:
        x -= w / 2
    elif fontJustify == JUSTIFY.RIGHT:
        x -= w
    if _isTtf(fontName):
        boundaries = []
        outlines = []
        for glyph in easyplot.fonts.ttfGlyphContours(s, fontName, h, kerning=k, tolerance=tol):
            for c in glyph:
                outlines.append([(x + px, y + py) for px, py in c] + [(x + c[0][0], y + c[0][1])])
            boundaries.append(easyplot.shape_fill.geometryFromContours(
                [[(x + px, y + py) for px, py in c] for c in glyph]))
        for boundary in boundaries:
            _fillWithGeom(boundary)
        for outline in outlines:
            polyline(outline)
    else:
        for pl in easyplot.fonts.hersheyPolylines(s, h, fontName, k, tolerance=tol):
            polyline([(x + px, y + py) for px, py in pl])

def _fillWithGeom(geom):
    if fillMode == FILLMODE.CONTOUR:
        _fillPolygonContourGeom(geom)
    elif fillMode == FILLMODE.LINE:
        _fillPolygonGeom(geom, lineFillAngle)

def _fillPolygonGeom(geom, angle=0.0):
    global currentPenIndex, fillPen, currentDrawSpeed, fillSpeed
    prevPen = currentPenIndex
    prevSpeed = currentDrawSpeed
    switchPen(fillPen)
    setSpeed(fillSpeed)
    spacing = _fillSpacing()
    if spacing is None:
        switchPen(prevPen)
        setSpeed(prevSpeed)
        return
    spacing *= fillSpacingCoef
    for pl in easyplot.shape_fill.hatchPolylines(geom, spacing, angle):
        polyline(pl)
    switchPen(prevPen)
    setSpeed(prevSpeed)

def _fillPolygonContourGeom(geom):
    global currentPenIndex, fillPen, currentDrawSpeed, fillSpeed
    prevPen = currentPenIndex
    prevSpeed = currentDrawSpeed
    switchPen(fillPen)
    setSpeed(fillSpeed)
    spacing = _fillSpacing()
    if spacing is None:
        switchPen(prevPen)
        setSpeed(prevSpeed)
        return
    spacing *= fillSpacingCoef
    for ring in easyplot.shape_fill.contourGeometry(geom, spacing):
        polyline(ring)
    switchPen(prevPen)
    setSpeed(prevSpeed)

def setSpeed(cm_per_second : int):
    global instructions, currentDrawSpeed
    currentDrawSpeed = cm_per_second
    instructions.append("VS " + str(cm_per_second) + ";")