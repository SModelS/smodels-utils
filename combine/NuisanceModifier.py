# taken from HiggsAnalysis/CombineLimit

from __future__ import absolute_import

import re
import sys
from math import exp, hypot, log


def appendMap(tmap, k, thing):
    if k in list(tmap.keys()):
        if thing not in tmap[k]:
            tmap[k].append(thing)
    else:
        tmap[k] = [thing]


def fullmatch(regex, line):
    """Performs regex match requiring the full string to match

    Args:
        regex (str or precompiled regex): The pattern to match
        line (str): The line of text to match

    Returns:
        bool: true if a complete match was found, false otherwise
    """
    if isinstance(regex, str):
        compiled = re.compile(regex)
    else:
        compiled = regex
    m = compiled.match(line)
    if m:
        start, stop = m.span()
        if stop - start == len(line):
            return True
    return False


def quadratureAdd(pdf, val1, val2, context=None):
    if type(val1) == list and len(val1) != 2:
        raise RuntimeError(f"{val1} is a list of length != 2")
    if type(val2) == list and len(val2) != 2:
        raise RuntimeError(f"{val2} is a list of length != 2")

    if type(val1) == list and type(val2) == list:
        return [
            quadratureAdd(pdf, val1[0], val2[0], context),
            quadratureAdd(pdf, val1[1], val2[1], context),
        ]
    elif type(val1) == list and type(val2) == float:
        return [
            quadratureAdd(pdf, val1[0], 1.0 / val2, context),
            quadratureAdd(pdf, val1[1], val2, context),
        ]
    elif type(val2) == list and type(val1) == float:
        return [
            quadratureAdd(pdf, 1.0 / val1, val2[0], context),
            quadratureAdd(pdf, val1, val2[1], context),
        ]
    if pdf in ["lnN", "lnU"]:
        if log(val1) * log(val2) < 0:
            raise RuntimeError(
                f"Can't add in quadrature nuisances of pdf {pdf} with values {val1}, {val2} that go in different directions (at {context})"
            )
        ret = exp(hypot(abs(log(val1)), abs(log(val2))))
        return ret if val1 > 1 else 1.0 / ret
    else:
        raise RuntimeError(f"Quadrature add not implemented for pdf {pdf} (at {context})")


def doAddNuisance(datacard, args):
    if len(args) < 5:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit add process channel name pdf value [ options ]")
    (process, channel, name, pdf, value) = args[:5]
    if process != "*":
        cprocess = re.compile(process)
    if channel != "*":
        cchannel = re.compile(channel.replace("+", r"\+"))
    opts = args[5:]
    found = False
    errline = dict([(b, dict([(p, 0) for p in datacard.exp[b]])) for b in datacard.bins])
    for lsyst, nofloat, pdf0, args0, errline0 in datacard.systs:
        if lsyst == name:
            if pdf != pdf0:
                raise RuntimeError(f"Can't add nuisance {name} with pdf {pdf} ad it already exists as {pdf0}")
            found = True
            errline = errline0
    if not found:
        datacard.systs.append([name, False, pdf, [], errline])
    if isinstance(value, (int, float, list)):
        pass
    elif "/" in value:
        value = [float(x) for x in value.split("/")]
    else:
        value = float(value)
    foundChann, foundProc = False, False
    for b in errline.keys():
        if channel == "*" or fullmatch(cchannel, b):
            foundChann = True
            for p in datacard.exp[b]:
                if process == "*" or fullmatch(cprocess, p):
                    foundProc = True
                    if value in [0.0, 1.0]:
                        pass  # do nothing, there's nothing to add
                    elif p in errline[b] and errline[b][p] not in [0.0, 1.0]:
                        if "addq" in opts:
                            errline[b][p] = quadratureAdd(
                                pdf,
                                errline[b][p],
                                value,
                                context=f"nuisance edit add, args = {args}",
                            )
                        elif "overwrite" in opts:
                            errline[b][p] = value
                        else:
                            raise RuntimeError(
                                "Can't add nuisance with args = %s for bin %s, process %s: found existing non-null value %s, and no option 'addq' or 'overwrite' given"
                                % (args, b, p, errline[b][p])
                            )
                    else:
                        errline[b][p] = value
    if not foundChann:
        sys.stderr.write(f"Warning: no channel found matching nuisance edit add with args = {args}\n")
    if not foundProc:
        sys.stderr.write(f"Warning: no process found matching nuisance edit add with args = {args}\n")


def doDropNuisance(datacard, args):
    if len(args) < 3:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit drop process channel name [ options ]")
    (process, channel, name) = args[:3]
    if process != "*":
        cprocess = re.compile(process)
    if channel != "*":
        cchannel = re.compile(channel.replace("+", r"\+"))
    opts = args[3:]
    foundProc = False
    for lsyst, nofloat, pdf, args0, errline in datacard.systs:
        if fullmatch(name, lsyst):
            for b in errline.keys():
                if channel == "*" or fullmatch(cchannel, b):
                    # if channel != "*": foundProc = False
                    for p in datacard.exp[b]:
                        if process == "*" or fullmatch(cprocess, p):
                            foundProc = True
                            errline[b][p] = 0
            # if channel != "*" and foundProc == False:
            #    if "ifexists" not in opts:
            #        raise RuntimeError, "Error: nuisance edit drop %s found nothing in channel %s" % (args, channel)
            #    else:
            #        sys.stderr.write("Warning1: nuisance edit drop %s found nothing in channel %s\n" % (args, channel))
    if not foundProc and channel != "*":
        if "ifexists" not in opts:
            raise RuntimeError(f"Error: nuisance edit drop {args} found nothing")
        else:
            sys.stderr.write(f"Warning2: nuisance edit drop {args} found nothing\n")


def checkRenameSafety(id, datacard, newname):
    lsyst, nofloat, pdf0, args0, errline0 = datacard.systs[id]
    for id2 in datacard.systIDMap[newname]:
        if id == id2:
            continue
        lsyst2, nofloat2, pdf02, args02, errline02 = datacard.systs[id2]
        if pdf0 == pdf02 and pdf0 != "param":
            return True
        if pdf0 == "param":
            if pdf02 != "param":
                if abs(float(args0[0])) > 1e-6 or abs(float(args0[1]) - 1) > 1e-6:
                    return False
            else:
                if abs(float(args0[0]) - float(args02[0])) > 1e-6 or abs(float(args0[1]) - float(args02[1])) > 1e-6:
                    return False
        else:
            if pdf02 == "param":
                if abs(float(args02[0])) > 1e-6 or abs(float(args02[1]) - 1) > 1e-6:
                    return False
    return True


def doRenameNuisance(datacard, args):
    vetoTypes = ["flatParam", "constr", "trG", "gmN"]
    isGlobal = False
    if len(args) == 2:
        (oldname, newname) = args[:2]
        isGlobal = True
    else:
        (process, channel, oldname, newname) = args[:4]
        if process != "*":
            cprocess = re.compile(process)
        if channel != "*":
            cchannel = re.compile(channel.replace("+", r"\+"))
        opts = args[4:]

    # print "map before ->", datacard.systIDMap
    # for dcs in datacard.systs: print " --> ", dcs
    if oldname in list(datacard.systIDMap.keys()):
        for id in list(datacard.systIDMap[oldname]):
            # print " when considering id %d, the map ->"%id, datacard.systIDMap
            # print oldname, " ID = ", id
            lsyst, nofloat, pdf0, args0, errline0 = datacard.systs[id]
            if pdf0 in vetoTypes:
                raise RuntimeError(
                    "Error: Can only use nuisance edit rename with param, shape(N) or lnN type nuisances currently - you should rename the parameter in your input workspace/datacard."
                )
            if newname in list(datacard.systIDMap.keys()):
                if not checkRenameSafety(id, datacard, newname):
                    raise RuntimeError(f"Error: Cannot rename {oldname} to {newname}, which exists and is incompatible")

            if isGlobal:  # easy case
                # print " global command, ", " looking at "
                # for dcs in datacard.systs: print " --> ", dcs
                datacard.systs[id][0] = newname
                appendMap(datacard.systIDMap, newname, id)
                if "param" in pdf0:
                    datacard.systematicsParamMap[oldname] = newname
                if "shape" in pdf0 or "lnN" in pdf0:
                    for b in errline0.keys():
                        for p in datacard.exp[b].keys():
                            if errline0[b][p] != "-" and errline0[b][p] != 0.0:
                                datacard.systematicsShapeMap[newname, b, p] = oldname
                            # print " for ", b,p,oldname,newname, errline0[b][p],
                    # print ""
                datacard.systIDMap[oldname].remove(id)
            else:  # more tricky
                # print " local command, ", " looking at a ", pdf0, " at id=",id
                if pdf0 == "param":
                    continue
                # for dcs in datacard.systs: print " --> ", dcs
                errline2 = dict([(b, dict([(p, 0) for p in datacard.exp[b]])) for b in datacard.bins])
                found = False
                if newname in list(datacard.systIDMap.keys()):
                    for id2 in datacard.systIDMap[newname]:
                        if id2 == id:
                            continue
                        lsyst2, nofloat2, pdf2, args2, errline2b = datacard.systs[id2]
                        if pdf2 == pdf0:
                            found = True
                            errline2 = errline2b
                if not found:
                    datacard.systs.append([newname, nofloat, pdf0, args0, errline2])
                    datacard.add_syst_id(newname)

                foundChan = False
                foundProc = False
                for b in errline0.keys():
                    if channel == "*" or fullmatch(cchannel, b):
                        foundChan = True
                        for p in datacard.exp[b].keys():
                            if process == "*" or fullmatch(cprocess, p):
                                foundProc = True
                                errline2[b][p] = errline0[b][p]
                                errline0[b][p] = 0
                                if "shape" in pdf0:
                                    datacard.systematicsShapeMap[newname, b, p] = oldname
                        if not foundProc and "ifexists" not in opts:
                            raise RuntimeError(
                                "Error: nuisance edit rename %s found no corresponding process in channel %s  (and option 'ifexists' not specified)"
                                % (args, channel)
                            )
                if not foundChan and "ifexists" not in opts:
                    raise RuntimeError(f"Error: no channel found matching nuisance edit rename with args = {args} (and option 'ifexists' not specified)\n")
                # if the result was to rename across everything, meaning 0s get put there, remove that id from the map
                # Double check if all elements are actually zeroes (int and float), not something else.
                # If an element is a list of two floats, it is an asymmetric log-normal uncertainty.
                allzeroes = True
                for a in errline0.keys():
                    for b in errline0[a].keys():
                        if type(errline0[a][b]) != int and type(errline0[a][b]) != float:
                            allzeroes = allzeroes and False
                        # elif errline0[a][b] != 0.0 and errline0[a][b] != 0: allzeroes = allzeroes and False
                        elif abs(errline0[a][b]) > 1e-6:
                            allzeroes = allzeroes and False
                # if abs( sum([errline0[a][b] for a in errline0.keys() for b in errline0[a].keys()]) ) < 1e-6 : datacard.systIDMap[oldname].remove(id)
                if allzeroes:
                    datacard.systIDMap[oldname].remove(id)
            # print " after considering id %d, the map ->"%id, datacard.systIDMap
        if len(datacard.systIDMap[oldname]) == 0:
            datacard.systIDMap.pop(oldname)

    else:
        raise RuntimeError(f"No nuisance parameter found with name {oldname} in the datacard")
    # print " map after -> " , datacard.systIDMap
    # for dcs in datacard.systs: print " --> ", dcs


def doChangeNuisancePdf(datacard, args):
    if len(args) < 2:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit changepdf name newpdf [ options ]")
    (name, newpdf) = args[:2]
    found = False
    for i, (lsyst, nofloat, pdf, args0, errline) in enumerate(datacard.systs):
        if fullmatch(name, lsyst):
            found = True
            ok = False
            if newpdf == pdf:
                continue
            if pdf in ["lnN", "lnU"]:
                if newpdf in ["lnN", "lnU"]:
                    ok = True
                elif newpdf in ["trG", "unif", "dFD", "dFD2"]:
                    ok = True
                    for b in errline.keys():
                        for p in errline[b].keys():
                            errline[b][p] = log(errline[b][p]) if errline[b][p] not in [0.0, 1.0] else 0.0
            elif pdf in ["trG", "unif", "dFD", "dFD2"]:
                if newpdf in ["trG", "unif", "dFD", "dFD2"]:
                    ok = True
                elif newpdf in ["lnN", "lnU"]:
                    ok = True
                    for b in errline.keys():
                        for p in errline[b].keys():
                            errline[b][p] = exp(errline[b][p]) if errline[b][p] not in [0.0, 1.0] else 0.0
            elif "shape" in pdf:
                if "shape" in newpdf:
                    ok = True
            if ok:
                datacard.systs[i][2] = newpdf
            else:
                raise RuntimeError(f"I can't convert pdf {lsyst} from pdf {pdf} to {newpdf}")
    if not found:
        sys.stderr.write(f"Warning: no pdf found for changepdf with args {args}\n")


def doMergeNuisance(datacard, args):
    if len(args) < 4:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit merge process channel name1 name2 [ options ]")
    (process, channel, name1, name2) = args[:4]
    if process != "*":
        cprocess = re.compile(process)
    if channel != "*":
        cchannel = re.compile(channel.replace("+", r"\+"))
    opts = args[4:]
    foundProc = False

    for lsyst2, nofloat2, pdf2, args02, errline2 in datacard.systs:
        if fullmatch(name2, lsyst2):
            for b in errline2.keys():
                if channel == "*" or fullmatch(cchannel, b):
                    for p in datacard.exp[b]:
                        if process == "*" or fullmatch(cprocess, p):
                            foundProc = True
                            doAddNuisance(
                                datacard,
                                [p + "$", b + "$", name1, pdf2, errline2[b][p], "addq"],
                            )
                            errline2[b][p] = 0

    if not foundProc and channel != "*":
        if "ifexists" not in opts:
            raise RuntimeError(f"Error: nuisance edit merge {args} found nothing")
        else:
            sys.stderr.write(f"Warning2: nuisance edit merge {args} found nothing\n")


def doSplitNuisance(datacard, args):
    if len(args) < 7:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit split process channel oldname newname1 newname2 value1 value2")
    (process, channel, oldname, newname1, newname2, value1, value2) = args[:7]
    if process != "*":
        cprocess = re.compile(process)
    if channel != "*":
        cchannel = re.compile(channel.replace("+", r"\+"))
    opts = args[7:]
    foundProc = False
    for lsyst, nofloat, pdf, args0, errline in datacard.systs:
        if fullmatch(oldname, lsyst):
            for b in errline.keys():
                if channel == "*" or fullmatch(cchannel, b):
                    for p in datacard.exp[b]:
                        if process == "*" or fullmatch(cprocess, p):
                            foundProc = True
                            if errline[b][p] not in [0.0, 1.0]:
                                doAddNuisance(datacard, [p, b, newname1, pdf, value1, "overwrite"])
                                doAddNuisance(datacard, [p, b, newname2, pdf, value2, "overwrite"])
                            errline[b][p] = 0

    if not foundProc and channel != "*":
        if "ifexists" not in opts:
            raise RuntimeError(f"Error: nuisance edit split {args} found nothing")
        else:
            sys.stderr.write(f"Warning2: nuisance edit split {args} found nothing\n")


def doFreezeNuisance(datacard, args):
    if len(args) < 1 or len(args) > 2:
        raise RuntimeError("Missing arguments: the syntax is: nuisance edit freeze name [ifexists] (name can be a pattern)")
    pat = re.compile("^" + args[0] + "$")
    opts = args[1:]
    found = []

    # first check in the list of paramters as flatParam, rateParam or discretes not included in datacard.systs (smaller usually)
    for lsyst in list(datacard.flatParamNuisances.keys()) + list(datacard.rateParamsOrder) + datacard.discretes + list(datacard.extArgs.keys()):
        if fullmatch(pat, lsyst):
            datacard.frozenNuisances.add(lsyst)
            found.append(lsyst)

    if not found:
        for lsyst, nofloat, pdf, args0, errline in datacard.systs:
            if fullmatch(pat, lsyst):
                datacard.frozenNuisances.add(lsyst)
                found.append(lsyst)

    # Warn user/exit
    if not found:
        if "ifexists" not in opts:
            raise RuntimeError(f"Error: nuisance edit freeze {args[0]} found nothing")
        else:
            sys.stderr.write(f"Warning2: nuisance edit freeze {args[0]} found nothing\n")


def doFlipNuisance(datacard, args):
    if len(args) < 3:
        raise RuntimeError(
            "Missing arguments: the syntax is: nuisance edit flip process channel name [options: ifexists, p2n (only positive to negative), n2p (only negative to positive)]"
        )
    (process, channel, name) = args[:3]
    if process != "*":
        cprocess = re.compile(process)
    if channel != "*":
        cchannel = re.compile(channel.replace("+", r"\+"))
    opts = args[3:]
    if "n2p" not in opts and "p2n" not in opts:
        raise RuntimeError(f"Error: nuisance edit flip {args} missed option n2p and/or p2n")
    foundProc = False
    for lsyst, nofloat, pdf, args0, errline in datacard.systs:
        if fullmatch(name, lsyst):
            if pdf not in ["lnN"]:
                raise RuntimeError(f"Error: nuisance edit flip {args} currently not support pdftype {pdf}")
            for b in errline.keys():
                if channel == "*" or fullmatch(cchannel, b):
                    for p in datacard.exp[b]:
                        if process == "*" or fullmatch(cprocess, p):
                            foundProc = True
                            if errline[b][p] not in [0.0, 1.0]:
                                if type(errline[b][p]) is list:
                                    if errline[b][p][0] < 1:
                                        if "p2n" in opts:
                                            errline[b][p][0] = 1.0 / errline[b][p][0]
                                            errline[b][p][1] = 1.0 / errline[b][p][1]
                                    elif errline[b][p][0] > 1:
                                        if "n2p" in opts:
                                            errline[b][p][0] = 1.0 / errline[b][p][0]
                                            errline[b][p][1] = 1.0 / errline[b][p][1]
                                else:
                                    if errline[b][p] > 1:
                                        if "p2n" in opts:
                                            errline[b][p] = 1.0 / errline[b][p]
                                    elif errline[b][p] < 1:
                                        if "n2p" in opts:
                                            errline[b][p] = 1.0 / errline[b][p]

    if not foundProc and channel != "*":
        if "ifexists" not in opts:
            raise RuntimeError(f"Error: nuisance edit flip {args} found nothing")
        else:
            sys.stderr.write(f"Warning2: nuisance edit flip {args} found nothing\n")


def doEditNuisance(datacard, command, args):
    if command == "add":
        doAddNuisance(datacard, args)
    elif command == "drop":
        doDropNuisance(datacard, args)
    elif command == "rename":
        doRenameNuisance(datacard, args)
    elif command == "changepdf":
        doChangeNuisancePdf(datacard, args)
    elif command == "merge":
        doMergeNuisance(datacard, args)
    elif command == "split":
        doSplitNuisance(datacard, args)
    elif command == "freeze":
        doFreezeNuisance(datacard, args)
    elif command == "flip":
        doFlipNuisance(datacard, args)
    else:
        raise RuntimeError(f"Error, unknown nuisance edit command {command} (args {args})")
