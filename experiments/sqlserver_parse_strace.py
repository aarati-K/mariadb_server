# strace command: strace -f -o /mnt/hdd/mariadb_strace.out ./bin/mysqld_safe --user=aarati &

INPUT_DIR = "/mnt/hdd/mariadb_strace/"
INPUT_FILE =  INPUT_DIR + "mssql_oltpbench_tpcc.strace"

# 'accept',
# access',
# 'arch_prctl',
# 'bind',
# 'clock_gettime',
# 'clone',
# 'close',
# 'connect',
# 'epoll_create',
# 'epoll_ctl',
# 'epoll_wait',
# 'eventfd2',
# 'exit',
# 'fallocate',
# 'fcntl',
# 'fdatasync',
# 'flock',
# 'fstat',
# 'fstatfs',
# 'fsync',
# 'ftruncate',
# 'futex',
# 'getcpu',
# 'getdents',
# 'getpeername',
# 'getrandom',
# 'getrusage',
# 'getsockname',
# 'getsockopt',
# 'gettid',
# 'io_getevents',
# 'io_submit',
# 'ioctl',
# 'lstat',
# 'madvise',
# 'mmap',
# 'mprotect',
# 'munmap',
# 'nanosleep',
# 'open',
# 'poll',
# 'ppoll',
# 'pread64',
# 'read',
# 'readlink',
# 'readlinkat',
# 'readv',
# 'recvfrom',
# 'recvmsg',
# 'restart_syscall',
# 'rt_sigprocmask',
# 'rt_sigreturn',
# 'rt_sigtimedwait',
# 'sched_getaffinity',
# 'sched_setaffinity',
# 'sched_yield',
# 'sendto',
# 'set_robust_list',
# 'setsockopt',
# 'sigaltstack',
# 'socket',
# 'stat',
# 'statfs',
# 'tgkill',
# 'unlink',
# 'wait4',
# 'write',
# 'writev'

def getSysCalls():
    f = open(INPUT_FILE, 'r')
    syscalls = set()
    for line in f:
        if "resumed" in line:
            continue
        syscall_substr = line.split(' ')[2]
        syscall_substr = syscall_substr.split('(')[0]
        try:
            x = float(syscall_substr)
            syscall_substr = line.split(' ')[3]
            syscall_substr = syscall_substr.split('(')[0]
        except:
            pass
        syscalls.add(syscall_substr)
    f.close()
    return syscalls

# Total 414, too many to enumerate
def getTIDs():
    f = open(INPUT_FILE, 'r')
    tids = set()
    for line in f:
        tids.add(line.split(' ')[0])
    f.close()
    return tids

# Total: 51
# 
# Data files:
# '/var/opt/mssql/data/oltpbench_tpcc.mdf', - Primary database file
# '/var/opt/mssql/data/oltpbench_tpcc_log.ldf', - Transaction log

# Log files: trace files
# '/var/opt/mssql/log/log_749.trc',
# '/var/opt/mssql/log/log_754.trc'

# '/var/opt/mssql/mssql.conf'
def getOpenedFilenames():
    f = open(INPUT_FILE, 'r')
    all_files = set()
    for line in f:
        syscall_substr = line.split(' ')[2]
        syscall_substr = syscall_substr.split('(')[0]
        try:
            x = float(syscall_substr)
            syscall_substr = line.split(' ')[3]
            syscall_substr = syscall_substr.split('(')[0]
        except:
            pass
        if syscall_substr == 'open':
            try:
                filepath = line.split('"')[1]
                all_files.add(filepath)
            except:
                print line
    f.close()
    return all_files

# Can't get the process tree, we seem to have only a part of the strace
def getProcessTree():
    f = open(INPUT_FILE, 'r')
    parents = {}
    for line in f:
        syscall_substr = line.split(' ')[2]
        syscall_substr = syscall_substr.split('(')[0]
        try:
            x = float(syscall_substr)
            syscall_substr = line.split(' ')[3]
            syscall_substr = syscall_substr.split('(')[0]
        except:
            pass
        if syscall_substr == 'clone' or 'clone resumed' in line:
            parent_pid = line.split(' ')[0]
            try:
                child_pid = line.split(' = ')[1]
                child_pid = child_pid.split('\n')[0]
            except:
                print line
                continue
            children = parents.get(parent_pid)
            if children:
                children.append(child_pid)
            else:
                children = [child_pid]
            parents[parent_pid] = children
    f.close()
    return parents

# Accesses to the primary database (mdf) file
def getMdfFileOpenTids():
    f = open(INPUT_FILE, 'r')
    tids = set()
    for line in f:
        if 'open("/var/opt/mssql/data/oltpbench_tpcc.mdf"' in line:
            tid = line.split(' ')[0]
            tids.add(tid)
    print tids

def getLdfFileOpenTids():
    f = open(INPUT_FILE, 'r')
    tids = set()
    for line in f:
        if 'open("/var/opt/mssql/data/oltpbench_tpcc_log.ldf"' in line:
            tid = line.split(' ')[0]
            tids.add(tid)
    print tids

def getMdfFileReadWrites():
    threadToFd = {}
    readSizes = set()
    writeSizes = set()
    f = open(INPUT_FILE, 'r')
    for line in f:
        syscall_substr = line.split(' ')[2]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr not in ['open', 'close', 'read', 'write', 'writev']:
            continue

        tid = line.split(' ')[0]
        if 'open("/var/opt/mssql/data/oltpbench_tpcc.mdf"' in line:
            try:
                fd = line.split(' = ')[1]
                fd = fd.split('\n')[0]
            except:
                print line
                continue
            threadToFd[tid] = fd
            print "adding ", tid
            continue

        if 'close(' in line:
            fd = line.split('(')[1]
            fd = fd.split(')')[0]
            if fd == threadToFd.get(tid):
                threadToFd.pop(tid)
                print "removing", tid
            continue

        if syscall_substr == 'read':
            fd = line.split('(')[1]
            fd = fd.split(')')[0]
            if fd == threadToFd.get(tid):
                try:
                    readsize = line.split(' = ')[1]
                    readsize = readsize.split('\n')[0]
                    readSizes.add(readsize)
                except:
                    continue
            continue

        if syscall_substr == 'write':
            fd = line.split('(')[1]
            fd = fd.split(')')[0]
            if fd == threadToFd.get(tid):
                try:
                    writesize = line.split(' = ')[1]
                    writesize = writesize.split('\n')[0]
                    writeSizes.add(writesize)
                except:
                    continue
            continue

        if syscall_substr == 'writev':
            fd = line.split('(')[1]
            fd = fd.split(')')[0]
            if fd == threadToFd.get(tid):
                try:
                    writesize = line.split(' = ')[1]
                    writesize = writesize.split('\n')[0]
                    writeSizes.add(writesize)
                except:
                    continue
            continue

    f.close()
    print readSizes
    print writeSizes
