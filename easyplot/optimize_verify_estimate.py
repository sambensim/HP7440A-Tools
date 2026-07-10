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

def msToTimeStr(ms):
    hours = int(floor(ms/MS_PER_HOUR))
    minutes = int(floor((ms % MS_PER_HOUR)/MS_PER_MINUTE))
    seconds = round((ms % MS_PER_MINUTE)/MS_PER_SECOND, 2)
    return ((str(hours) + ":") if hours>0 else "") + str(minutes) + ":" + str(seconds)

def OVE(instrs, carriage):
    instrs = optimize(instrs, carriage)
    if len(instrs) > 0:
        print("instructions optimized and verified. estimated time to print: " + msToTimeStr(estimateTime(instrs)))
        return instrs
    return []

def sign(n):
    return (n > 0) - (n < 0)




# def optimize(instrs : list, carriage : easyplot.pen_definition.PenCarriage,
#              splitLayers = True, reduceLifts = True,
#              liftReductionTolerance = 3, lineAngleCombinationTolerance = (3.14*2) / 180):
#     if instrs[0] != "IN;" or instrs[-1][:2] != "SP":
#         print("invalid start or end (must start with IN; and end with SP;)")
#         return []
#     plotRelative = False
#     penDown = False
#     out = []
#     currentPos = np.array([0, 0])
#     currentSlot = 0
#     batch = []
#     keepBatch = False
#     layerBatches = [[], [], [], [], [], [], [], []]
#     # prevPos = np.array([0, 0])
    
#     for line, ins in enumerate(instrs):
#         strs = getStrs(plotRelative, penDown)

#         matchValue = ins[:2]
#         if matchValue == "PA":
#             plotRelative = False
#         elif matchValue == "PR":
#             plotRelative = True
#         elif matchValue == "PD":
#             penDown = True
#             keepBatch = True
#             if reduceLifts and batch and batch[-1] == "PU;":
#                 batch.pop()
#                 continue
#         elif matchValue == "PU":
#             penDown = False
#         elif matchValue == "SP":
#             if len(ins) <= 3:
#                 if not splitLayers:
#                     batch.append(ins)
#                 continue
#             slot = int(ins[2:-1])-1
#             if (slot) not in carriage.getUsedSlots():
#                 print("invalid or empty pen selection:\n" + "instruction line: " + str(line) + "\n" + "instruction: " + ins + "\n" + "non-empty slots: " + str(carriage.getUsedSlots()))
#                 return []
#             if slot != currentSlot:
#                 if keepBatch:
#                     if splitLayers:
#                         layerBatches[currentSlot] += batch
#                     else:
#                         out += batch
#                     batch = []
#                     keepBatch = False
#                 if not splitLayers:
#                     batch.append(ins)
#                 currentSlot = slot
#             continue
#         elif matchValue == "IN":
#             if line != 0:
#                 print("ERROR: `IN;` command should not be used other than to start")
#                 return []
#             if not splitLayers:
#                 batch.append(ins)
#             continue
#         else:
#             batch.append(ins)
#             continue
        
#         if "," not in ins:
#             if matchValue not in strs:
#                 batch.append(ins)
#             continue
        
#         #get movement
#         delta = np.array([int(s.strip()) for s in ins[3:-1].split(",")])
#         if ((matchValue == "PA" and (currentPos == delta).all())
#             or (matchValue == "PR" and (delta == 0).all())):
#             continue
#         if matchValue == "PR":
#             delta += currentPos
#             matchValue = "PA"
#         # prevPos.append(currentPos)
#         currentPos = delta
#         if not (0 <= currentPos[0] <= BOUNDS[0] and 0 <= currentPos[1] <= BOUNDS[1]):
#             print("out of bounds error:\n" + "instruction line: " + str(line) + "\n" + "instruction: " + ins + "\n" + "position: " + str(currentPos))
#             print("recent instructions: " + str(instrs[line-5:line]))
#             return []
        
#         #try merge
#         if matchValue in strs and len(batch) > 0 and batch[-1][:2] in strs: #no options change needed: attempt merge
#             if len(batch[-1]) == 3: #last command doesn't move
#                     batch[-1] = batch[-1][:2] + " " + str(delta[0]) + "," + str(delta[1]) + ";"
#                     continue
#             # prevDelta = np.array([int(s.strip()) for s in batch[-1][3:-1].split(",")]) TODO - fix
#             # diff = np.abs(delta - prevDelta)
#             # if ((not penDown)
#             #     or (np.abs(
#             #         np.arctan2(delta[1], delta[0]) - 
#             #         np.arctan2(prevDelta[1], prevDelta[0])
#             #     ) < lineAngleCombinationTolerance)):
#             #     # or (np.abs(np.arctan2(delta[1], delta[0]) - np.arctan2(prevDelta[1], prevDelta[0])) < lineAngleCombinationTolerance)):
#             #     angle = np.arctan2(prevDelta[1], prevDelta[0])
#             #     movementDirectionVector = np.array([np.cos(angle), np.sin(angle)])
#             #     scalarComponent = np.dot(delta, movementDirectionVector)
#             #     componentVector = scalarComponent * movementDirectionVector
#             #     combination = componentVector + prevDelta
#             #     batch[-1] = batch[-1][:2] + " " + str(int(combination[0])) + "," + str(int(combination[1])) + ";" #merge
#             #     continue
#         batch.append(ins)
    
#     if splitLayers:
#         out = ["IN;"]
#         layerBatches[currentSlot] += batch
#         for i in carriage.getUsedSlots():
#             if len(layerBatches[i]) > 0:
#                 out += [str("SP" + str(i+1) + ";")]
#                 out += layerBatches[i]
#         out += ["SP;"]
#     else:
#         out += batch
#     return out

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