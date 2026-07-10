import numpy as np
import easyplot.pen_definition

BOUNDS = [10300, 7650]

def getStrs(plotRelative, penDown):
    return ["PR" if plotRelative else "PA", "PD" if penDown else "PU"]


class _OptimizerState:
    def __init__(self):
        self.plotRelative = False
        self.penDown = False
        self.currentPos = np.array([0, 0])
        self.prevPos = np.array([0, 0])       # position before currentPos
        self.lastTravel = np.array([0, 0]) # direction that ended at currentPos
        self.currentSlot = 0
        self.batch = []
        self.keepBatch = False
        self.out = []
        self.layerBatches = [[] for _ in range(8)]
        self.travelMap = {}


def _validate_instructions(instrs):
    """The instruction list must start with IN; and end with a pen select."""
    if instrs[0] != "IN;" or instrs[-1][:2] != "SP":
        print("invalid start or end (must start with IN; and end with SP;)")
        return False
    return True


def _flush_batch(state, splitLayers):
    """Move the pending batch into the current layer (or main output)."""
    if splitLayers:
        state.layerBatches[state.currentSlot] += state.batch
    else:
        state.out += state.batch
    state.batch = []
    state.keepBatch = False


def _handle_pen_down(state, ins, reduceLifts):
    """PD: mark batch as worth keeping; optionally cancel a redundant PU/PD pair.
    Returns True if the instruction was consumed (lift reduced)."""
    state.penDown = True
    state.keepBatch = True
    if reduceLifts and state.batch and state.batch[-1] == "PU;":
        state.batch.pop()
        return True
    return False


def _handle_pen_select(state, ins, line, carriage, splitLayers):
    """SP: validate the slot and flush the current batch on a pen change.
    Returns False on an invalid pen selection."""
    if len(ins) <= 3:
        if not splitLayers:
            state.batch.append(ins)
        return True
    slot = int(ins[2:-1]) - 1
    if slot not in carriage.getUsedSlots():
        print("invalid or empty pen selection:\n"
              + "instruction line: " + str(line) + "\n"
              + "instruction: " + ins + "\n"
              + "non-empty slots: " + str(carriage.getUsedSlots()))
        return False
    if slot != state.currentSlot:
        if state.keepBatch:
            _flush_batch(state, splitLayers)
        if not splitLayers:
            state.batch.append(ins)
        state.currentSlot = slot
    return True


def _parse_movement(ins):
    """Extract the x,y pair from a movement instruction."""
    return np.array([int(s.strip()) for s in ins[3:-1].split(",")])


def _is_redundant_move(state, matchValue, delta):
    """Skip moves that don't change position."""
    return ((matchValue == "PA" and (state.currentPos == delta).all())
            or (matchValue == "PR" and (delta == 0).all()))


def _check_bounds(state, ins, line, instrs):
    """Verify the new position is inside plotter bounds."""
    if not (0 <= state.currentPos[0] <= BOUNDS[0]
            and 0 <= state.currentPos[1] <= BOUNDS[1]):
        print("out of bounds error:\n"
              + "instruction line: " + str(line) + "\n"
              + "instruction: " + ins + "\n"
              + "position: " + str(state.currentPos))
        print("recent instructions: " + str(instrs[line - 5:line]))
        return False
    return True


def _try_merge(state, matchValue, delta, strs, lineAngleCombinationTolerance):
    """Attempt to merge this move into the previous batched instruction.
    Returns True if merged (instruction consumed)."""
    #try merge
    if matchValue in strs and len(state.batch) > 0 and state.batch[-1][:2] in strs: #no options change needed: attempt merge
        if len(state.batch[-1]) == 3: #last command doesn't move
            state.batch[-1] = state.batch[-1][:2] + " " + str(delta[0]) + "," + str(delta[1]) + ";"
            return True
        travel = state.currentPos - state.prevPos
        if ((not state.penDown)
            or (np.abs(
                np.arctan2(state.lastTravel[1], state.lastTravel[0]) -
                np.arctan2(travel[1], travel[0])
            ) < lineAngleCombinationTolerance)):
            prevDelta = np.array([int(s.strip()) for s in state.batch[-1][3:-1].split(",")])
            combination = travel + prevDelta
            state.batch[-1] = state.batch[-1][:2] + " " + str(int(combination[0])) + "," + str(int(combination[1])) + ";" #merge
            return True
    return False


def _assemble_output(state, carriage, splitLayers):
    """Build the final instruction list, grouping by pen layer if requested."""
    if splitLayers:
        out = ["IN;"]
        state.layerBatches[state.currentSlot] += state.batch
        for i in carriage.getUsedSlots():
            if len(state.layerBatches[i]) > 0:
                out += [str("SP" + str(i + 1) + ";")]
                out += state.layerBatches[i]
        out += ["SP;"]
        return out
    return state.out + state.batch


def optimize(instrs: list, carriage: easyplot.pen_definition.PenCarriage,
            splitLayers=False, reduceLifts=True,
            liftReductionTolerance=3, lineAngleCombinationTolerance=(3.14 * 2) / 180,
            dedupe = False):
    if not _validate_instructions(instrs):
        return []

    state = _OptimizerState()

    for line, ins in enumerate(instrs):
        strs = getStrs(state.plotRelative, state.penDown)
        matchValue = ins[:2]

        if matchValue == "PA":
            state.plotRelative = False
        elif matchValue == "PR":
            state.plotRelative = True
        elif matchValue == "PD":
            if _handle_pen_down(state, ins, reduceLifts):
                continue
        elif matchValue == "PU":
            state.penDown = False
        elif matchValue == "SP":
            if not _handle_pen_select(state, ins, line, carriage, splitLayers):
                return []
            continue
        elif matchValue == "IN":
            if line != 0:
                print("ERROR: `IN;` command should not be used other than to start")
                return []
            if not splitLayers:
                state.batch.append(ins)
            continue
        else:
            state.batch.append(ins)
            continue

        # non-moving pen commands: keep only if they change the current mode
        if "," not in ins:
            if matchValue not in strs:
                state.batch.append(ins)
            continue

        #get movement
        delta = _parse_movement(ins)
        if _is_redundant_move(state, matchValue, delta):
            continue
        if matchValue == "PR":
            delta += state.currentPos
            matchValue = "PA"
        # direction that ended with the previous position (currentPos, pre-update)
        state.lastTravel = state.currentPos - state.prevPos
        state.prevPos = state.currentPos
        if dedupe:
            h = hash((state.currentPos[0], state.currentPos[1]))
            h2 = hash((delta[0], delta[1]))
            connections = state.travelMap.get(h, [])
            if h2 in connections and not state.keepBatch: #TODO this
                print("HI")
                continue
            state.travelMap[h] = connections + [h2]
        state.currentPos = delta
        if not _check_bounds(state, ins, line, instrs):
            return []

        if _try_merge(state, matchValue, delta, strs, lineAngleCombinationTolerance):
            continue
        state.batch.append(ins)

    return _assemble_output(state, carriage, splitLayers)