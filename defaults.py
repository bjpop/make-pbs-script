machineName = 'bruce.vlsci.unimelb.edu.au'
defaultScriptName = 'job.pbs'
defaultCores = 1
maxCores = 512
helpEmail = 'help@vlsci.unimelb.edu.au'
socketsPerNode = 2
coresPerSocket = 4
coresPerNode = coresPerSocket * socketsPerNode
defaultWallTime = '01:00:00'
defaultDistribMem = 1 # gigabytes
maxSMPMem = 144 # gigabytes
defaultSMPMem = 3 # gigabytes
maxDistribMem = 144 # XXX not sure if this is really sane
defaultSameDir = 'y'
defaultReceiveMail = 'y'
defaultFileOverwrite = 'n'
defaultJobName = ''
defaultIsSMP = 'n'
defaultCommand = ''
defaultModules = ''