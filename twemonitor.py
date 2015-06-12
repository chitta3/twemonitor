#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#	TWE-lite 2525A monitor
#

import serial
import time
import datetime
import locale
import syslog
import signal
import sys
import os
import sqlite3


DBNAME = "/var/log/twelite/twelite.db"

SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 115200

ser = serial.Serial(SERIALPORT, BAUDRATE)
ser.bytesize = serial.EIGHTBITS #number of bits per bytes
ser.parity = serial.PARITY_NONE #set parity check: no parity
ser.stopbits = serial.STOPBITS_ONE #number of stop bits

#ser.timeout = None          #block read
#ser.timeout = 0             #non-block read
ser.timeout = 2              #timeout block read
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 0     #timeout for write

#print 'Starting Up Serial Monitor'

def sigint_handler(signal, frame):
    syslog.closelog()
    ser.close()
    con.close()
    print("Interrupted")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

try:
    os.chdir('/var/log')
    ser.open()
#   syslog.openlog("twelite", syslog.LOG_PID | syslog.LOG_PERROR, syslog.LOG_LOCAL0)
    syslog.openlog("twelite", syslog.LOG_PID, syslog.LOG_LOCAL0)

except Exception, e:
    print "error open serial port: " + str(e)
    ser.close()
    syslog.closelog()
    exit()

if ser.isOpen():
    try:
        ser.flushInput() #flush input buffer, discarding all its contents
        ser.flushOutput()#flush output buffer, aborting current output

        con = sqlite3.connect(DBNAME, isolation_level=None)

        while True:
            response = ser.readline()
            line = response.split(";")
            if len(line) > 3:
                d = datetime.datetime.now()
                line = line + [d.strftime("%Y%m%d%H%M%S")]
                syslog.syslog("{0[16]};{0[5]};{0[6]}".format(line))

                c = con.execute("""SELECT * FROM data WHERE id = '{0[5]}';""".format(line))
                r = c.fetchall()
                if len(r) > 0:
                    c = con.execute("""UPDATE data
                        SET dtime='{0[16]}', batt='{0[6]}'
                        WHERE id = '{0[5]}';""".format(line))
                else:
                    c = con.execute("""INSERT INTO
                        data(id, batt, dtime)
                        VALUES('{0[5]}', '{0[6]}', '{0[16]}');""".format(line))

        ser.close()
        syslog.closelog()
        con.close()

    except Exception, e:
        print "error communicating...: " + str(e)

else:
    print "cannot open serial port "
