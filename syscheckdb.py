#!/tools/bin/python

import sys
from optparse import OptionParser

import psycopg2
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import DictCursor

import config

# Add options for scanning all machines (-a) for a specific attribute,
# or one machine for all of its info by name (-m).
def parse_options():
    parser = OptionParser()
    parser.add_option("-a", "--all", action="store", dest="all",
                      help="Query all machines in the database containing <arg>")
    parser.add_option("-m", "--machine", type="string", action="store",
                      dest="machine", help="Query a specific machine in the database")

    (options, args) = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    return options, args

# Connect to our postgres instance.
sqldb = connect(config.sql_dict["home"])


# Connect to the database, parse options, and query postgres for data.
def check_system_db():
    rindex = 0
    cursor = sqldb.cursor()
    options, args = parse_options()

    # If -m option, search by name entered.
    if options.machine:
        cursor.execute(
            " SELECT system_check.*"
            + " FROM system_check "
            #            + " ON name = host "
            + " WHERE lastuser LIKE '{0}'".format(options.machine)
            + " OR system_check.name LIKE '{0}'".format(options.machine)
            + " OR gpu LIKE '{0}'".format(options.machine)
        )

    # If -a option, search all machines by attribute entered.
    elif options.all:
        cursor.execute(
            " SELECT system_check.*"
            + " FROM system_check "
            #            + " ON name = host "
            #            + " ON system_check.name"
            + " WHERE system_check.name LIKE '{0}'".format(options.all)
            + " OR system_check.class LIKE '{0}'".format(options.all)
            + " OR system_check.ipaddr LIKE '{0}'".format(options.all)
            + " OR system_check.macaddr LIKE '{0}'".format(options.all)
            + " OR system_check.cpuname LIKE '{0}'".format(options.all)
            + " OR system_check.procs LIKE '{0}'".format(options.all)
            + " OR system_check.ram LIKE '{0}'".format(options.all)
            + " OR system_check.ramspeed LIKE '{0}'".format(options.all)
            + " OR system_check.gpu LIKE '{0}'".format(options.all)
            + " OR system_check.gpuserial LIKE '{0}'".format(options.all)
            + " OR system_check.ssd LIKE '{0}'".format(options.all)
            + " OR system_check.tablet LIKE '{0}'".format(options.all)
            + " OR system_check.monitor1 LIKE '{0}'".format(options.all)
            + " OR system_check.serial1 LIKE '{0}'".format(options.all)
            + " OR system_check.monitor2 LIKE '{0}'".format(options.all)
            + " OR system_check.serial2 LIKE '{0}'".format(options.all)
            + " OR CAST(system_check.lastupdate AS CHAR) LIKE '{0}'".format(options.all)
            + " OR system_check.lastuser LIKE '{0}'".format(options.all)
            + " OR CAST(system_check.lastlogon AS CHAR) LIKE '{0}'".format(options.all)
            + " OR system_check.lastos LIKE '{0}'".format(options.all)
            + " OR system_check.state LIKE '{0}'".format(options.all)
            + " OR system_check.uptime LIKE '{0}'".format(options.all)
            + " OR CAST(system_check.nvme AS CHAR) LIKE '{0}'".format(options.all)
            + " OR system_check.mbserial LIKE '{0}'".format(options.all)
            + " OR system_check.gpuram LIKE '{0}'".format(options.all)
            + " OR CAST(system_check.gpuarch AS CHAR) LIKE '{0}'".format(options.all)
        )

    result = cursor.fetchall()
    cursor.close()

    cursor = sqldb.cursor()
    cursor.execute(
        " select column_name "
        + " from INFORMATION_SCHEMA.COLUMNS where table_name = 'system_check' "
    )

    result2 = cursor.fetchall()

    spacing = 12

    print("")

    # For each column in the row.
    for item in result:
        # For item in each row.
        for entry in result2:
            entry_string = ''.join(str(entry[0]))
            item_string = str(item[rindex])

            # If empty entry, indicate with "-".
            if len(item_string) == 0 or item_string == "None":
                item_string = "-"

            # Calculate empty space needed for string to fit nicely.
            empty_space = spacing - len(str(entry[0]))
            # Add the appropriate empty space.
            spaces = str(empty_space * " ")
            # Create the entry with the string + empty space.
            entry_string = spaces + entry_string

            # Indicate between each entry.
            if entry == ('name',):
                print("----------------------------------------------------")

            entry_row = "{0}: {1}".format(entry_string, item_string)
            print(entry_row)

            # Keep track of mutliple items in each row.
            rindex += 1

        # Reset items in each row.
        rindex = 0

    print("")


if __name__ == "__main__":
    check_system_db()
