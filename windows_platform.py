#!/usr/bin/env python

import os
import sys
from subprocess import Popen, PIPE
from cross_platform import CrossPlatform

import config

CP = CrossPlatform()

# Platform for windows-y ways of getting hardware information.
class WindowsPlatform:
    # This will determine a machine's location based on several factors. Some domains only have one
    # location, and the three d2 locations are determined by IP addresses.
    def get_location(self):
        cmddom = ['wmic', 'computersystem', 'get', 'domain']
        rundom = Popen(cmddom, stdout=PIPE)
        domain = rundom.communicate()[0].strip().split(b'\r\r\n')[1]

        if domain == 'la.company.com':
            location = 'losangeles'
        elif domain == 'bc.company.com':
            location = 'vancouver'
        # Infer some known VLANs for actual locations in CA.
        elif domain == 'company.com':
            ip_vlan = int(CrossPlatform().get_ip().split(b'.', 2)[1])

            if ip_vlan == 147:
                location = 'losangeles'
            elif ip_vlan <= 55 and ip_vlan >= 51:
                location = 'portland'
            elif ip_vlan == 161:
                location = 'sanfrancisco'
        # Fallback location is portland, as this is the most important location.
        else:
            location = 'home'

        return location

    # Get the motherboard serial number for reference later.
    def get_mb_serial(self):
        mbserial = ''
        cmdmbserial = ['wmic', 'baseboard', 'get', 'serialnumber']
        runmbserial = Popen(cmdmbserial, stdout=PIPE)
        mbserial = runmbserial.communicate()[0].strip().split(b'\r\r\n')[1]
        mbserial = mbserial.decode("utf-8")

        return mbserial

    # Retrieve the machine's RAM in GB for human readability.
    def get_ram(self):
        cmdram = [
            'powershell',
            '(Get-WMIObject Win32_PhysicalMemory |  Measure-Object Capacity -Sum).sum/1GB']
        runram = Popen(cmdram, stdout=PIPE)
        ram = runram.communicate()[0].strip().split(b'.')[0]
        ram = ram.decode("utf-8")

        return ram

    # Get the RAM's speed in MT/s.
    def get_ram_speed(self):
        cmdramspeed = [
            'powershell',
            '((Get-WMIObject CIM_PhysicalMemory).Speed | Get-Unique)']
        runramspeed = Popen(cmdramspeed, stdout=PIPE)
        ramspeed = runramspeed.communicate()[0].strip()
        ramspeed = ramspeed.decode("utf-8")

        return ramspeed

    # Get SSD Serial Number for reference.
    def get_ssd(self):
        cmdssd = [
            'powershell',
            '(Get-WmiObject win32_diskdrive |where{$_.model -Like "*SSD*"}| select-object -expand SerialNumber)']
        runssd = Popen(cmdssd, stdout=PIPE)
        ssd = runssd.communicate()[0].strip().replace(b"\r\n", b", ")
        ssd = ssd.decode("utf-8")

        return ssd

    # Get an attached tablet on the system. May be useful to know.
    def get_tablet(self):
        cmdtablet = [
            'powershell',
            '(get-wmiobject win32_pnpentity | where {$_.caption -eq "Wacom Tablet"} | select-object -Expand deviceid)']
        runtablet = Popen(cmdtablet, stdout=PIPE)
        try:
            tablet = runtablet.communicate()[0].split(b'\\')[1].split(b'&')[1]
            tablet = config.windows_tablet_dict[tablet]
        except BaseException:
            tablet = ''

        return tablet

    # Get up to 2 connected monitors.
    def get_monitor_info(self):
        cmdmon = [
            'powershell',
            '-ExecutionPolicy',
            'ByPass',
            '-File',
            os.path.join(
                sys.path[0],
                'moninfo.ps1')]
        runmon = Popen(cmdmon, stdout=PIPE)
        mon = runmon.communicate()[0].strip().replace(b"\r\n", b":").replace(b" ", b"")
        mon = mon.replace(b"\x00", b"")
        mon = mon.decode("utf-8")
        mon = mon.split(":")
        
        try:
            monitor1 = mon[7]
        except BaseException:
            monitor1 = ''
        try:
            serial1 = mon[9]
        except BaseException:
            serial1 = ''
        try:
            monitor2 = mon[22]
        except BaseException:
            monitor2 = ''
        try:
            serial2 = mon[24]
        except BaseException:
            serial2 = ''

        return monitor1, serial1, monitor2, serial2

    # Get the last logged in user.
    def get_last_info(self):
        cmdlast = [
            'powershell',
            r'(Get-ItemProperty "hklm:SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI").LastLoggedOnUser']
        runlast = Popen(cmdlast, stdout=PIPE)
        lastuser = runlast.communicate()[0].strip()
        lastuser = lastuser.decode("utf-8")

        if '@' in lastuser:
            lastuser = lastuser.split('@')[0]
        elif '\\' in lastuser:
            lastuser = lastuser.split('\\')[1]

        # Some powershell magic to get the lastlogon time. Format in YYYY-MM-DD.
        cmdlastlogon = [
            'powershell',
            '(Get-WMIObject -Class Win32_UserProfile | Where-Object {($_.SID -eq (New-Object System.Security.Principal.NTAccount("' +
            lastuser +
            '")).Translate([System.Security.Principal.SecurityIdentifier]).Value)} | Sort-Object -Property LastUseTime -Descending | Select-Object -First 1).converttodatetime((Get-WMIObject -Class Win32_UserProfile | Where-Object {($_.SID -match (New-Object System.Security.Principal.NTAccount("' +
            lastuser +
            '")).Translate([System.Security.Principal.SecurityIdentifier]).Value)} | Sort-Object -Property LastUseTime -Descending | Select-Object -First 1).lastusetime).tostring("yyyy-MM-dd")']
        runlastlogon = Popen(cmdlastlogon, stdout=PIPE)
        lastlogon = runlastlogon.communicate()[0].strip()

        # Nobody logged in yet (shouldn't happen?)
        if b'FullyQualifiedErrorId' in lastlogon:
            lastlogon = 'NULL'
        else:
            lastlogon = "{0}".format(lastlogon)

        lastlogon = lastlogon.replace("b'", "")
        lastlogon = lastlogon.replace("'", "")

        return lastuser, lastlogon

    # Get proc count on this machine. May be useful for Race.
    def get_procs(self, hyperthread_reporting_enabled):
        cmdprocs = [
            'powershell',
            '(Get-WmiObject win32_processor).NumberOfCores']
        runprocs = Popen(cmdprocs, stdout=PIPE)
        procs = 0
        winprocs = runprocs.communicate()[0].split(b'\r\n')
        winprocs.remove(b'')
        for line in winprocs:
            procs = procs + int(line)
        lprocs = 0
        cmdlprocs = [
            'powershell',
            '(Get-WmiObject win32_processor).NumberOfLogicalProcessors']
        runlprocs = Popen(cmdlprocs, stdout=PIPE)
        winlprocs = runlprocs.communicate()[0].split(b'\r\n')
        winlprocs.remove(b'')

        for line in winlprocs:
            lprocs = lprocs + int(line)
        cmdcpuname = ['powershell', '(Get-WmiObject win32_processor).Name']
        runcpuname = Popen(cmdcpuname, stdout=PIPE)

        try:
            cpulist = runcpuname.communicate()[0].strip(b'\r\n').split()
            cpulist.remove(b'CPU')
            cpulist = [entry.decode("utf-8") for entry in cpulist]
            cpuname = " ".join(cpulist)
        except BaseException:
            cpuname = ''
        if procs != lprocs:
            hyperthread = 1
        else:
            hyperthread = 0

        if hyperthread_reporting_enabled:
            procs = lprocs

        return procs, hyperthread, cpuname

    # Get the uptime of the machine. Format for SQL.
    def get_uptime(self):
        cmdup = [
            'powershell',
            '(get-date)',
            '-',
            '(gcim Win32_OperatingSystem).LastBootUpTime']
        runup = Popen(cmdup, stdout=PIPE)
        uptime = runup.communicate()[0].strip(b'\r\n')
        uptime = uptime.decode("utf-8")
        uptime = uptime.replace(" ", "").replace("\r\n", ":")
        uptime = uptime.split(":")
        uptime = "{0} days, {1} hours".format(uptime[1], uptime[3])
        
        return uptime

    # See if the machine has an NVME for tracking purposes.
    def check_nvme(self):
        cmd = ['powershell', 'Get-Disk', '|', '?', 'model']
        run = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = run.communicate()
        out = out.decode("utf-8")

        if 'NVME' in out:
            nvme = 1
        else:
            nvme = 0

        return nvme
