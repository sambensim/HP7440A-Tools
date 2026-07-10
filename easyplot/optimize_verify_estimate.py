from math import sqrt
from math import floor
import numpy as np
import easyplot.pen_definition
from easyplot.optimize import optimize

UNIT_TO_MS = 0.055 #see benchmarks.txt
PEN_UP_OR_DOWN_MS = 70.005 #see benchmarks.txt
MS_PER_SECOND = 1000
MS_PER_MINUTE = MS_PER_SECOND * 60
MS_PER_HOUR = MS_PER_MINUTE * 60

def OVE(instrs, carriage):
    instrs = optimize(instrs, carriage)
    if len(instrs) > 0:
        print("instructions optimized and verified. estimated time to print: " + _msToTimeStr(estimateTime(instrs)))
        return instrs
    return []


def _msToTimeStr(ms):
    hours = int(floor(ms/MS_PER_HOUR))
    minutes = int(floor((ms % MS_PER_HOUR)/MS_PER_MINUTE))
    seconds = round((ms % MS_PER_MINUTE)/MS_PER_SECOND, 2)
    return ((str(hours) + ":") if hours>0 else "") + str(minutes) + ":" + str(seconds)


def estimateTime(instructions):
    time = 0.0
    plotRelative = False
    currentPosition = [0, 0]
    for ins in instructions:
        if not (ins.startswith("PR") or ins.startswith("PA") or ins.startswith("PU") or ins.startswith("PD")):
            continue
        if ins.startswith("PR"):
            plotRelative = True
        elif ins.startswith("PA"):
            plotRelative = False
        elif ins.startswith("PU") or ins.startswith("PD"):
            time += PEN_UP_OR_DOWN_MS
            if not ("," in ins):
                continue
        parts = ins[3:].split(",")
        dx = int(parts[0])
        dy = int(parts[1].strip().rstrip(";"))
        if plotRelative:
            time += UNIT_TO_MS * sqrt(dx * dx + dy * dy)
            currentPosition[0] += dx
            currentPosition[1] += dy
        else:
            time += UNIT_TO_MS * sqrt((abs(dx) - abs(currentPosition[0])) ** 2 + (abs(dx) - abs(currentPosition[1])) ** 2)
            currentPosition[0] = dx
            currentPosition[1] = dy
    return time