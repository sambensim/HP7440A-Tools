UNITS_PER_mm = 1.0 / 0.025

class PenDefinition:
    # DARKNESS : float = 0.7
    DARKNESS : float = 0.9
    # DARKNESS : float = 1
    def __init__(self, r : int, g : int, b : int, width_mm : float):
        self.color = (r, g, b)
        self.width_mm = width_mm
        self.pixel_width = width_mm * UNITS_PER_mm

MICRON_LIGHT_COOL_GRAY_01 = PenDefinition(131, 126, 112, 0.25)
MICRON_LIGHT_COOL_GRAY_05 = PenDefinition(131, 126, 112, 0.45)
MICRON_LIGHT_COOL_GRAY_08 = PenDefinition(131, 126, 112, 0.50)
MICRON_LIGHT_COOL_GRAY_10 = PenDefinition(131, 126, 112, 0.60)
MICRON_COOL_GRAY_01 = PenDefinition(77, 78, 71, 0.25)
MICRON_COOL_GRAY_05 = PenDefinition(77, 78, 71, 0.45)
MICRON_COOL_GRAY_08 = PenDefinition(77, 78, 71, 0.50)
MICRON_COOL_GRAY_10 = PenDefinition(77, 78, 71, 0.60)
MICRON_BLACK_05 = PenDefinition(40, 40, 39, 0.45)
MICRON_BLACK_10 = PenDefinition(40, 40, 39, 0.6)
MICRON_SEPIA_05 = PenDefinition(61, 54, 45, 0.45)
MICRON_BLUE_05 = PenDefinition(16, 87, 156, 0.45)
MICRON_GREEN_05 = PenDefinition(0, 255, 0, 0.45)
MICRON_RED_05 = PenDefinition(255, 0, 0, 0.45)
MICRON_PURPLE_05 = PenDefinition(61, 51, 93, 0.45)
MICRON_ROSE_05 = PenDefinition(0, 0, 0, 0.45)
MICRON_BROWN_05 = PenDefinition(0, 0, 0, 0.45)

class PenCarriage:
    def __init__(self, penArray = [0, 0, 0, 0, 0, 0, 0, 0]):
        self.slots = penArray
    def loadPen(self, slot : int, pen : PenDefinition):
        if not (0 <= slot <= 7):
            print("ERROR: pen slot " + str(slot) + " doesn't exist")
            return
        if self.slots[slot] != 0:
            print("ERROR: pen slot " + str(slot) + " is empty")
            return
        else:
            self.slots[slot] = pen
    def getUsedSlots(self):
        return [i for i, pen in enumerate(self.slots) if pen != 0]
    def getSlot(self, slot : int):
        if not (0 <= slot <= 7):
            print("ERROR: pen slot " + str(slot) + " doesn't exist")
            return
        return self.slots[slot]

ALL_BLACK = PenCarriage([MICRON_BLACK_05 for i in range(8)])