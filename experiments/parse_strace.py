# strace command: strace -f -o /mnt/hdd/mariadb_strace.out ./bin/mysqld_safe --user=aarati &

INPUT_DIR = "/mnt/hdd/mariadb_strace/"
INPUT_FILE =  INPUT_DIR + "mariadb_strace.out"

def getPIDs():
    f = open(INPUT_FILE, 'r')
    pids = set()
    for line in f:
        pids.add(line.split(' ')[0])
    f.close()
    return pids


# Sorted list of sys calls at the end of the file
# ['lseek', 'accept4', 'getsockname', 'rt_sigaction', 'io_getevents', 'mprotect', 'setsockopt', 'io_submit', 
# 'uname', 'brk', 'pread64', 'rt_sigtimedwait', 'poll', 'close', 'recvfrom', 'futex', 'open', 
# 'newfstatat', 'write', 'bind', 'io_setup', 'exit_group', 'getpriority', 'mmap', 'geteuid', 'lstat', 'umask', 
# 'arch_prctl', 'statfs', 'access', 'faccessat', 'setpriority', 'recvmsg', 'getpid', 'openat', 'exit', 'getrlimit', 
# 'munmap', 'setrlimit', 'listen', 'fcntl', 'getsockopt', 'stat', 'getcwd', 'dup3', 'dup2', 'read', 
# 'sched_yield', 'clone', 'sendto', 'getppid', 'fadvise64', 'pwrite64', 'set_robust_list', 'ioctl', 'socket', 
# 'readlink', 'unlink', 'fdatasync', 'fallocate', 'execve', 'times', 'wait4', 'gettid', 'chdir', 'getdents', 
# 'madvise', 'set_tid_address', 'fsync', 'fstat', 'pipe', 'nanosleep', 'rt_sigprocmask', 'unlinkat', 'kill', 
# 'rt_sigreturn', 'connect']
#
# I/O system calls: lseek, io_getevents, io_submit, pread64, close, open
# write, io_setup, lstat?, mmap, statfs, openat, fcntl, stat, getcwd, dup2, dup3,
# read, pwrite64, fadvise64, ioctl, readlink/unlink/unlinkat?, fdatasync, fsync, fstat, 
def getSysCalls():
    f = open(INPUT_FILE, 'r')
    syscalls = set()
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        syscalls.add(syscall_substr)
    f.close()
    return syscalls

# Some relevant files, opened using the "open" system call
# Directory prefix: /usr/local/mysql/data
# ibdata1 - Looks like a single file for the doublewrite buffer and change buffer
#           Refer to: https://dev.mysql.com/doc/refman/8.0/en/innodb-system-tablespace.html
# ib_logfile0, ib_logfile1 - Redo log (but why two files?)
#                            Refer to: https://dev.mysql.com/doc/refman/5.6/en/innodb-redo-log.html
# undo001 - undo log? Has been deleted (undone? :P)..
# test/KV.isl - InnoDB symbolic link files, has been deleted
# test/KV.ibd - This is the main file containing table data
# ibtmp1 - Not sure what this is; refer to https://dev.mysql.com/doc/refman/5.7/en/innodb-temporary-tablespace.html
#          Looks like has a fixed size of 12MB
# ddl_log.log - metadata log, records metadata operations: https://dev.mysql.com/doc/refman/8.0/en/ddl-log.html
#               has been deleted
# test/db.opt - not important, contains some random info
# 
# So in conclusion, the important files are:
# ibdata1
# ib_logfile0, ib_logfile1
# undo001
# test/KV.ibd
# ddl_log.log
def getOpenedFilenames():
    f = open(INPUT_FILE, 'r')
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'open':
            filepath = line.split('"')[1]
            if filepath.startswith('/'):
                continue
            print filepath
    f.close()

# Looks like "openat" is used to open the path to /usr/local/mysql/data directory
# All the files (obtained from the previous function getOpenedFilenames) are contained in this directory
# There is a directory named "test" inside /usr/local/mysql/data, which corresponds to the database named test
def getOpenatFilenames():
    f = open(INPUT_FILE, 'r')
    all_paths = set()
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'openat':
            filepath = line.split('"')[1]
            all_paths.add(filepath)
    for path in all_paths:
        print path
    f.close()

def getProcessTree():
    # Look for the 'clone' system call
    f = open(INPUT_FILE, 'r')
    parents = {}
    for line in f:
        syscall_substr = line.split(' ')[1]
        syscall_substr = syscall_substr.split('(')[0]
        if syscall_substr == 'clone' or "clone resumed" in line:
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
    print parents
    f.close()

# All PIDs: Total 96
# '24872','24873','24874','24875','24876','24877','24878','24879','24880','24881','24882','24883',
# '24884','24885','24886','24887','24888','24889','24890','24891','24892','24893','24894','24895',
# '24896','24897','24898','24899','24900','24901','24902','24903','24904','24905','24906','24907',
# '24908','24909','24910','24911','24912','24913','24914','24915','24916','24917','24918','24919',
# '24920','24921','24922','24923','24924','24925','24926','24927','24928','24929','24930','24931',
# '24932','24933','24934','24935','24936','24937','24938','24939','24940','24941','24942','24943',
# '24944','24945','24946','24947','24948','24949','24950','24951','24952','24953','24954','24955',
# '24956','24957','24958','24959','24960','24961','24962','24963','24964','24965','24966','25051',

# Parent PIDs:
# '24883', '24897', '24903', '24935', '24928', '24872', '24873', '24913',
# '24876', '24916', '24919', '24922', '24879', '24925', '24893'

# Process Tree:
# The parent process: 24872, Total 96 processes
# {'24872': ['24873','24876','24879','24883','24886','24887','24888','24889',\
#            '24890','24891','24892','24893','24896','24897','24900','24901',\
#            '24902','24903','24906','24907','24908','24909','24910','24911',\
#            '24912','24913','24916','24919','24922','24925','24928','24931',\
#            '24932','24933','24934','24935'],
#  '24873': ['24874', '24875'],
#  '24876': ['24877', '24878'],
#  '24879': ['24880', '24881', '24882'],
#  '24883': ['24884', '24885'],
#  '24893': ['24894', '24895'],
#  '24897': ['24898', '24899'],
#  '24903': ['24904', '24905'],
#  '24913': ['24914', '24915'],
#  '24916': ['24917', '24918'],
#  '24919': ['24920', '24921'],
#  '24922': ['24923', '24924'],
#  '24925': ['24926', '24927'],
#  '24928': ['24929', '24930'],
 # '24935': ['24936','24937','24938','24939','24940','24941','24942','24943',\
 #           '24944','24945','2494366','24947','24948','24949','24950','24951',\
 #           '24952','24953','24954','24955','24956','24957','24958','24959',\
 #           '24960','24961','24962','24963','24964','24965','24966','25051']}

# ibdata1 file
def ibdataIOld():
    # Start by printing a sample I/O call - file descriptor arg is present
    # Get a list of all the PIDs that opened this file - Just 24935, fd 6
    f = open(INPUT_FILE, 'r')
    ibdata_syscalls = open(INPUT_DIR + "ibdata_syscall_trace",'w')
    parent = "24935"
    children = ['24936','24937','24938','24939','24940','24941','24942','24943',\
           '24944','24945','24946','24947','24948','24949','24950','24951',\
           '24952','24953','24954','24955','24956','24957','24958','24959',\
           '24960','24961','24962','24963','24964','24965','24966','25051']
    all_pids = [parent] + children
    pids_with_ibdata = set(all_pids)
    ibdataOpen = True
    lineno = 0

    # Dealing with unfinished lines
    lineUnfinished = False
    syscallUnfinished = None
    pidUnfinished = None
    prevLine = None
    for line in f:
        lineno += 1
        # Look at option for unfinished lines
        if lineUnfinished:
            # The line written to the file in the previous iteration was unfinished
            if syscallUnfinished not in line or pidUnfinished not in line:
                # Might have to skip this line
                syscall = line.split(' ')[1]
                syscall = syscall.split('(')[0]
                if syscall in {'pread64', 'pwrite64', 'read', 'write', 'io_submit'}:
                    print "Skipping IO syscall: ", line, " lineno: ", lineno
                    return
                continue

            try:
                ibdata_syscalls.write(line.split("resumed> ")[1])
                lineUnfinished = False
                continue
            except:
                # Something wrong
                print "Something wrong in lineUnfinished: ", prevLine
                print "lineno: ", lineno
                return

        syscall = line.split(' ')[1]
        syscall = syscall.split('(')[0]
        try:
            output = line.split("= ")[1]
            output = output.split('\n')[0]
        except:
            output = 'undefined'
        pid = line.split(' ')[0]
        if syscall == 'open' and "./ibdata1" in line:
            ibdataOpen = True
            pids_with_ibdata.add(pid)
            # print "pids_with_ibdata: ", pids_with_ibdata

        if not ibdataOpen:
            # Nothing to do
            continue

        if pid not in pids_with_ibdata:
            # Not a relevant pid
            continue

        # Record relevant syscalls: clone, pread64, pwrite64, read, write, io_submit
        # Clone might not mean the same fds (there is an option)
        if syscall == 'clone' or "clone resumed" in line:
            # The clone process also has an fd to ibdata1 file
            if output == "undefined":
                # The next line contains the child PID
                continue
            pids_with_ibdata.add(output)
            # print "pids_with_ibdata: ", pids_with_ibdata
            continue

        # pread, pwrite, read, write
        if syscall in {'pread64', 'pwrite64', 'read', 'write'}:
            fd = line.split('(')[1]
            fd = fd.split(',')[0]
            if int(fd) == 6:
                ibdata_syscalls.write(line.split("<unfinished ...>")[0])
                if "<unfinished ...>" in line:
                    lineUnfinished = True
                    prevLine = line
                    pidUnfinished = pid
                    syscallUnfinished = syscall
            continue

        # io_submit
        if syscall == 'io_submit':
            fd = line.split("fildes=")[1]
            fd = fd.split(',')[0]
            if int(fd) == 6:
                ibdata_syscalls.write(line.split("<unfinished ...>")[0])
                if "<unfinished ...>" in line:
                    lineUnfinished = True
                    prevLine = line
            continue

        # dup2, dup3
        if syscall in {'dup2', 'dup3'}:
            fd = line.split('(')[1]
            fd = fd.split(',')[0]
            if int(fd) == 6:
                print "Fd 6 duped in pid: ", pid, " lineno: ", lineno

        if 'close(6)' in line and pid in pids_with_ibdata:
            pids_with_ibdata.remove(pid)
            # print "pids_with_ibdata: ", pids_with_ibdata

        if not len(pids_with_ibdata):
            ibdataOpen = False
            print "No process with fd to ibdata1"

    f.close()
    ibdata_syscalls.close()

# ibdata1 file
def ibdataIO():
    f = open(INPUT_FILE, 'r')
    ibdata_syscalls = open(INPUT_DIR + "ibdata_syscall_trace",'w')
    parent = "24935"
    children = ['24936','24937','24938','24939','24940','24941','24942','24943',\
           '24944','24945','24946','24947','24948','24949','24950','24951',\
           '24952','24953','24954','24955','24956','24957','24958','24959',\
           '24960','24961','24962','24963','24964','24965','24966','25051']
    all_pids = [parent] + children
    lineno = 0
    for line in f:
        lineno += 1
        syscall = line.split(' ')[1]
        syscall = syscall.split('(')[0]
        try:
            output = line.split("= ")[1]
            output = output.split('\n')[0]
        except:
            output = 'undefined'
        pid = line.split(' ')[0]
        if pid not in all_pids:
            # Not a relevant pid
            continue
        if syscall in {'pread64', 'pwrite64', 'read', 'write'}:
            fd = line.split('(')[1]
            fd = fd.split(',')[0]
            if int(fd) == 6:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + "lineno: " + str(lineno) + '\n'
                ibdata_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass

        if syscall == 'io_submit':
            fd = line.split("fildes=")[1]
            fd = fd.split(',')[0]
            if int(fd) == 6:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + '\n'
                ibdata_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass
        
    f.close()
    ibdata_syscalls.close()

# ib_logfile0 file
def iblogfile0():
    f = open(INPUT_FILE, 'r')
    iblogfile_syscalls = open(INPUT_DIR + "iblogfile0_syscall_trace",'w')
    parent = "24935"
    children = ['24936','24937','24938','24939','24940','24941','24942','24943',\
           '24944','24945','24946','24947','24948','24949','24950','24951',\
           '24952','24953','24954','24955','24956','24957','24958','24959',\
           '24960','24961','24962','24963','24964','24965','24966','25051']
    all_pids = [parent] + children
    lineno = 0
    for line in f:
        lineno += 1;
        syscall = line.split(' ')[1]
        syscall = syscall.split('(')[0]
        try:
            output = line.split("= ")[1]
            output = output.split('\n')[0]
        except:
            output = 'undefined'
        pid = line.split(' ')[0]
        if pid not in all_pids:
            # Not a relevant pid
            continue
        if syscall in {'pread64', 'pwrite64', 'read', 'write'}:
            fd = line.split('(')[1]
            fd = fd.split(',')[0]
            if int(fd) == 10:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + "lineno: " + str(lineno) + '\n'
                iblogfile_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass

        if syscall == 'io_submit':
            fd = line.split("fildes=")[1]
            fd = fd.split(',')[0]
            if int(fd) == 10:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + '\n'
                iblogfile_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass
        
    f.close()
    iblogfile_syscalls.close()

# ib_logfile1 file
def iblogfile1():
    f = open(INPUT_FILE, 'r')
    iblogfile_syscalls = open(INPUT_DIR + "iblogfile1_syscall_trace",'w')
    parent = "24935"
    children = ['24936','24937','24938','24939','24940','24941','24942','24943',\
           '24944','24945','24946','24947','24948','24949','24950','24951',\
           '24952','24953','24954','24955','24956','24957','24958','24959',\
           '24960','24961','24962','24963','24964','24965','24966','25051']
    all_pids = [parent] + children
    lineno = 0
    for line in f:
        lineno += 1;
        syscall = line.split(' ')[1]
        syscall = syscall.split('(')[0]
        try:
            output = line.split("= ")[1]
            output = output.split('\n')[0]
        except:
            output = 'undefined'
        pid = line.split(' ')[0]
        if pid not in all_pids:
            # Not a relevant pid
            continue
        if syscall in {'pread64', 'pwrite64', 'read', 'write'}:
            fd = line.split('(')[1]
            fd = fd.split(',')[0]
            if int(fd) == 11:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + "lineno: " + str(lineno) + '\n'
                iblogfile_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass

        if syscall == 'io_submit':
            fd = line.split("fildes=")[1]
            fd = fd.split(',')[0]
            if int(fd) == 11:
                write_line = line.split("<unfinished ...>")[0]
                if write_line[-1] != '\n':
                    write_line = write_line + '\n'
                iblogfile_syscalls.write(write_line)
                if "<unfinished ...>" in line:
                    # Handle this later
                    pass
        
    f.close()
    iblogfile_syscalls.close()

def printFn():
    f = open(INPUT_FILE, 'r')
    for line in f:
        syscall = line.split(' ')[1]
        syscall = syscall.split('(')[0]
        if syscall == 'io_submit':
            print line
            return
    f.close()

# All system calls
# ['accept4',
#  'access',
#  'arch_prctl',
#  'bind',
#  'brk',
#  'chdir',
#  'clone',
#  'close',
#  'connect',
#  'dup2',
#  'dup3',
#  'execve',
#  'exit',
#  'exit_group',
#  'faccessat',
#  'fadvise64',
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
#  'getppid',
#  'getpriority',
#  'getrlimit',
#  'getsockname',
#  'getsockopt',
#  'gettid',
#  'io_getevents',
#  'io_setup',
#  'io_submit',
#  'ioctl',
#  'kill',
#  'listen',
#  'lseek',
#  'lstat',
#  'madvise',
#  'mmap',
#  'mprotect',
#  'munmap',
#  'nanosleep',
#  'newfstatat',
#  'open',
#  'openat',
#  'pipe',
#  'poll',
#  'pread64',
#  'pwrite64',
#  'read',
#  'readlink',
#  'recvfrom',
#  'recvmsg',
#  'rt_sigaction',
#  'rt_sigprocmask',
#  'rt_sigreturn',
#  'rt_sigtimedwait',
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
#  'unlinkat',
#  'wait4',
#  'write']

def fixStraceOutput():
    input_file = INPUT_DIR + "binlog.strace"
    input_file = open(input_file, 'r')

    lines = []
    for line in input_file:
        lines.append(line)
    input_file.close()

    # Fix the "unfinished" system calls
    output_file = INPUT_DIR + "corrected_binlog.strace"
    output_file = open(output_file, 'w')
    lc = len(lines) # lc: line count
    print "Total line count: ", lc
    i = 0
    j = 0
    lines_accounted_for = set()
    while i < lc:
        line = lines[i]
        # Unbroken line
        if 'unfinished' not in line and 'resumed' not in line:
            output_file.write(line)
            lines_accounted_for.add(i)
        # Broken line first half
        if 'unfinished' in line:
            pid = line.split(' ')[0]
            syscall = line.split(' ')[1]
            syscall = syscall.split('(')[0]
            # find the completing line
            j = i+1
            while j < lc:
                pid_test = lines[j].split(' ')[0]
                syscall_substr = syscall + " " + "resumed"
                if pid_test == pid and syscall_substr in lines[j]:
                    output_file.write(line.split(' <')[0])
                    output_file.write(lines[j].split('>')[1])
                    lines_accounted_for.add(i)
                    lines_accounted_for.add(j)
                    break
                j+=1
                continue
        # Broken line second half, should have been accounted for
        if 'resumed' in line:
            if i not in lines_accounted_for:
                print "Line: ", i, " not accounted for"
                return
        i += 1
        continue
    output_file.close()
