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
#
################################################################################


import re
import os.path

machineName = 'bruce.vlsci.unimelb.edu.au'
defaultScriptName = 'job.pbs'
defaultCores = 1 
maxCores = 512
helpEmail = 'help@vlsci.unimelb.edu.au'
socketsPerNode = 2
coresPerSocket = 4
defaultWallTime = '01:00:00'
defaultSMPMem = 24 # gigabytes
defaultDistMem = 1 # gigabytes
maxSMPMem = 144 # gigabytes
maxDistMem = 144 # XXX not sure if this is really sane
defaultWorkDir = 'y'
defaultReceiveMail = 'y'
defaultFileOverwrite = 'n'
defaultJobName = ''

class Script(object): pass

def doNothing(state):
    pass

def modifyNothing(result, state):
    pass

class Action(object):
    def __init__(self, selector, action=doNothing, modifyState=modifyNothing):
        self.selector = selector
        self.action = action
        self.modifyState = modifyState
   
    def decide(self, state):
        result = self.action(state)
        self.modifyState(result, state)
        self.selector(result).decide(state)


def askQuestion(question, help, default, parser, state):
    while True:
        response = raw_input(question + ' ').strip()
        if len(response) == 0:
            if default == None:
                continue
            else:
                response = default 
        elif response.lower() in ['h', 'help']:
            print "\n%s\n" % help
            continue
        elif response.lower() in ['q', 'quit']:
           raise Terminate()
        try:
           parseOut = parser(response)    
           return parseOut
        except ResponseError, e:
           print e 
           continue

# Something wrong with the way the user responded to the question.
class ResponseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

# User requested early termination of the dialog.
class Terminate(Exception):
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return 'Terminate'

def parseYesNo(input):
    normalisedInput = input.lower()
    if normalisedInput in ['yes', 'y', 'true']:
        return True
    elif normalisedInput in ['no', 'n', 'false']:
        return False 
    else:
        raise ResponseError("The answer to this question must be y or n.")

# Parse time input.
def parseTime(input):
    pat = re.match(r"(\d+):(\d{1,2}):(\d{1,2})$", input)
    if pat != None: 
       (hours, mins, secs) = pat.groups()
       if int(mins) < 60 and int(secs) < 60:
           return input
    raise ResponseError('''
The answer to this question must be in the form: hours:minutes:seconds
hours is a sequence of at least one digit (it can be just 0).
minutes is a sequence of one or two digits < 60.
seconds is a sequence of one or two digits < 60.
'''
)

# Accept any non-empty string.
def parseNonEmptyString(input):
    return input

def parseIntegerInRange(input,lo,hi):
    if input.isdigit():
        val = int(input)
        if lo <= val and val <= hi:
            return val
    raise ResponseError("The answer to this question must be a number in the range (%d-%d)." % (lo,hi) )


class FileOpen(object):
    def __init__(self, name, file=None, exists=False, error=None):
        self.file = file
        self.exists = exists
        self.error = error 
        self.name = name

def fileExists (name):
    return Decision(
    question = 'File %s already exists, do you want to overwrite it? [%s]' % (name, defaultFileOverwrite),
    modifyState = setScriptName, 
    selector = overwriteFileSelector,
    help = '''
'''
)

def askToOverwriteFile():

    overwriteHelp = '''
The file name you have requested refers to a file that already exists.
If you answer 'y' (yes) to this question then that file will be overwritten
with new data, and the contents of the current version will be lost. If you
don't want to overwrite the file then answer 'n' (no) and you will be prompted
for a new file name.
'''

    def overwriteQuestion(script):
        return askQuestion (
            question = 'File %s already exists, do you want to overwrite it? [%s]' % (script.fileName, defaultFileOverwrite),
            default = defaultFileOverwrite, 
            parser = parseYesNo,
            help = overwriteHelp,
            state = script)

    def overwriteSelector(response):
        if response:
            return foobar
        else:
            return scriptName() 

    return Action(action=overwriteQuestion, selector=overwriteSelector)

def jobName():

    jobNameHelp = '''
This entry is optional. If you press enter it will not be used.
You can attach a name to a job to remind you of its purpose.
The name will be visible in the job queue, which will help
you to distinguish it from any other jobs that you might be
running or have run previously.
'''
    def jobNameQuestion(s):
        return askQuestion (
            question = 'What is the name of your job? []',
            default = defaultJobName,
            parser = parseNonEmptyString,
            help = jobNameHelp,
            state = s)

    def setJobName(name, script):
        script.JobName = name

    return Action(
        selector = lambda _ : foobar, 
        action = jobNameQuestion,
        modifyState = setJobName)

def openFile(): 
    def setScriptFile(file, script):
       script.file = file

    def openFileSelector (fileOpenResult):
        if fileOpenResult.file:
            return jobName()
        elif fileOpenResult.exists:
            return askToOverwriteFile() 
        elif fileOpenResult.error: 
            print (fileOpen.error)
            return scriptName()

    def openFile(script):
        name = script.fileName
        if os.path.exists(name):
            return FileOpen(name, exists=True) 
        try:
            f = open(name, "w")
            return FileOpen(name, file=f)
        except IOError, e:
            return FileOpen(name, error=str(e))

    return Action(
        selector = openFileSelector, 
        action = openFile,
        modifyState = setScriptFile)


def scriptName(): 

    scriptNameHelp = '''
Enter the name of the file for your new PBS script.
Some tips for choosing a good name:
   - Make it meaningful, so it is easy to find in the future.
   - Avoid whitespace in the name.
   - Avoid using the name of an existing file,
     unless you want to overwrite its contents.
'''

    def setScriptName(name, script):
        script.fileName = name 

    def scriptNameQuestion(s):
        return askQuestion (
            question = 'What is the file name of the new script? [%s]' % defaultScriptName,
            default = defaultScriptName,
            parser = parseNonEmptyString,
            help = scriptNameHelp,
            state = s)

    return Action (
        selector = lambda _ : openFile(),
        action = scriptNameQuestion,
        modifyState = setScriptName) 

def terminate():
    raise Terminate()

def banner(): print "#" * 80

welcomeMessage = ''' 
Welcome to the PBS script generator.

Please answer the questions which follow.

Where possible:
   - Valid responses are shown inside parenthesis ().
   - Default responses are shown inside square brackets [].

Press enter after you have typed your answer to the question.

Where possible you can accept the default answer to a 
question by pressing enter immediately.

If you don't understand a question then press h (and enter) for help.

You can exit anytime by pressing q (and enter). If you exit early 
a partial script will be saved to file.

Questions about using the script should be sent to: 

    help@vlsci.unimelb.edu.au
'''

def finalise(script):
    print "finalise"

def main():
    banner()
    print welcomeMessage
    banner()
    print
    script = Script()
    try:
        scriptName().decide(script)
    except Terminate:
        finalise(script) 

main()
