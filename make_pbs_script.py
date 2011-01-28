#!/usr/bin/env python

################################################################################
#
# An interative program to help people write PBS scripts. The goal is to help
# new users write simple PBS scripts. Interaction with the user takes the form
# of a question and answer dialog. The code is designed so that you can easily
# add new questions, response parsers and actions to take for each response.
# It also provides online help for each question asked.
#
# Author: Bernie Pope (bjpope@unimelb.edu.au)
# License: GPL V3: http://www.gnu.org/licenses/gpl.html
# Version: 0.1
# Revision history:
#
# Fri 6 Aug 2010, Version 0.1. Untested. Incomplete.
# Tue 25 Jan 2011, Version 0.2. Made messages and defaults sep modules.
#     moved file name question until the end.
#
################################################################################

import re
import os.path
from defaults import *
from local import *
from messages import *

def addLine (script, line):
    'Adds a new line of text to the accumlated PBS script'
    script.lines.append(line)

def replaceAll(pred, c, new):
    'Replace all items in c which satisfy pred, with new'
    def replacer(x):
        if pred(x):
            return new
        else:
            return x
    return map (replacer, c)

# saves writing some lambdas for simple selector functions.
def const(x):
    return lambda y: x

class Script(object):
    'An accumulator which is passed as a state value throughout the decision tree.'
    pass

def doNothing(state):
    'An action which does nothing.'
    pass

def modifyNothing(result, state):
    'A state modifier which does nothing.'
    pass

def decide(node, state):
    'Walk over the decision graph and update the state.'
    nextNode = node
    while(nextNode):
        result = nextNode.action(state)
        nextNode.modifyState(result, state)
        nextNode = nextNode.selector(result)

class Decision(object):
    '''
    Defines a node in the decision tree. Each node has:

    1. An action to perform when the node is visited.
       An action takes the state as input and returns
       some kind of result value as output. It will often
       have a side-effect as well, such as printing a message
       to the user.

    2. A state modifier. This takes the output of the action
       and the state as input and updates the state, via a
       side-effect.

    3. A selector. This is a function which takes the output of
       the action and chooses the next node to visit in the
       decision tree.
    '''
    def __init__(self, selector, action=doNothing, modifyState=modifyNothing):
        self.selector = selector
        self.action = action
        self.modifyState = modifyState

def askQuestion(question, help, default, parser):
    '''
    Ask the user a question, allowing the user to ask for help
    or quit the application. Default answers can be provided.
    The user's response is checked for correctness by the parser
    argument.
    '''
    if default != None:
        questionStr = '%s [%s] ' % (question, default)
    else:
        questionStr = '%s ' % question
    while True:
        response = raw_input(questionStr).strip()
        if len(response) == 0:
            if default == None:
                continue
            else:
                response = default
        elif response.lower() in ['?', 'h', 'help']:
            print "\n%s\n" % help
            continue
        elif response.lower() in ['q', 'quit']:
           terminate()
        try:
           parseOut = parser(response)
           return parseOut
        except ResponseError, e:
           print e
           continue

class ResponseError(Exception):
    'Something was wrong with the way the user responded to the question.'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Terminate(Exception):
    'The user requested early termination of the dialog.'
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return 'Terminate'

class FileOpen(object):
    'Record the status of a file which we attempted to open.'
    def __init__(self, name, openFile=None, exists=False, error=None):
        self.openFile = openFile
        self.exists = exists
        self.error = error
        self.name = name

def parseYesNo(input):
    'Parse yes/no (true/false) in a variety of ways'
    normalisedInput = input.lower()
    if normalisedInput in ['yes', 'y', 'true']:
        return True
    elif normalisedInput in ['no', 'n', 'false']:
        return False
    else:
        raise ResponseError('The answer to this question must be y or n.')

def parseTime(input):
    'Parse time input in hh:mm:ss format'
    pat = re.match(r"(\d+):(\d{1,2}):(\d{1,2})$", input)
    if pat != None:
       (hours, mins, secs) = pat.groups()
       if int(mins) < 60 and int(secs) < 60:
           return input
    raise ResponseError(parseTimeMessage)

def parseNonEmptyString(input):
    'Accept any non-empty string.'
    if len(input) == 0:
        raise ResponseError(emptyStringMessage)
    else:
        return input

def parseAnyString(input):
    'Aceept any string, including empty ones'
    return input

def parseIntegerInRange(input,lo,hi):
    'Parse an integer in between lo and hi.'
    if input.isdigit():
        val = int(input)
        if lo <= val and val <= hi:
            return val
    raise ResponseError("The answer to this question must be a number in the range (%d-%d)." % (lo,hi))

def overwriteFile():
    'Try to overwrite a file that already exists.'

    def modify(file, script):
        script.file = file

    def select(fileOpenResult):
        if fileOpenResult.openFile:
            return None
        elif fileOpenResult.error:
            print (fileOpen.error)
            return scriptName()

    def act(state):
        name = state.fileName
        try:
            f = open(name, "w")
            return FileOpen(name, openFile=f)
        except IOError, e:
            return FileOpen(name, error=str(e))

    return Decision(select, act, modify)

def askToOverwriteFile():
    'Ask the user if they want to overwrite a file that already exists.'

    def act(state):
        return askQuestion (
            question = 'File %s already exists, do you want to overwrite it?' % state.fileName,
            default = defaultFileOverwrite,
            parser = parseYesNo,
            help = overwriteFileMessage)

    def select(response):
        if response:
            return overwriteFile()
        else:
            return scriptName()

    return Decision(select, act)

def runInSameDir():
    'Ask the user if they want to run the job in the same directory as it was launched.'

    def act(state):
        return askQuestion (
            question = runInSameDirQuestion,
            default = defaultSameDir,
            parser = parseYesNo,
            help = sameDirMessage)

    def modify(response, script):
        if response:
            addLine(script, '# ' + runInSameDirQuestion)
            addLine(script, 'cd $PBS_O_WORKDIR')

    return Decision(const(modules()), act, modify)

def smpRAM():
    'Ask for the maximum memory needed for an SMP job.'

    def act(state):
        return askQuestion (
            question = smpRAMQuestion,
            default = str(defaultSMPMem),
            parser = lambda input: parseIntegerInRange(input,1,maxSMPMem),
            help = smpMemMessage)

    def modify(response, script):
        addLine(script, '# ' + smpRAMQuestion)
        addLine(script, '#PBS -l mem=%dgb' % response)

    return Decision(const(runInSameDir()), act, modify)

def isSMP():
    'Is the job SMP? True means yes, False means it is treated as a distributed job.'

    def act(state):
        return askQuestion (
            question = isSMPQuestion,
            default = defaultIsSMP,
            parser = parseYesNo,
            help = smpMessage)

    def select(response):
        if response:
            return smpRAM()
        else:
            return distribCores()

    def modify(response, script):
        script.lines.append('# Which queue to send your job to?')
        if response:
            addLine(script, '#PBS -q smp')
        else:
            addLine(script, '#PBS -q batch')

    return Decision(select, act, modify)

def distribCores():
    'Ask how many cores are needed by a distributed job.'

    def act(state):
        return askQuestion (
            question = distribCoresQuestion,
            default = str(defaultCores),
            parser = lambda input: parseIntegerInRange(input, 1, maxCores),
            help = coresMessage)

    def modify(response, script):
        addLine(script, '# ' + distribCoresQuestion)
        addLine(script, '#PBS -l procs=%d' % response)

    return Decision(const(distribMem()), act, modify)

def distribMem():
    'Ask how much memory is needed per task in a distributed job'

    def act(state):
        return askQuestion (
            question = distribMemQuestion,
            default = str(defaultDistribMem),
            parser = lambda input: parseIntegerInRange(input, 1, maxDistribMem),
            help = distribMemMessage)

    def modify(response, script):
        addLine(script, '# ' + distribMemQuestion)
        addLine(script, '#PBS -l pvmem=%dgb' % response)

    return Decision(const(runInSameDir()), act, modify)

def walltime():
    'Ask how much walltime is needed for the job.'

    def act(state):
        return askQuestion (
            question = walltimeQuestion,
            default = defaultWallTime,
            parser = parseTime,
            help = timeMessage)

    def modify(time, script):
        addLine(script, '# ' + walltimeQuestion)
        addLine(script, '#PBS -l walltime=%s' % time)

    return Decision(const(isSMP()), act, modify)

def jobName():
    'Ask for the name of the job.'

    def act(state):
        return askQuestion (
            question = jobNameQuestion,
            default = defaultJobName,
            parser = parseAnyString,
            help = jobNameMessage)

    def modify(name, script):
        if len(name) > 0:
            # PBS doesn't allow spaces in the name of a job, replace with undescore
            canonical = ''.join(replaceAll(lambda x: x.isspace(), name, '_'))
            addLine(script, '# ' + jobNameQuestion)
            addLine(script, '#PBS -N %s' % canonical)

    return Decision(const(walltime()), act, modify)

def openFile():
    'Try to open a file for writing, and check if we are overwriting an existing file.'

    def modify(file, script):
       script.file = file

    def select(fileOpenResult):
        if fileOpenResult.openFile:
            return None
        elif fileOpenResult.exists:
            return askToOverwriteFile()
        elif fileOpenResult.error:
            print (fileOpenResult.error)
            return scriptName()

    def act(state):
        name = state.fileName
        if os.path.exists(name):
            return FileOpen(name, exists=True)
        try:
            f = open(name, "w")
            return FileOpen(name, openFile=f)
        except IOError, e:
            return FileOpen(name, error=str(e))

    return Decision(select, act, modify)

def scriptName():
    'Ask for the name of the job script file (not the name of the job).'

    def modify(name, script):
        # replace spaces with underscore to be on the safe side.
        canonical = ''.join(replaceAll(lambda x: x.isspace(), name, '_'))
        script.fileName = canonical

    def act(state):
        return askQuestion (
            question = scriptNameQuestion,
            default = defaultScriptName,
            parser = parseNonEmptyString,
            help = scriptNameMessage)

    return Decision(const(openFile()), act, modify)

def modules():
    'Ask for the modules to load.'

    def act(state):
        return askQuestion (
            question = moduleQuestion,
            default = defaultModules,
            parser = parseAnyString,
            help = moduleMessage)

    def modify(moduleStr, script):
        if len(moduleStr) > 0:
            addLine(script, '# ' + moduleQuestion)
            addLine(script, 'module load ' + moduleStr)

    return Decision(const(command()), act, modify)

def command():
    'Ask for the command to run.'

    def act(state):
        return askQuestion (
            question = commandQuestion,
            default = defaultCommand,
            parser = parseAnyString,
            help = jobNameMessage)

    def modify(commandStr, script):
        if len(commandStr) > 0:
            addLine(script, '# ' + commandQuestion)
            addLine(script, commandStr)

    return Decision(const(None), act, modify)

def terminate(): raise Terminate()

def banner(): print "#" * 80

def tryDecide(decision,script):
    try:
       decide(decision, script)
    except Terminate:
        pass
    except KeyboardInterrupt:
        print
        print "Terminating. Output was NOT written to file."
        exit(0)

def finalise(script):
   tryDecide(scriptName(), script)
   if script.file != None:
        theFile = script.file.openFile
        theFile.write('\n'.join(script.lines))
        theFile.write('\n')
        theFile.close()
        print "Output was written to the file: " + script.file.name

def main():
    banner()
    print welcomeMessage
    banner()
    print '\nh = help, q = quit\n'
    script = Script()
    script.file = None
    script.lines = ['#!/bin/bash']
    tryDecide(jobName(), script)
    finalise(script)

main()
