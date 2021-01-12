#!/usr/bin/env python

import os
import datetime
import math
import re
from subprocess import Popen, PIPE
from cross_platform import CrossPlatform

import config

CP = CrossPlatform()

# Platform for linux-y ways of getting hardware information.
class LinuxPlatform:
    def get_mb_serial(self):
        cmdmbserial = ['/usr/sbin/dmidecode', '-t', 'system']
        runmbserial = Popen(cmdmbserial, stdout=PIPE)
        mbserial = [x for x in runmbserial.communicate()[0].split(
            b'\n') if b'Serial Number' in x][0].split()[-1]
        mbserial = mbserial.decode("utf-8")
            
        return mbserial

    # Get the machine's location in the ORG based on VLAN.
    def get_location(self):
        ip_vlan = int(CrossPlatform().get_ip().split('.', 2)[1])

        if ip_vlan == 147:
            location = 'losangeles'
        elif ip_vlan <= 55 and ip_vlan >= 51:
            location = 'portland'
        elif ip_vlan == 161:
            location = 'sanfrancisco'
        else:
            location = 'home'

        return location

    # Get the machine's location in the ORG based on VLAN.
    def get_ram(self):
        ram_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        # Cast to str to truncate int
        ram = int(ram_bytes / (1024.**2))
        ram = str(int(ram_bytes / (1024.**2)))[:-3]
        # Back to int for calculation
        ram = int(ram)

        # Edge cases where RAM count isn't rounded from MB truncate
        # Assuming RAM is divisible by 8
        if (ram + 1) % 8 == 0:
            ram += 1
        elif (ram - 1) % 8 == 0 and ram != 1:
            ram -= 1

        return ram

    # Get the RAM's speed.
    def get_ram_speed(self):
        ramspeed = ''
        cmdspeed = ['/usr/sbin/dmidecode', '--type', 'memory']
        runcmdspeed = Popen(cmdspeed, stdout=PIPE)
        speeds = runcmdspeed.communicate()[0].split(b'\n')
        ramspeed = [
            entry for entry in speeds if b'Speed' in entry and b'Unknown' not in entry \
            and b'Configured Clock Speed' not in entry][0]
        ramspeed = ramspeed.lstrip(b'\tSpeed: ')

        if not ramspeed.isdigit():
            ramspeed = ''
            
        # If the clockspeed is configured separately.
        ccramspeed = [
            entry for entry in speeds if b'Configured Clock Speed' in entry and b'Unknown' not in entry]

        if ccramspeed:
            ccramspeed = ccramspeed[0]
            ccramspeed = ccramspeed.lstrip(b'\tConfigured Clock Speed: ')

        if ccramspeed and ccramspeed != ramspeed:
            ramspeed = str(ramspeed) + '(' + str(ccramspeed) + ')'

        return ramspeed

    # Get any SSDs the machine may have internally.
    def get_ssd(self):
        ssd = ''
        cmddisk = ['lsblk', '-n', '-d', '-o', 'NAME,ROTA', '-I', '8']
        rundisk = Popen(cmddisk, stdout=PIPE)
        disks = rundisk.communicate()[0].strip().split(b'\n')
        cmddiskid = ['ls', '-la', '/dev/disk/by-id', '-I', '.', '-I', '..']
        rundiskid = Popen(cmddiskid, stdout=PIPE)
        diskids = rundiskid.communicate()[0].strip().split(b'\n')

        for disk in disks:
            if b'0' in disk:
                ssdisk = [diskid.split(b' ->')[0].split(b'_')[-1] for diskid in diskids if disk.split()[
                    0] in diskid and b'part' not in diskid and b'scsi' not in diskid and b'wwn-' not in diskid]
                if ssdisk != []:
                    ssd += ssdisk[0]

        return ssd

    # Get the type of tablet machine is using.
    def get_tablet(self):
        cmdtablet = ['lsusb', '-d', '056a:']
        runtablet = Popen(cmdtablet, stdout=PIPE)
        try:
            tabletraw = runtablet.communicate()[0]
            tablet = [entry.split(b', Ltd')[1].split() for entry in tabletraw.split(
                b'\n') if b'intuos' in entry.lower()][0]
            tablet = tablet[0] + ' ' + tablet[1]
        except BaseException:
            try:
                pid = tabletraw.split()[5].split(':')[1]
                tablet = config.linux_tablet_dict[pid]
            except BaseException:
                tablet = ''

        return tablet

    # Get monitor info.
    def get_monitor_info(self):
        try:
            cmdmon = ['nvidia-xconfig', '--query-gpu-info']
            runmon = Popen(cmdmon, stdout=PIPE)
            mons = runmon.communicate()[0].split(b'\n')
            mon = [mon.split(b':')[1].strip() for mon in mons if b'EDID' in mon]
        except BaseException:
            pass
        try:
            monitor1 = mon[0]
        except BaseException:
            monitor1 = ''
        try:
            monitor2 = mon[1]
        except BaseException:
            monitor2 = ''
        try:
            with open('/var/log/Xorg.0.log', 'r') as data:
                serialfile = data.readlines()
            serials = [serial.split(b': ')[2].strip(
            ) for serial in serialfile if b'Serial Number String' in serial]
        except BaseException:
            serials = ''
        try:
            serial1 = serials[-2]
        except BaseException:
            serial1 = ''
        try:
            serial2 = serials[-1]
        except BaseException:
            serial2 = ''

        return monitor1, serial1, monitor2, serial2

    # Get info on the last logged in user.
    # This function would need to be fine-tuned per OS, and this specific
    # function has been fine-tuned for CentOS 7.
    def get_last_info(self):
        cmdlast = ['last', '-wF']
        runlast = Popen(cmdlast, stdout=PIPE)
        last = runlast.communicate()[0]
        last = last.split(b"\n")
        last = last[0]

        if last:
            lastentry = last.split()
            lastentry_formatted = []
            # Strip away ":0", "pts", and domains from lastentry, this minimizes chance that they
            # appear differently on different OS's
            # If the last entry has a regular user, expect these spots to have
            # the accurate information
            if re.match(r"[0-9]{4}", str(lastentry[7])):
                lastentry_formatted += lastentry[0], lastentry[3], lastentry[4], lastentry[5], lastentry[6], lastentry[7]
            # If the last entry has a "system boot", there's an extra string we
            # need to account for
            else:
                lastentry_formatted += lastentry[0], lastentry[3], lastentry[4], lastentry[5], lastentry[6], lastentry[7]

            lastuser = lastentry_formatted[0]
            lastuser = lastuser.decode("utf-8")
            lasttime = b' '.join(lastentry_formatted[1:6])
            lasttime = lasttime.decode("utf-8")
            lastlogon = datetime.datetime.strptime(
                lasttime, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d")
            lastlogon = "{0}".format(lastlogon)
        else:
            lastuser = ''
            lastlogon = 'NULL'

        return lastuser, lastlogon

    # Get the proc (core) count. This would be useful for something like telling a
    # service how many cores each machine has to use.
    def get_procs(self, hyperthread_reporting_enabled):
        with open('/proc/cpuinfo', 'r') as data:
            cpuinfo = data.readlines()
            try:
                physcores = int(
                    re.sub(r'[^\d.]+', '', [entry for entry in cpuinfo if 'cores' in entry][0]))
                physcpus = len(
                    set([entry for entry in cpuinfo if 'physical id' in entry]))
                physprocs = physcores * physcpus
            except BaseException:
                physprocs = len(
                    [entry for entry in cpuinfo if 'processor' in entry])

        procs = len([entry for entry in cpuinfo if 'processor' in entry])

        cmd = ['/usr/bin/lscpu']
        run = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = run.communicate()
        out = out.split(b"\n")

        threads = [entry for entry in out if b'Thread(s) per core' in entry]
        threads = int(threads[0].split(b":")[1].strip())

        if physprocs != procs:
            hyperthread = 1
        elif threads > 1:
            hyperthread = 1
        else:
            hyperthread = 0

        # Only report physical cores, to leave virtual cores as a buffer,
        # so things wouldn't potentially get oversubscribed.
        if not hyperthread_reporting_enabled and not hyperthread == 0:
            procs = procs / 2

        cpuname = [entry for entry in cpuinfo if 'model name' in entry][0]
        cpuname = cpuname.split(":")[1].strip()

        return procs, hyperthread, cpuname

    # Get the uptime of the machine. Format for SQL.
    def get_uptime(self):
        cmdup = ['uptime']
        runup = Popen(cmdup, stdout=PIPE)
        uptime = runup.communicate()[0].split(b',')[0].lstrip()
        uptime = uptime.decode("utf-8")

        return uptime

    # See if the machine has an NVME for tracking purposes.
    def check_nvme(self):
        cmd = ['/sbin/lspci']
        run = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = run.communicate()

        if b'Non-Volatile memory controller' in out:
            nvme = 1
        else:
            nvme = 0

        return nvme
