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

# Something wrong with the way the user responded to the question.
class ResponseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

# Something wrong with the action performed on their response.
class ActionError(Exception):
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

# Parse time input.
def hoursMinutesSeconds(input):
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
def nonEmptyString(input):
    if len(input) == 0:
       return None 
    else:
       return input

def yesNo(input):
    normalisedInput = input.lower()
    if normalisedInput in ['yes', 'y', 'true']:
        return True
    elif normalisedInput in ['no', 'n', 'false']:
        return False 
    else:
        raise ResponseError("The answer to this question must be y or n.")

def integerInRange(input,lo,hi):
    if input.isdigit():
        val = int(input)
        if lo <= val and val <= hi:
            return val
    raise ResponseError("The answer to this question must be a number in the range (%d-%d)." % (lo,hi) )

class Script(object):
    def __init__(self):
        self.lines = ['#!/bin/bash\n']
        self.outFile = None
        self.isSMP = False
    def mkJobName(self, msg, name):
        if name != None:
            self.lines.append("# %s\n" % msg)
            self.lines.append("#PBS -N %s\n" % name)
    def mkFileName(self, msg, name):
        if os.path.exists(name) and not askQuestion(overwriteFile):
            raise ActionError("Please choose another file name.")
        try:
            outFile = open(name, "w")
            self.outFile = outFile
        except IOError, e:
            raise ActionError(str(e))
    def mkSMP(self, msg, isSMP):
        if isSMP:
            self.isSMP = True
            self.lines.append("# %s\n" % msg)
            self.lines.append("#PBS -q smp\n")
    def mkProcs(self, msg, num):
        self.lines.append("# %s\n" % msg)
        self.lines.append("#PBS -l procs=%d\n" % num) 
    def mkWallTime(self, msg, time):
        self.lines.append("# %s\n" % msg)
        self.lines.append("#PBS walltime=%s\n" % time)
    def mkSMPMem(self, msg, amount):
        self.lines.append("# %s\n" % msg)
        self.lines.append("#PBS -l mem=%d\n" % amount)
    def mkDistMem(self, msg, amount):
        self.lines.append("# %s\n" % msg)
        self.lines.append("#PBS -l pvmem=%d\n" % amount)
    def mkWorkDir(self, msg, wantWorkDir):
        if wantWorkDir:
            self.lines.append("# %s\n" % msg)
            self.lines.append("cd $PBS_O_WORKDIR\n")
    def mkModules(self, msg, input):
        if input != None:
            self.lines.append("# %s\n" % msg)
            self.lines.append("module load %s\n" % input)
    def mkCommand(self, msg, input):
        if input != None:
            self.lines.append("# %s\n" % msg)
            self.lines.append("%s\n" % input)
 

class Question(object):
     def __init__(self, message, parser, default, action, help, askMe):
         self.message = message
         self.parser = parser
         self.default = default
         self.action = action
         self.help = help
         self.askMe = askMe

script = Script()

scriptName = Question(
    askMe = lambda: True,
    message = 'What is the file name of the new script? [%s]' % defaultScriptName,
    parser  = nonEmptyString,
    default = defaultScriptName, 
    action = script.mkFileName,
    help = '''
Enter the name of the file for your new PBS script.
Some tips for choosing a good name:
   - Make it meaningful, so it is easy to find in the future.
   - Avoid whitespace in the name.
   - Avoid using the name of an existing file, 
     unless you want to overwrite its contents.
'''
)
 
jobName = Question(
    askMe = lambda: True,
    message = 'What is the name of your job? []',
    parser  = nonEmptyString,
    default = '',
    action = script.mkJobName,
    help = '''
This entry is optional. If you press enter it will not be used.
You can attach a name to a job to remind you of its purpose. 
The name will be visible in the job queue, which will help
you to distinguish it from any other jobs that you might be
running or have run previously. 
'''
)
 
isSMP = Question(
    askMe = lambda: True,
    message = 'Is your job SMP? (y/n) [n]', 
    parser  = yesNo,
    default = 'n',
    action = script.mkSMP,
    help = '''
SMP means "Symmetric multiprocessing". 
See: http://en.wikipedia.org/wiki/Symmetric_multiprocessing.
SMP jobs consist of one multithreaded process and use a maximum of 8 CPU cores. 
They are not distributed over multiple compute nodes.
'''
) 

cpuCores = Question(
    askMe = lambda: not script.isSMP,
    message = 'What is the maximum number of CPU cores needed by your job? (1-%d) [%d]' % (maxCores, defaultCores),
    parser = lambda n: integerInRange(n, 1, maxCores),
    default = str(defaultCores),
    action = script.mkProcs,
    help = '''
A CPU core is one processor.
On %s each compute node has %d processor sockets.
Each processor socket has %d CPU cores.
Therefore each compute node has %d CPU cores.
All CPU cores on the same compute node share the RAM memory of the node.
''' % (machineName, socketsPerNode, coresPerSocket, socketsPerNode * coresPerSocket)
)

wallTime = Question(
   askMe = lambda: True,
   message = 'What is the maximum wall time needed by your job? (hh:mm:ss) [%s]' % defaultWallTime,
   parser = hoursMinutesSeconds,
   default = defaultWallTime,
   action = script.mkWallTime,
   help = '''
The wall time of your job is the time it takes to complete, measured by
a clock on the wall. The time is counted from the moment when the
job begins execution on the compute nodes (not when it is submitted to
the job queue). The time ends when the job completes. If your job runs
out of wall time then it will be automatically terminated. However, you
can request an extension by sending an email to %s.
''' % helpEmail
) 

smpMem = Question(
    askMe = lambda: script.isSMP,
    message = 'What is the maximum RAM memory required by your job in gigabytes? (1-%d) [%s]' % (maxSMPMem, defaultSMPMem),
    parser = lambda n: integerInRange(n,1,maxSMPMem),
    default = str(defaultSMPMem),
    action = script.mkSMPMem,
    help = '''
SMP jobs run on only one compute node. Therefore the amount of
memory requested is the total for the entire job. The 
requested memory is shared by all the threads in the job. 
'''
)

distMem = Question(
    askMe = lambda: not script.isSMP,
    message = 'What is the maximum RAM memory required by each PROCESS in your job in gigabytes? (1-%d) [%s]' % (maxDistMem, defaultDistMem),
    parser = lambda n: integerInRange(n,1,maxDistMem),
    default = str(defaultDistMem),
    action = script.mkDistMem,
    help = '''
Distributed jobs can run over multiple compute nodes, and can consist of
more than one process. The answer to this question should give the maximum
memory per process, not the total memory for the whole job. 
'''
)

workDir = Question(
    askMe = lambda: True,
    message = 'Do you want the job to run in the same directory from where it is launched? (y/n) [%s]' % defaultWorkDir,
    parser = yesNo, 
    default = defaultWorkDir,
    action = script.mkWorkDir,
    help = '''
All compute jobs start execution within a particular directory.
Most often you want that directory to be the same as the one from where
the job is launched (the directory where you enter the qsub command).
'''
)

overwriteFile = Question(
    askMe = lambda: True,
    message = 'That file already exists, do you want to overwrite it? (y/n) [n]',
    parser  = yesNo,
    default = 'n',
    action = lambda msg, answer: answer,
    help = '''
The file name you have requested refers to a file that already exists.
If you answer 'y' (yes) to this question then that file will be overwritten 
with new data, and the contents of the current version will be lost. If you 
don't want to overwrite the file then answer 'n' (no) and you will be prompted 
for a new file name.
'''
)

modules = Question(
    askMe = lambda: True,
    message = 'What modules would you like to be loaded for your script? []', 
    parser  = nonEmptyString,
    default = '',
    action = script.mkModules,
    help = '''
The answer to this question should be a possibly empty sequence of module names separated
by whitespace on a single line. For example:

   octave-icc gcc velvet-gcc

Modules provide a convenient way to set up the unix environment for particular programs.
Many programs on %s have a module file associated with them. The module file must be
loaded before the program can be run. To find out what modules are available on
%s, type the command 'module avail' at the unix prompt.
''' % (machineName, machineName)
)

command = Question(
    askMe = lambda: True,
    message = 'What command do you want your script to run? []',
    parser  = nonEmptyString,
    default = '',
    action = script.mkCommand,
    help = '''
Enter the unix command that you want to execute on the compute nodes. For example,
if you wanted to run a distributed NAMD job on the macpf.conf input file, the
command would be:

   mpiexec namd2 macpf.conf 

mpiexec is used for launching distributed parallel jobs. SMP jobs do not need
to be prefixed by mpiexec. 

Note this PBS generation program only allows you to enter a single line command.
If you want to run a multi-line command you will have to edit the generated
PBS script by hand.
'''
)



def askQuestion(q):
    while True:
        response = raw_input(q.message + ' ').strip()
        if len(response) == 0:
           response = q.default
        elif response.lower() in ['h', 'help']:
            print "\n%s\n" % q.help
            continue
        elif response.lower() in ['q', 'quit']:
           raise Terminate()
        try:
           parseOut = q.parser(response)    
           return q.action(q.message, parseOut)
        except (ResponseError, ActionError), e:
           print e 
           continue

def interact():
    # The order of (some) questions is important.
    # The answer to SMP questions determines the questions asked later.
    questions = [ scriptName, jobName, wallTime, isSMP, cpuCores, smpMem, distMem, workDir, modules, command ]
    try:
        for q in questions:
            if q.askMe(): askQuestion(q)
    except Terminate, e:
        print "Exiting the PBS script generator."

def banner(): print "#" * 80

banner()
print '''
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
banner()
print

interact()
if script.outFile != None:
    script.outFile.writelines(script.lines)
    script.outFile.close()
    print "Output written to file: %s" % script.outFile.name 
