from PIL import Image
import numpy as np
import math
import easyplot.pen_definition

BOUNDS = (10300, 7650)

def preview(instrs: list, carriage: easyplot.pen_definition.PenCarriage):
    print("creating preview")
    plotRelative = False
    cPos = (0, 0)
    penDown = False
    currentPen = None
    arr = np.full((BOUNDS[1], BOUNDS[0], 3), 255, dtype=np.uint8)
    for ins in instrs:
        matchValue = ins[:2]
        if matchValue == "PA":
            plotRelative = False
        elif matchValue == "PR":
            plotRelative = True
        elif matchValue == "PD":
            if currentPen == None:
                print("ERROR: No pen selected")
                return
            if not penDown:
                penDown = True
                if currentPen:
                    dot(cPos[0], cPos[1], arr, currentPen)
        elif matchValue == "PU":
            penDown = False
        elif matchValue == "SP":
            if len(ins) > 3 and ins != "SP0;" and ins != "SP 0;":
                currentPen = carriage.getSlot(int(ins[2:-1]) - 1)
                if not hasattr(currentPen, "_sub_cached"):
                    currentPen._sub_cached = np.round(
                        (255 - np.array(currentPen.color, dtype=np.float32)) * currentPen.DARKNESS
                    ).astype(np.int16)
        if "," in ins:
            delta = [int(s.strip()) for s in ins[2:-1].split(",")]
            nextPos = delta if not plotRelative else (delta[0] + cPos[0], delta[1] + cPos[1])
            if penDown:
                line(cPos[0], cPos[1], nextPos[0], nextPos[1], arr, currentPen)
            cPos = nextPos
    out = Image.fromarray(arr)
    out.show()

def line(x1, y1, x2, y2, img, pen: easyplot.pen_definition.PenDefinition):
    height, width = img.shape[:2]
    half_w = pen.pixel_width / 2.0
    min_x = max(int(math.floor(min(x1, x2) - half_w)), 0)
    max_x = min(int(math.ceil(max(x1, x2) + half_w)), width - 1)
    min_y = max(int(math.floor(min(y1, y2) - half_w)), 0)
    max_y = min(int(math.ceil(max(y1, y2) + half_w)), height - 1)
    if min_x > max_x or min_y > max_y:
        return
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    ys, xs = np.ogrid[min_y:max_y + 1, min_x:max_x + 1]
    if length_sq == 0:
        dist = np.hypot(xs - x1, ys - y1)
    else:
        t = ((xs - x1) * dx + (ys - y1) * dy) / length_sq
        t = np.clip(t, 0.0, 1.0)
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        dist = np.hypot(xs - closest_x, ys - closest_y)
    mask = dist <= half_w
    region = img[min_y:max_y + 1, min_x:max_x + 1]
    sub = np.round((255 - np.array(pen.color, dtype=np.float32)) * pen.DARKNESS).astype(np.int16)
    region[mask] = np.clip(region[mask].astype(np.int16) - sub, 0, 255).astype(np.uint8)

def dot(x, y, img, pen: easyplot.pen_definition.PenDefinition):
    height, width = img.shape[:2]
    radius = pen.pixel_width / 2.0 * 1.2
    min_x = max(int(math.floor(x - radius)), 0)
    max_x = min(int(math.ceil(x + radius)), width - 1)
    min_y = max(int(math.floor(y - radius)), 0)
    max_y = min(int(math.ceil(y + radius)), height - 1)
    if min_x > max_x or min_y > max_y:
        return
    ys, xs = np.mgrid[min_y:max_y + 1, min_x:max_x + 1]
    dist = np.hypot(xs - x, ys - y)
    mask = dist <= radius
    region = img[min_y:max_y + 1, min_x:max_x + 1]
    # darkness 1.0: subtract the full complement, clamp at 0
    sub = np.round(255 - np.array(pen.color, dtype=np.float32)).astype(np.int16)
    region[mask] = np.clip(region[mask].astype(np.int16) - sub, 0, 255).astype(np.uint8)