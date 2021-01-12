#!/usr/bin/env python

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import connect
# Config file for storing configurable variables.
import config
# Modules per OS
from linux_platform import LinuxPlatform
from windows_platform import WindowsPlatform
from cross_platform import CrossPlatform
import os
import sys
import time
import datetime
import traceback
import smtplib
import warnings
from optparse import OptionParser
from email.message import Message
from subprocess import Popen, PIPE
os.environ['PATH'] += os.pathsep + '/tools/bin'
os_version = CrossPlatform().get_os_version()

# Ignore sys warnings.
if not sys.warnoptions:
    warnings.simplefilter("ignore")

# Base class for system_check. This class will determine all major pieces
# of config, site, os, db etc.
class SystemCheck:
    def __init__(self, sql_dict):
        self.sysos = CP.get_os()

        if self.sysos == 'linux':
            self.location = LinuxPlatform().get_location()
        elif self.sysos == 'windows':
            self.location = WindowsPlatform().get_location()

        if self.location in sql_dict:
            self.db_info = sql_dict[self.location]
        else:
            print("Location not found.")

    # Establishes a connection to DD's SQL database
    def sql_connect(self, db_info):
        self.dbh = connect("{0}".format(db_info))
        self.dbh.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cursor = self.dbh.cursor(cursor_factory=DictCursor)
        sql = "SET client_encoding = 'UTF8'"
        self.cursor.execute(sql)

    # Actually updates the db
    def sql_update(self, sql):
        self.sql_connect(self.db_info)
        self.cursor.execute(sql)
        self.dbh.close()

    # Retrieve info from the db
    def sql_query(self, sql):
        self.sql_connect(self.db_info)
        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        self.dbh.close()

        return result

    # Checks to see if the host should be reporting
    def check_allowed(self, name):
        mclass = "NA"
        notallname = ['puppet', 'remotesupport', 'term-']

        if any(nope in name for nope in notallname):
            sys.exit(1)

        return mclass

    # Checks if an entry exists for the host and creates an empty one if not
    def check_sql(self, name):
        sqlname = "select name from system_check where name='{0}'".format(name)
        result = self.sql_query(sqlname)

        try:
            result["name"] == name
        except Exception as e:
            sqlupdate = "insert into system_check (name) values ('{0}')".format(
                name)
            SC.sql_update(sqlupdate)

    # Determine what values to push to SQL
    def get_updates(self):
        name = CP.get_name()
        mclass = self.check_allowed(name)
        location = self.location
        ipaddr = CP.get_ip()
        smi = r'nvidia-smi'

        if self.sysos == 'windows':
            osclass = WindowsPlatform()
        elif self.sysos == 'linux':
            osclass = LinuxPlatform()

        # Including this option for whether or not we want Race to handle hyperthread reporting.
        # "True"  = all threads (physical + virtual)
        # "False" = physical threads only
        hyperthread_reporting_enabled = False

        # Cross platform check
        macaddr = CP.get_mac()
        lastupdate = CP.get_current_time()
        mbserial = osclass.get_mb_serial()
        gpu = CP.get_gpu(smi)
        gpuserial = CP.get_gpu_serial(smi)
        gpuram = CP.get_gpu_ram(smi)
        gpuarch = CP.get_gpu_arch(gpu)
        lastos = CP.get_os_version()
        ram = osclass.get_ram()
        ramspeed = osclass.get_ram_speed()
        ssd = osclass.get_ssd()
        tablet = osclass.get_tablet()
        monitor1, serial1, monitor2, serial2 = osclass.get_monitor_info()
        lastuser, lastlogon = osclass.get_last_info()
        procs, hyperthread, cpuname = osclass.get_procs(
            hyperthread_reporting_enabled)
        uptime = osclass.get_uptime()
        nvme = osclass.check_nvme()

        # The BIG general push.
        sqlupdate = "update system_check set ipaddr='{0}', macaddr='{1}', cpuname = '{2}', procs='{3}', \
        hyperthread='{4}', ram='{5}', ramspeed='{6}', gpu='{7}', gpuserial='{8}', gpuram='{9}', \
        gpuarch='{10}', ssd='{11}', tablet='{12}', monitor1='{13}', serial1='{14}', monitor2='{15}', \
        serial2='{16}', lastupdate='{17}', lastuser='{18}', lastlogon='{19}', lastos='{20}', \
        uptime='{21}', mbserial='{22}', state='up', nvme='{23}' where name='{24}'" \
        .format(ipaddr, macaddr, cpuname, procs, hyperthread, ram, ramspeed, gpu, gpuserial, gpuram, \
                gpuarch, ssd, tablet, monitor1, serial1, monitor2, serial2, lastupdate, lastuser, lastlogon, \
                lastos, uptime, mbserial, nvme, name)

        # Linux specific check.
        if self.sysos == 'linux':
            #LinuxPlatform() checks here
            #
            #
            
            # The BIG linux push, just in case linux needs extra parameters.
            sqlupdate = "update system_check set ipaddr='{0}', macaddr='{1}', cpuname = '{2}', procs='{3}', \
	    hyperthread='{4}', ram='{5}', ramspeed='{6}', gpu='{7}', gpuserial='{8}', gpuram='{9}', \
            gpuarch='{10}', ssd='{11}', tablet='{12}', monitor1='{13}', serial1='{14}', monitor2='{15}', \
            serial2='{16}', lastupdate='{17}', lastuser='{18}', lastlogon='{19}', lastos='{20}', \
            uptime='{21}', mbserial='{22}', state='up', nvme='{23}' where name='{24}'" \
            .format(ipaddr, macaddr, cpuname, procs, hyperthread, ram, ramspeed, gpu, gpuserial, gpuram, \
                    gpuarch, ssd, tablet, monitor1, serial1, monitor2, serial2, lastupdate, lastuser, lastlogon, \
                    lastos, uptime, mbserial, location, nvme, name)

        self.check_sql(name)

        return name, ipaddr, sqlupdate

    # Push to SQL
    def do_update(self):
        try:
            name, ipaddr, sqlupdate = self.get_updates()
            self.check_sql(name)
            self.sql_update(sqlupdate)
        except Exception as e:
            print("Failed to update database.")
            print(e)


if __name__ == '__main__':
    CP = CrossPlatform()
    SC = SystemCheck(config.sql_dict)

    try:
        SC.do_update()
    except Exception as e:
        print(e)
        print((traceback.format_exc()))
