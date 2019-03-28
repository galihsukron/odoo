# FIle ini dibuat untuk mempermudah pembuatan 2 buah service dan 3 buah bat file untuk menjalankan
# Application Server OpenERP di direktory ini.
import os
import sys
import datetime

if len(sys.argv)>1:
    descproses = str(sys.argv[1]).replace('_', ' ')
else:
    descproses = "coba"

f=open('LOG_taskScheduler.txt', 'a')
f.write( "[ "+str(datetime.datetime.now())+" ] proses script 2 run "+descproses+"\n" )
#s = raw_input('--> ')

#print timeproses
#print descproses
#print 'ok'



