'''
Created on 07 Juli 2010

@author: Aden
'''
import subprocess
import re
import os
import sys

import string
import time
import datetime
import threading
from time import gmtime,strftime

import win32api
import win32net

import ConfigParser
import csv

class Task( threading.Thread ):
    def __init__( self, action, loopdelay, initdelay ):
        self._action = action
        self._loopdelay = loopdelay
        self._initdelay = initdelay
        self._running = 1
        threading.Thread.__init__( self )

    def __repr__( self ):
        return '%s %s %s' % (
            self._action, self._loopdelay, self._initdelay )

    def run( self ):
        if self._initdelay:
            time.sleep( self._initdelay )
        self._runtime = time.time()
        while self._running:
            start = time.time()
            self._action()
            self._runtime += self._loopdelay
            time.sleep( self._runtime - start )

    def stop( self ):
        self._running = 0

class Scheduler:
    def __init__( self ):
        self._tasks = []

    def __repr__( self ):
        rep = ''
        for task in self._tasks:
            rep += '%s\n' % `task`
        return rep

    def AddTask( self, action, loopdelay, initdelay = 0 ):
        task = Task( action, loopdelay, initdelay )
        self._tasks.append( task )

    def StartAllTasks( self ):
        for task in self._tasks:
            task.start()

    def StopAllTasks( self ):
        for task in self._tasks:
            print 'Stopping task', task
            task.stop()
            task.join()
            print 'Stopped'

# parse fields utk import master data (status: TESTING)
def parsefieldsmaster(reader, importEquivalences=[],arrHead=[]):
        baris=0;kol=0;iter=-1;pk=''
        if arrHead:
            baris=arrHead[0]
            kol=arrHead[1]

        # read the first line of the file (it contains columns titles)
        f=[]
        for row in reader:
            iter+=1
            if row and iter==baris:
               f = row
               break

#        print f
        #assign title to index e.g. 'kl_do=0'
        dicKolom={}
        arrKolom=[]
        for i in range(kol,len(f)):
#            kolom=re.sub('[%s]' % re.escape(string.punctuation), '', f[i]) #remove punctuattion
            kolom1=str(f[i]).replace(' ','').replace('\xa0','') #buang spaces
            dicKolom[kolom1]=i

            #jika format nama kolomnya 'tablename.fieldname'
            kolom2=kolom1.split('.')
            if len(kolom2)>1: kolom=kolom2[-1]
            else: kolom=kolom1

            arrKolom.append([kolom,kolom1])

        if not importEquivalences:
            equivalencesImpor=arrKolom
        else:
            equivalencesImpor=[equivalence for equivalence in importEquivalences]
            for equivalence in equivalencesImpor:
                equivalence[1]=str(equivalence[1]).replace(' ','').replace('\xa0','') #buang spaces
#                equivalence[1]=str(equivalence[1]).replace(' ','').lower().replace('\xa0','') #buang spaces

        #TASK SPECIFIC
        # read the rest of the file
        dataArr=[]

        for row in reader: #the variable name gk boleh diganti krn dipakai di equivalencesImpor
#            print row
                #line += 1
            # skip empty rows and rows where the kpi field (=first field) is empty
            try:
                if (row[0]==''):
                    continue
            except:
                continue

            #assign the value to data dictionary

            data={'name':0}
            for equivalence in equivalencesImpor:
#                kolom=str(equivalence[1]).replace(' ','').lower().replace('\xa0','') #buang spaces
                kolom=equivalence[1]
                kolomInd=dicKolom[kolom]
                #print equivalence, kolomInd
                try:
                    isi=row[kolomInd].replace('\xa0','')
                    data[equivalence[0]]=isi
                    if equivalence[2]:
                        pk=equivalence[0]
                except: pass
#                data[equivalence[0]]=eval(equivalence[1])

#            print data
            dataArr.append(data)

#        reconstructShipment(cr,uid,pooler,dataArr)

        return dataArr,pk

#parsefieldsmaster()

def OpenMapServer():
   mapDrive = r"\\10.1.32.61\bak"
   data1 = {}
   data1['remote'] = mapDrive
   data1['local'] = "Q:"
   data1['password'] = "Firdausi"
   data1['user'] = "padalarang"
   data1['asg_type'] = 0

   data2 = {}
   data2['remote'] = mapDrive
   data2['local'] = "Q:"
   data2['password'] = "Firdausi"
   data2['username'] = "padalarang"
   data2['asg_type'] = 0

   try:
       try:
           win32net.NetUseDel(None, data1['local'], 2)
       except:
           try:
               win32net.NetUseDel(None, data2['local'], 2)
           except:
               pass
       try:
           win32net.NetUseAdd(None, 2, data1)
           return True
       except:
           try:
               win32net.NetUseAdd(None, 2, data2)
               return True
           except:
               print sys.exc_info()[1]
               return False
   except:
       return False

def CloseMapServer():
   mapDrive = r"\\10.1.32.61\bak"
   data1 = {}
   data1['remote'] = mapDrive
   data1['local'] = "Q:"
   data1['password'] = "Firdausi"
   data1['user'] = "padalarang"
   data1['asg_type'] = 0

   data2 = {}
   data2['remote'] = mapDrive
   data2['local'] = "Q:"
   data2['password'] = "Firdausi"
   data2['username'] = "padalarang"
   data2['asg_type'] = 0

   try:
       try:
           win32net.NetUseDel(None, data1['local'], 2)
           return True
       except:
           try:
               win32net.NetUseDel(None, data2['local'], 2)
               return True
           except:
               print sys.exc_info()[1]
               return False
   except:
       return False


gJmlRow = 0
gScope = []
gIdentifikasi = []
gScript2run = []
gFrequency = []
gStartTime = []
gRepeat = []
gRepeat_Interval = []
gDepotTimeShiftFromStartTime = []
gKeterangan = []
gUrut = []

def getCodeDepot():
    CodeDepot = ''
    p=ConfigParser.SafeConfigParser()
    confname=''
    try:
        newpath = ''
        fullpath=os.path.split(__file__)[0]
        xpath = fullpath.split('\\')
        for i in range(len(xpath)-1):
            newpath = newpath + xpath[i] + '\\'
        confname = newpath + "pn2\\wizard\\ms2connection.conf"
        try:
            p.read([confname])
            section='MachineSpesific'
            CodeDepot=p.get(section,'kodedepot')
        except:
            print 'Error 2 on Get Code Depot',sys.exc_info()[1]
    except:
        print 'Error 1 on Get Code Depot',sys.exc_info()[1]

    return CodeDepot


def getSyncmasterConfiguration():
    global gJmlRow
    global gScope
    global gIdentifikasi
    global gScript2run
    global gFrequency
    global gStartTime
    global gNextTime
    global gRepeat
    global gRepeat_Interval
    global gDepotTimeShiftFromStartTime
    global gKeterangan
    global gUrut
    SycnName = ''
    try:
        newpath = ''
        fullpath=os.path.split(__file__)[0]
        xpath = fullpath.split('\\')
        for i in range(len(xpath)-1):
            newpath = newpath + xpath[i] + '\\'
        SycnName = newpath + "syncmaster\\syncmaster_configuration.csv"
        try:
            reader = csv.reader(open(SycnName,"rb"))
            dataArr,pk=parsefieldsmaster(reader)
            gJmlRow = len(dataArr)
            gScope = []
            gIdentifikasi = []
            gScript2run = []
            gFrequency = []
            gStartTime = []
            gNextTime = []
            gRepeat = []
            gRepeat_Interval = []
            gDepotTimeShiftFromStartTime = []
            gKeterangan = []
            gUrut = []
            print "###############################################################"
            print "==============================================================="
            print "      SIOD scheduler                                           "
            print "      Dont Close!!!                                            "
            print "---------------------------------------------------------------"
            print 'Task Schedule :'
            for dtArr in dataArr:
                print '   Time : ',dtArr['starttime'],'   Name : ',dtArr['Identifikasi']
                gScope.append(str(dtArr['scope']))
                gIdentifikasi.append(str(dtArr['Identifikasi']))
                gScript2run.append(str(dtArr['script2run']))
                gFrequency.append(str(dtArr['frequency']))
                gStartTime.append(str(dtArr['starttime']))
                gNextTime.append(str('00:00:00'))
                gRepeat.append(str(dtArr['repeat']))
                gRepeat_Interval.append(str(dtArr['Repeatinterval']))
                gDepotTimeShiftFromStartTime.append(str(dtArr['DepotTimeShiftFromStartTime']))
                gKeterangan.append(str(dtArr['Keterangan']))
                gUrut.append(str(dtArr['Urut']))
            print "---------------------------------------------------------------"
            print "###############################################################"
        except:
            print 'Error 2 on Get Syncmaster Configuration',sys.exc_info()[1]
    except:
        print 'Error 1 on Get Syncmaster Configuration',sys.exc_info()[1]


def getDepotOrder(CodeDepot):
    orderNumber = 0
    csvName = ''
    try:
        newpath = ''
        fullpath=os.path.split(__file__)[0]
        xpath = fullpath.split('\\')
        for i in range(len(xpath)-1):
            newpath = newpath + xpath[i] + '\\'
        csvname = newpath + "syncmaster\\depotorder.csv"
        try:
            reader = csv.reader(open(csvname,"rb"))
            dataArr,pk=parsefieldsmaster(reader)
            for dtArr in dataArr:
                if (dtArr['kode_depot']==CodeDepot):
                    orderNumber = int(dtArr['urutan'])
                    return orderNumber
        except:
            print 'Error 2 on Get Depot Order',sys.exc_info()[1]
    except:
        print 'Error 1 on Get Depot Order',sys.exc_info()[1]

    return orderNumber


def RunProses(script2run,namescript):
    import subprocess
    import datetime
    
    '''
    untuk mulai proses run script
    '''
    namescript = str(namescript).replace(" ", "_")
    #f=open('LOG_taskScheduler.txt', 'a')
    #f.write( "[ "+str(datetime.datetime.now())+" ] proses script 2 run "+namescript+"\n" )
    #print namescript
    #print script2run
    newpath = ''
    try:
        fullpath=os.path.split(__file__)[0]
        xpath = fullpath.split('\\')
        for i in range(len(xpath)-1):
            newpath = newpath + xpath[i] + '\\'
    except:
        pass

    '''Start For Real !!!!!!'''
    if(script2run==''):
        print 'Nothing Script To Run'
    else:
        command = newpath + str(script2run)
        try:
            if os.name == 'nt':
                #os.system('start ' + command)
                #execfile(command)
                subprocess.call([command], shell=True)
                #TULIS LOG
                subprocess.call([newpath+"scheduler\\LOGTaskScheduler.py "+namescript+""], shell=True)
                #pass
            else:
                subprocess.call([command], shell=True)
                #TULIS LOG
                subprocess.call([newpath+"scheduler\\LOGTaskScheduler.py "+namescript+""], shell=True)
                #os.system(command)
                #execfile(command)
        except:
            print 'Error Run Proses ',sys.exc_info()[1]
    '''End For Real !!!!!!'''

    '''Start For Testing !!!!!!'''
    #===========================================================================
    #command = str(script2run)
    #try:
    #    if os.name == 'nt':
    #        os.system('start ' + command)
    #    else:
    #        os.system(command)
    #except:
    #    print 'Error Run Proses ',sys.exc_info()[0]
    #===========================================================================
    '''End For Testing !!!!!!'''


def Task2():
    while True:
        time.sleep(1)
        DATE_FORMAT = "%H:%M:%S"
        #print strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        datetimelocal = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        #print strftime("%H:%M:%S", time.localtime())
        timelocal = strftime("%H:%M:%S", time.localtime())
        if(timelocal == '00:00:01'):  #-> Start Time & New Variabel From syncmaster_configuration.csv
            getSyncmasterConfiguration()
        if(timelocal == '23:59:59'):  #-> End Of Time & Get New syncmaster_configuration.csv From Central
            for i in range(gJmlRow):
                if (gIdentifikasi[i].lower() == 'taskschedulerpreparation'):
                    if (gScope[i] != 'none'):
                        #pass   #  --> untuk Fase II dimana akan update schedule dari Server Central
                        if OpenMapServer():
                            newpath = ''
                            fullpath=os.path.split(__file__)[0]
                            xpath = fullpath.split('\\')
                            for i in range(len(xpath)-1):
                                newpath = newpath + xpath[i] + '\\'
                            SycnServer = r"Q:\\syncmaster_configuration.csv"
                            SycnDepot = newpath + "syncmaster\\syncmaster_configuration.csv"
                            try:
                                reader = csv.reader(open(SycnServer,"rb"))
                                csvwriter = csv.writer(file(SycnDepot, "wb"))
                                for row in reader:
                                    csvwriter.writerow(row)
    
                                CloseMapServer()
                                #print 'suksesss'
                            except:
                                print 'Error Update SyncMaster Configuration',sys.exc_info()[1]
    
        if (timelocal > '00:00:01' and timelocal < '23:59:59'): # > Cek Variabel Filter
            #print timelocal
            for i in range(gJmlRow):
                #if (gIdentifikasi[i] == 'test'):
                if (gScope[i].lower()=='global' or gScope[i].upper()==getCodeDepot()):
                    xStartTime = gStartTime[i]
                    original = datetime.datetime.strptime(xStartTime, DATE_FORMAT)
                    xDepotTime = int(gDepotTimeShiftFromStartTime[i].replace('menit',''))
                    xUrutan = getDepotOrder(getCodeDepot())
                    newtime = original + datetime.timedelta(minutes=int(xDepotTime*xUrutan))
                    xperfectTime = newtime.strftime(DATE_FORMAT)
                    #print 'localTime',timelocal
                    #print gIdentifikasi[i],'perfectTime',xperfectTime
                    #For Repeat Command
                    if (gNextTime[i] != '00:00:00'):
                        if (gNextTime[i] <= timelocal):
                            xRepeat = int(gRepeat[i])
                            xRepeatInterval = int(gRepeat_Interval[i].replace('menit',''))
                            if(xRepeat > 0 and xRepeatInterval > 0):
                                original = datetime.datetime.strptime(gStartTime[i], DATE_FORMAT)
                                newtime = original + datetime.timedelta(minutes=xRepeatInterval) + datetime.timedelta(minutes=int(xDepotTime*xUrutan))
                                xperfectTime = newtime.strftime(DATE_FORMAT)
                                #print xperfectTime
                                xRepeat = xRepeat - 1
                                gStartTime[i] = str(xperfectTime)
                                gNextTime[i] = str(xperfectTime)
                                gRepeat[i] = str(xRepeat)
                                try:
                                    print datetimelocal,' proses script 2 run ',gIdentifikasi[i]
                                    RunProses(gScript2run[i],gIdentifikasi[i])
                                    print 'Time Next Proses : ',gStartTime[i],'   Name : ',gIdentifikasi[i],' queue proses : ',gRepeat[i]
                                except:
                                    print 'Error Execute Script To Run',sys.exc_info()[1]
                    
                    else:
                        #For Once Command
                        if(xperfectTime == timelocal):
                            xRepeat = int(gRepeat[i])
                            xRepeatInterval = int(gRepeat_Interval[i].replace('menit',''))
                            if(xRepeat > 0 and xRepeatInterval > 0):
                                original = datetime.datetime.strptime(gStartTime[i], DATE_FORMAT)
                                newtime = original + datetime.timedelta(minutes=xRepeatInterval) + datetime.timedelta(minutes=int(xDepotTime*xUrutan))
                                xperfectTime = newtime.strftime(DATE_FORMAT)
                                #print xperfectTime
                                xRepeat = xRepeat - 1
                                gStartTime[i] = str(xperfectTime)
                                gNextTime[i] = str(xperfectTime)
                                gRepeat[i] = str(xRepeat)
                            try:
                                print datetimelocal,' proses script 2 run ',gIdentifikasi[i]
                                RunProses(gScript2run[i],gIdentifikasi[i])
                                print 'Time Next Proses : ',gStartTime[i],'   Name : ',gIdentifikasi[i],' queue proses : ',gRepeat[i]
                            except:
                                print 'Error Execute Script To Run',sys.exc_info()[1]

def running():
    getSyncmasterConfiguration()
    Task2()
    #s = Scheduler()
    #s.AddTask(Task1,1.0,0)
    #s.StartAllTasks()
    #raw_input()
    #s.StopAllTasks()

if __name__ == '__main__':
    running()
    #RunProses("scheduler\\Backup_Depot1.py","Coba Backup")











