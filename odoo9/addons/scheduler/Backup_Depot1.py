'''
Created on 08 Apr 2010
@author: Aden
'''
import os, sys
import time
import sys
import os #,fxl,fxl_pnlo
import shutil
import ConfigParser
import csv
import psycopg2 as dbapi2
from psycopg2 import psycopg1
import win32api
import win32net
import ConfigParser


class backupdepot:
    def __init__(self):
        self.pathname = os.path.dirname(sys.argv[0])
        self.glThisScriptPath=os.path.abspath(self.pathname)

    def findPg_dump(xLocation,xFile):
       for root, dirs, files in os.walk(xLocation):
           for f in files:
              file_Loc = root + '\\' + f
              if(f==xFile):
                  return file_Loc
       return "-"


    def goBackup(self):
        import subprocess
        import shutil

        def testDir(xpath):
           try:
               os.mkdir(xpath)
               os.rmdir(xpath)
               return True
           except:
               return False

        def CommandLine(xString):
            try:
                #print xString
                fi,fo,fe=os.popen3(xString)
                #for i in fe.readlines():
                #    print i
                #    x += i
                return True
            except:
                return False

        def OpenMapServer():
           mapDrive = r"\\10.1.32.61\bak"
           #mapDrive = r"\\192.168.0.139\coba1"
           data1 = {}
           data1['remote'] = mapDrive
           data1['local'] = "Q:"
           data1['password'] = "Firdausi"
           #data1['password'] = ""
           data1['user'] = "padalarang"
           #data1['user'] = ""
           data1['asg_type'] = 0

           data2 = {}
           data2['remote'] = mapDrive
           data2['local'] = "Q:"
           data2['password'] = "Firdausi"
           #data2['password'] = ""
           data2['username'] = "padalarang"
           #data2['username'] = ""
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
                       #print sys.exc_info()[0]
                       return False
           except:
               return False

        def CloseMapServer():
           mapDrive = r"\\10.1.32.61\bak"
           #mapDrive = r"\\192.168.0.139\coba1"
           data1 = {}
           data1['remote'] = mapDrive
           data1['local'] = "Q:"
           data1['password'] = "Firdausi"
           #data1['password'] = ""
           data1['user'] = "padalarang"
           #data1['user'] = ""
           data1['asg_type'] = 0

           data2 = {}
           data2['remote'] = mapDrive
           data2['local'] = "Q:"
           data2['password'] = "Firdausi"
           #data2['password'] = ""
           data2['username'] = "padalarang"
           #data2['username'] = ""
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
                       print sys.exc_info()[0]
                       return False
           except:
               return False




        #Cek PG dump
        #pg_dump = r"G:\ap\AADC\AS\release\2.0\addons\scheduler\93\bin\pg_dump.exe"
        pg_dump = self.glThisScriptPath+'\\93\\bin\\pg_dump.exe '
        #===========================================================================
        # if not os.path.isfile(pg_dump):
        #   drives=win32api.GetLogicalDriveStrings().split(":" )
        #   for i in drives:
        #       dr=i[-1].lower()
        #       if dr.isalpha():
        #           dr+=":\\"
        #           #print dr
        #           pg_dump = findPg_dump(dr, "pg_dump.exe")
        #           if pg_dump != "-":
        #               #print pg_dump
        #               break
        #===========================================================================

        try:
            OpenMapServer()
        except:
            pass

        #cek Local Folder 1
        dirLocal1 = r"C:\WINDOWS\addins\11\BAK\1"
        if not os.path.isdir(dirLocal1):
           data = dirLocal1.split("\\")
           i=0
           for dt in range(len(data)):
              if i==0:
                  newLoc = data[i]
                  i += 1
              else:
                  newLoc = newLoc + "\\" + data[i]
                  i += 1
                  if not os.path.isdir(newLoc):
                     os.mkdir(newLoc)
        #Lokasi backup 1
        print 'Lokasi Backup Local 1 '+dirLocal1


        #cek Local Folder 2
        dirLocal2 = ""
        stlocal2 = False
        drives=win32api.GetLogicalDriveStrings().split(":" )
        if len(drives)> 1:
           for i in drives:
               if stlocal2 == False:
                   dr=i[-1].lower()
                   if dr != "c":
                       if dr != "d":
                           if dirLocal2 == "":
                               if testDir(dr+":\coba")==True:
                                   Local2 = r":\WINDOWS\addins\11\BAK\2"
                                   Local2 = dr+Local2
                                   #print Local2
                                   if not os.path.isdir(Local2):
                                      data = Local2.split("\\")
                                      i=0
                                      newLoc=""
                                      for dt in range(len(data)):
                                         if i==0:
                                             newLoc = dr + ":"
                                             i += 1
                                         else:
                                             newLoc = newLoc + "\\" + data[i]
                                             i += 1
                                             if not os.path.isdir(newLoc):
                                                os.mkdir(newLoc)
                                      dirLocal2 = newLoc
                                      #print dirLocal2
                                      stlocal2 = True
                                   else:
                                       dirLocal2 = Local2
                                       stlocal2 = True

        else:
           #Jika hanya ada satu drive
           dirLocal2 = r"C:\WINDOWS\addins\11\BAK\2"
           if not os.path.isdir(dirLocal2):
               data = dirLocal2.split("\\")
               i=0
               for dt in range(len(data)):
                  if i==0:
                      newLoc = data[i]
                      i += 1
                  else:
                      newLoc = newLoc + "\\" + data[i]
                      i += 1
                      if not os.path.isdir(newLoc):
                         os.mkdir(newLoc)
        #Lokasi backup 2
        print 'Lokasi Backup Local 2 '+dirLocal2

        ## CHECK KONFIGURASI di SETUP.CONF

    #    newpath = ''
    #    fullpath=os.path.split(__file__)[0]
    #    xpath = fullpath.split('\\')
    #    for i in range(len(xpath)-1):
    #        newpath = newpath + xpath[i] + '\\'



        #configfile = newpath + "pn2\\wizard\\ms2connection.conf"
#        configfile = self.glThisScriptPath + "\\..\\..\\..\\..\\SIOD_setup.conf"
        configfile = self.glThisScriptPath + "\\..\\..\\openerp-server.conf"

        p=ConfigParser.SafeConfigParser()
        xKodeDepot = ""
        xDBName = ""
        xDBPort = ""
        try:
            p.read([configfile])
            section='options'
            try:
                xKodeDepot=p.get(section,'kodedepot')
            except:
                xKodeDepot = ""
            try:
                xDBName=p.get(section,'db_name')
                xDBUser=p.get(section,'db_user')
                xDBPassword=p.get(section,'db_password')
                xDBPort=p.get(section,'db_port')
            except:
                xDBName = ""; xDBPassword=''

            #Peoses backup
            if xKodeDepot != "" and xDBName != "":

                #Delete Old File
                xDelFile = xKodeDepot + '-1.dmp'
                try:
                    os.remove(dirLocal1 + "\\" + xDelFile)
                except:
                    pass

                #Rename File
                for i in range(11):
                    if i>1:
                        try:
                            xRenFile_old = dirLocal1 + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                            xRenFile_new = dirLocal1 + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                            os.rename(xRenFile_old, xRenFile_new)
                        except:
                            pass

                #Create New File
                xNewFile = xKodeDepot + '-10.dmp '
                pg_dump = "set PGPASSWORD="+xDBPassword+"&" + pg_dump + " -h localhost -p " + xDBPort + " -U "+ xDBUser+" -i -F c -E UTF8 -Z 5 -v -f "+ " " #" -W "+xDBPassword+
                xDumpFile = dirLocal1 + "\\" + xNewFile
                #print xDumpFile
                cuk = pg_dump + xDumpFile + xDBName
                #print cuk
                #================================================
                if CommandLine(cuk):
                    pass
                #================================================

                #duplicate to 2nd location
                #Delete Old File
                xDelFile = xKodeDepot + '-1.dmp'
                try:
                    os.remove(dirLocal2 + "\\" + xDelFile)
                    #pass
                except:
                    pass

                #Rename File
                for i in range(11):
                    if i>1:
                        try:
                            xRenFile_old = dirLocal2 + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                            xRenFile_new = dirLocal2 + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                            os.rename(xRenFile_old, xRenFile_new)
                        except:
                            pass

                #Create New File
                try:
                    oldLoc = dirLocal1 + "\\" + xKodeDepot + '-10.dmp'
                    newLoc = dirLocal2 + "\\" + xKodeDepot + '-10.dmp'
                    try:
                        shutil.copy2(oldLoc, newLoc)
                        #pass
                    except:
                        print sys.exc_info()[1]
                        pass
                except:
                    pass

                #cek folder server
                dirServer = "Q:\\" + xKodeDepot
                dirServerStatus = False
                if 1==1:
                    if not os.path.isdir(dirServer):
                        data = dirServer.split("\\")
                        i=0
                        for dt in range(len(data)):
                            if i==0:
                                newLoc = data[i]
                                i += 1
                            else:
                                newLoc = newLoc + "\\" + data[i]
                                i += 1
                                if not os.path.isdir(newLoc):
                                   try:
                                       os.mkdir(newLoc)
                                       dirServerStatus = True
                                       CloseMapServer()
                                   except:
                                       pass
                                else:
                                    dirServerStatus = True
                else:
                    dirServerStatus = True
                    CloseMapServer()
                #Lokasi Backup Server
                print 'Lokasi Backup Server '+dirServer

                #duplicate to server location
                if True == True:
                    if 1==1:
                        #Delete Old File
                        xDelFile = xKodeDepot + '-1.dmp '
                        try:
                            os.remove(dirServer + "\\" + xDelFile)
                            #pass
                        except:
                            pass

                        #Rename File
                        for i in range(11):
                            if i>1:
                                try:
                                    xRenFile_old = dirServer + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                                    xRenFile_new = dirServer + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                                    os.rename(xRenFile_old, xRenFile_new)
                                except:
                                    pass

                        #Create New File
                        try:
                            oldLoc = dirLocal1 + "\\" + xKodeDepot + '-10.dmp'
                            newLoc = dirServer + "\\" + xKodeDepot + '-10.dmp'
                            #newLoc = "D:\\F306\\aku.dmp"
                            try:
                                #import shutil
                                shutil.copy2(oldLoc,newLoc)
                                #pass
                            except:
                                #errornya = str(sys.exc_info()[1]).replace(" ","_")
                                #subprocess.call(["H:\\DATA\\MyJOB\\pn\\trunk2\\application_server\\bin\\addons\\scheduler\\LOGTaskScheduler.py erorgak4"+errornya], shell=True)
                                pass
                        except:
                            pass

                        #CloseMapServer()

                #selesai...................
        except:
            pass


    #===========================================================================
    # def main():
    #    print 'Proses Backup Database Depot......>>>'
    #    goBackup()
    #    print '<<<....Finished Backup Database Depot'
    #===========================================================================

if __name__ == '__main__':
    print 'Proses Backup Database Depot......>>>'
    proses = backupdepot()
    proses.goBackup()
    print '<<<....Finished Backup Database Depot'
    #main()
    #OpenMapServer()
    #print "ok"
