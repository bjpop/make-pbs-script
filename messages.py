from defaults import *

jobNameQuestion = 'What is the name of your job?'
walltimeQuestion = 'What is the maximum wall time needed by your job? (hh:mm:ss)'
scriptNameQuestion = 'What is the file name of the new script?'
distribCoresQuestion = 'What is the maximum number of CPU cores needed by your job? (1-%d)' % maxCores
isSMPQuestion = 'Is your job SMP? (y/n)'
smpRAMQuestion = 'What is the maximum RAM memory required by your job in gigabytes? (1-%d)' % maxSMPMem
runInSameDirQuestion = 'Do you want the job to run in the same directory from where it is launched? (y/n)'
distribMemQuestion = 'What is the maximum RAM memory required by each PROCESS in your job in gigabytes? (1-%d)' % maxDistribMem
commandQuestion = 'What command do you want your script to run?'
moduleQuestion = 'What modules would you like to be loaded for your script?'

emptyStringMessage = '''
Please enter a non-empty sequence of characters.
'''

parseTimeMessage = '''
The answer to this question must be in the form: hours:minutes:seconds
hours is a sequence of at least one digit (it can be just 0).
minutes is a sequence of one or two digits < 60.
seconds is a sequence of one or two digits < 60.
'''

overwriteFileMessage = '''
The file name you have requested refers to a file that already exists.
If you answer 'y' (yes) to this question then that file will be overwritten
with new data, and the contents of the current version will be lost. If you
don't want to overwrite the file then answer 'n' (no) and you will be prompted
for a new file name.
'''

jobNameMessage = '''
This entry is optional. If you press enter it will not be used.
You can attach a name to a job to remind you of its purpose.
The name will be visible in the job queue, which will help
you to distinguish it from any other jobs that you might be
running or have run previously.
'''

scriptNameMessage = '''
Enter the name of the file for your new PBS script.
Some tips for choosing a good name:
   - Make it meaningful, so it is easy to find in the future.
   - Avoid whitespace in the name.
   - Avoid using the name of an existing file,
     unless you want to overwrite its contents.
'''

timeMessage = '''
The wall time of your job is the time it takes to complete, measured by
a clock on the wall. The time is counted from the moment when the
job begins execution on the compute nodes (not when it is submitted to
the job queue). The time ends when the job completes. If your job runs
out of wall time then it will be automatically terminated. However, you
can request an extension by sending an email to help@vlsci.unimelb.edu.au.
'''

smpMessage = '''
SMP means 'Symmetric multiprocessing'.
See: http://en.wikipedia.org/wiki/Symmetric_multiprocessing.
SMP jobs consist of one multithreaded process. The number of cores available
to an SMP job is limited by the physical number of cores on a single compute
node. On the x86 clusters at VLSCI the maximum cores per node is %d.
Each core shares access to the same pool of memory as every other core in the job.
SMP jobs are not distributed over multiple compute nodes.
''' % coresPerNode

smpMemMessage = '''
Specify how much memory you need for the whole job.
'''

sameDirMessage = '''
All compute jobs start execution within a particular directory.
Most often you want that directory to be the same as the one from where
the job is launched (the directory where you enter the qsub command).
'''

distribMemMessage = '''
Distributed jobs can run over multiple compute nodes, and can consist of
more than one process. The answer to this question should give the maximum
memory per process, not the total memory for the whole job.
'''

coresMessage = '''
A CPU core is one processor.
On bruce.vlsci.unimelb.edu.au each compute node has 2 processor sockets.
Each processor socket has 4 CPU cores.
Therefore each compute node has 8 CPU cores.
All CPU cores on the same compute node share the RAM memory of the node.
'''

commandMessage = '''
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

moduleMessage = '''
The answer to this question should be a possibly empty sequence of module names separated
by whitespace on a single line. For example:

   octave-icc gcc velvet-gcc

Modules provide a convenient way to set up the unix environment for particular programs.
Many programs on bruce.vlsci.unimelb.edu.au have a module file associated with them.
The module file must be loaded before the program can be run. To find out what modules
are available on bruce.vlsci.unimelb.edu.au, type the command 'module avail' at the
unix prompt.
'''

welcomeMessage = '''
Welcome to the PBS script generator.

Please answer the questions which follow.

Press enter after you have typed your answer to each question.

Where possible:
   - Valid responses are shown inside parenthesis ().
   - Default responses are shown inside square brackets [].

If a default answer is available, you can accept it by pressing enter
immediately.

If you don't understand a question then press h (and enter) for help.

You can exit anytime by pressing q (and enter). You will be prompted for
a file name to save a partially complete script.

You can also exit immediately without saving your results to file
by pressing Control-C.

Questions about using the script should be sent to:

    help@vlsci.unimelb.edu.au
'''
