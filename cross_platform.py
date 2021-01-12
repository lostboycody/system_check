#!/usr/bin/env python

import re
import platform
import socket
import time
from subprocess import Popen, PIPE, CalledProcessError
from uuid import getnode as get_mac

import config

# Base class for tasks that can be accomplished on both Linux and Windows.
class CrossPlatform:
    def get_name(self):
        try:
            name = socket.gethostname().lower()
        except BaseException:
            name = socket.gethostname().lower()

        return name

    def get_os(self):
        sysos = platform.system().lower()

        return sysos

    # Get Operating System type and version, then format for SQL.
    def get_os_version(self):
        osversion = platform.platform()
        if 'centos-7.' in osversion:
            return "cent7_64"
        elif 'redhat-7' in osversion:
            return "cent7_64"
        elif 'centos-6.' in osversion:
            return "cent6_64"
        elif 'redhat-6' in osversion:
            return "cent6_64"
        elif 'XP' in osversion:
            return "xp_32"
        elif 'Windows-7' in osversion:
            return "win7_64"
        elif 'Windows-10' in osversion:
            return "win10_64"
        elif 'Windows-post2008Server' in osversion:
            return "win7_64"
        else:
            return "unknown"

    # Get the IPv4 address.
    def get_ip(self):
        try:
            ipaddr = socket.gethostbyname(socket.gethostname())
            return ipaddr
        except:
            ipaddr = '0.0.0.0'
            return ipaddr

    # Get the MAC address.
    def get_mac(self):
        macaddr = ':'.join(("%012X" % get_mac())[i:i + 2] for i in range(0, 12, 2))

        return macaddr

    # Get the current time in YYYY-mm-dd HH:MM:SS format.
    def get_current_time(self):
        lastupdate = time.strftime("%Y-%m-%d %H:%M:%S")

        return lastupdate

    # Get NVIDIA GPU information.
    def get_gpu(self, smi):
        try:
            cmdgpu = [smi, '-L']
            rungpu = Popen(cmdgpu, stdout=PIPE)
            gpu = rungpu.communicate()[0].strip()
            gpu = re.sub(r'\([^)]*\)', '', gpu)
            gpu = re.sub(r'GPU.+: ', '', gpu).strip()
            gpu = gpu.replace('\r', '')
            if '\n' in gpu:
                gpu = gpu.replace(' \n', ',')
            if 'NVIDIA-SMI' in gpu:
                gpu = ''
            if 'Failed' in gpu:
                gpu = ''
            if 'Unable' in gpu:
                gpu = ''
        except BaseException:
            try:
                gpu = ''
                cmdgpu = [
                    'powershell',
                    '(Get-WMIObject Win32_VideoController).Name |  Where-Object {$_ -notmatch "Remote"}']
                rungpu = Popen(cmdgpu, stdout=PIPE)
                gpu = rungpu.communicate()[0].strip(b'\r\n')
                gpu = gpu.decode("utf-8")
                if '\n' in gpu:
                    gpu = gpu.replace(' \n', ',')
            except BaseException:
                gpu = ''

        return gpu

    # Get the Serial number of the NVIDIA GPU.
    def get_gpu_serial(self, smi):
        try:
            cmdgpuserial = [smi, '--query-gpu=serial', '--format=csv,noheader']
            rungpuserial = Popen(
                cmdgpuserial,
                stdout=PIPE,
                stderr=subprocess.STDOUT)
            gpuserial = rungpuserial.communicate()[0].strip()
            gpuserial = gpuserial.replace('\r', '')
            if '\n' in gpuserial:
                gpuserial = gpuserial.replace('\n', ',')
            if 'NVIDIA-SMI' in gpuserial:
                gpuserial = ''
            if 'Invalid' in gpuserial:
                gpuserial = ''
            if 'Failed' in gpuserial:
                gpuserial = ''
            if 'Unable' in gpuserial:
                gpuserial = ''
            if 'Not Supported' in gpuserial:
                gpuserial = ''
        except BaseException:
            gpuserial = ''

        return gpuserial

    # Get the amount of VRAM on the NVIDIA GPU.
    def get_gpu_ram(self, smi):
        try:
            cmdgpuram = [
            	smi,
            	'--query-gpu=memory.total',
            	'--format=csv,noheader']
            rungpuram = Popen(cmdgpuram, stdout=PIPE)
            gpuram = rungpuram.communicate()[0].strip()
            gpuram = gpuram.decode("utf-8")
            gpuram = re.sub("[^0-9\n]", "", gpuram)
            if '\n' in gpuram:
                gpuram = gpuram.replace('\n', ',')
            if 'NVIDIA-SMI' in gpuram:
                gpuram = ''
            if 'Invalid' in gpuram:
                gpuram = ''
            if 'Failed' in gpuram:
                gpuram = ''
            if 'Unable' in gpuram:
                gpuram = ''
        except BaseException:
            gpuram = ''

        return gpuram

    # Get the microarchitecture of the NVIDIA GPU.
    # These values are embedded in config.
    def get_gpu_arch(self, gpu):
        gpuarch = ''
        try:
            if ',' in gpu:
                gpuarch = []
                for x in gpu.split(b','):
                    for k in list(config.gpu_arch_dict.keys()):
                        if re.search(k, gpu):
                            gpuarch.append(config.gpu_arch_dict[k])
                gpuarch = ','.join(gpuarch)
            else:
                for k in list(config.gpu_arch_dict.keys()):
                    if re.search(k, gpu):
                        gpuarch = config.gpu_arch_dict[k]
        except BaseException:
            gpuarch = ''

        return gpuarch
