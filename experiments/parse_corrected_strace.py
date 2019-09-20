from collections import defaultdict

INPUT_DIR = "/mnt/hdd/mariadb_strace/"
INPUT_FILE =  INPUT_DIR + "corrected_binlog.strace"

def getPIDs():
    f = open(INPUT_FILE, 'r')
    pids = set()
    for line in f:
        pids.add(line.split(' ')[0])
    f.close()
    return pids

# Total 33 processes, single parent, all children
def getProcessTree():
    # Look for the 'clone' system call
    f = open(INPUT_FILE, 'r')
    parents = {}
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'clone':
            parent_pid = line.split(' ')[0]
            try:
                child_pid = line.split('= ')[1]
                child_pid = child_pid.split('\n')[0]
            except:
                continue
            children = parents.get(parent_pid)
            if children:
                children.append(child_pid)
            else:
                children = [child_pid]
            parents[parent_pid] = children
    f.close()
    return parents

def getOpenedFilenames():
    f = open(INPUT_FILE, 'r')
    filenames = set()
    for line in f:
        pid = line.split(' ')[0]
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'open':
            filepath = line.split('"')[1]
            # if filepath.startswith('/'):
            #     continue
            filenames.add(filepath)
            print pid, filepath
    f.close()
    return filenames

def getSysCalls():
    f = open(INPUT_FILE, 'r')
    syscalls = set()
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        syscalls.add(syscall_substr)
    f.close()
    return syscalls

# To check if clone is called with CLONE_FILES
# Looks like CLONE_FILES flag is always passed during cloning
# That means the thread ID is not important, all threads share the same
# file descriptor table
def cloneFilesAlways():
    f = open(INPUT_FILE, 'r')
    total_clones = 0
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'clone':
            total_clones += 1
            if 'CLONE_FILES' not in line:
                print line
    print total_clones
    f.close()

# Relevant I/O calls:
#  'close': close a file (descriptor)
#  'fcntl': F_DUPFD_CLOEXEC
#  'io_submit',
#  'lseek',
#  'open',
#  'openat',
#  'pread64',
#  'pwrite64',
#  'read',
#  'write'

# Maybe imp:
#  'fdatasync',
#  'fsync',
def getIOCallsForFiles():
    f = open(INPUT_FILE, 'r')
    fdToFilenameMap = {}
    filenameToReadSizes = defaultdict(list)
    filenameToWriteSizes = defaultdict(list)
    lineno = 0
    for line in f:
        try:
            lineno += 1
            syscall = line.split(' ')[1]
            syscall = syscall.split('(')[0]

            if syscall == 'open' or syscall == 'openat':
                filename = line.split('"')[1]
                fd = line.split('= ')[1]
                fd = fd.split('\n')[0]
                if '-1' in fd:
                    continue
                if fdToFilenameMap.has_key(fd):
                    print "open/openat: fd: ", fd, " already exists: ", fdToFilenameMap[fd]
                    print "lineno: ", lineno
                    return
                fdToFilenameMap[fd] = filename
                continue

            if syscall == 'close':
                fd = line.split('(')[1]
                fd = fd.split(')')[0]
                fd = fd.split(' ')[0] # Sometimes printed as close(21 ) for eg.
                try:
                    fdToFilenameMap.pop(fd)
                except:
                    print "close: Fd: ", fd, " not in fdToFilenameMap"
                    print "lineno: ", lineno
                    # fd could be a socket
                    continue
                continue

            if syscall == 'fcntl' and 'F_DUPFD_CLOEXEC' in line:
                newfd = line.split('= ')[1]
                newfd = newfd.split('\n')[0]
                oldfd = line.split(',')[0]
                oldfd = oldfd.split('(')[1]
                if newfd in fdToFilenameMap.keys():
                    print "fcntl: New fd already initialized? lineno: ", lineno
                    return
                if oldfd not in fdToFilenameMap.keys():
                    print "fcntl: Old fd not initialized? line: ", lineno 
                    return
                try:
                    fdToFilenameMap[newfd] = fdToFilenameMap[oldfd]
                except:
                    print "fcntl: something wrong, lineno: ", lineno
                    return

            if syscall == 'io_submit':
                fd = line.split('fildes=')[1]
                fd = fd.split(',')[0]
                size = line.split('nbytes=')[1]
                size = size.split(',')[0]
                filename = fdToFilenameMap.get(fd)
                if not fd:
                    print "io_submit: No file with fd: ", fd
                    print "lineno: ", lineno
                    return
                if 'pwrite' in line:
                    filenameToWriteSizes[filename].append(size)
                elif 'pread' in line:
                    filenameToReadSizes[filename].append(size)
                else:
                    print "io_submit: Neither? lineno: ", lineno
                    return
                continue

            if syscall == 'write' or syscall == 'pwrite64':
                fd = line.split('(')[1]
                fd = fd.split(',')[0]
                filename = fdToFilenameMap.get(fd)
                if not filename or fd == '2':
                    # 2 is for stderr by default
                    continue
                if not filename:
                    print "write/pwrite64: No file with fd: ", fd
                    print "lineno: ", lineno
                    return
                size = line.split('= ')[1]
                size = size.split("\n")[0]
                filenameToWriteSizes[filename].append(size)
                continue

            if syscall == 'read' or syscall == 'pread64':
                fd = line.split('(')[1]
                fd = fd.split(',')[0]
                filename = fdToFilenameMap.get(fd)
                if not filename:
                    print "read/pread64: No file with fd: ", fd
                    print "lineno: ", lineno
                    return
                size = line.split('= ')[1]
                size = size.split("\n")[0]
                filenameToReadSizes[filename].append(size)
                continue
        except:
            print "Some error, lineno: ", lineno
            return

    f.close()
    return filenameToWriteSizes

# Syscalls
# {'+++',
#  'accept4',
#  'access',
#  'arch_prctl',
#  'bind',
#  'brk',
#  'chdir',
#  'clone',
#  'close',
#  'connect',
#  'dup3',
#  'execve',
#  'exit',
#  'fallocate',
#  'fcntl',
#  'fdatasync',
#  'fstat',
#  'fsync',
#  'futex',
#  'getcwd',
#  'getdents',
#  'geteuid',
#  'getpid',
#  'getpriority',
#  'getrlimit',
#  'getsockname',
#  'getsockopt',
#  'gettid',
#  'io_getevents',
#  'io_setup',
#  'io_submit',
#  'ioctl',
#  'listen',
#  'lseek',
#  'lstat',
#  'madvise',
#  'mmap',
#  'mprotect',
#  'munmap',
#  'nanosleep',
#  'open',
#  'openat',
#  'poll',
#  'pread64',
#  'pwrite64',
#  'read',
#  'readlink',
#  'recvfrom',
#  'recvmsg',
#  'rt_sigaction',
#  'rt_sigprocmask',
#  'sched_yield',
#  'sendto',
#  'set_robust_list',
#  'set_tid_address',
#  'setpriority',
#  'setrlimit',
#  'setsockopt',
#  'socket',
#  'stat',
#  'statfs',
#  'times',
#  'umask',
#  'uname',
#  'unlink',
#  'write'}
