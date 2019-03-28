'''
Created on 08 Apr 2010
@author: Aden
'''
import os, sys
import shutil
import ConfigParser
import win32api
import win32net


class backupdepot:
    def __init__(self):
        self.pathname = os.path.dirname(sys.argv[0])
        self.glThisScriptPath=os.path.abspath(self.pathname)
#        print "self.pathname ", self.pathname
#        print "self.glThisScriptPath ", self.glThisScriptPath

    def goBackup(self,localdrive,mapdrive):
        
        def testDir(xpath):
            try:
                os.mkdir(xpath)
                os.rmdir(xpath)
                return True
            except: 
                return False

        def CommandLine(xString):
            try:
                os.popen3(xString)
                return True
            except:
                return False

        def OpenMapServer(mapdrive):
            mapsts=[]
            for data in mapdrive:
                data['asg_type'] = int(data['asg_type'])
                map1 = {'local':data['local'],'sts':False}
                try:
                    try: win32net.NetUseDel(None, data['local'], 2)
                    except: pass
                    try: 
                        win32net.NetUseAdd(None, 2, data)
                        map1['sts']= True
                    except: 
                        map1['sts']= False
                except: map1['sts']= False
                if map1['sts']: mapsts.append(map1)
            return mapsts
            

        def CloseMapServer(mapsts):
            for data in mapsts:
                try: win32net.NetUseDel(None, data['local'], 2)
                except: print sys.exc_info()[0]
            return True



        
        ## ===========================================================================
        ## MAIN START
        ## ===========================================================================
        
        pg_dump = self.glThisScriptPath+'\\postgresql_bin\\pg_dump.exe '
		

        ## GET MAPPING DRIVE 
        mapsts = OpenMapServer(mapdrive)
        
        
        ## GET DEFAULT LOKAL DRIVE 
        dirLocal1 = localdrive + r"\1"
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
                    if not os.path.isdir(newLoc): os.mkdir(newLoc)
        print 'Lokasi Backup Local 1 '+dirLocal1


        ## GET OTHER LOKAL DRIVE 
        dirLocal2 = ""
        stlocal2 = False
        drives=win32api.GetLogicalDriveStrings().split(":" )
        if len(drives)> 1:
            for i in drives:
                if stlocal2 == False:
                    dr=i[-1].lower()
                    if dr != "c":
                        if dr != "a":
                            if dirLocal2 == "":
                                if testDir(dr+":\coba")==True:
                                    Local2 = r":\WINDOWS\addins\11\BAK\2"
                                    Local2 = dr+Local2
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
                                                if not os.path.isdir(newLoc): os.mkdir(newLoc)
                                        dirLocal2 = newLoc
                                        stlocal2 = True
                                    else:
                                        dirLocal2 = Local2
                                        stlocal2 = True
        else:
            dirLocal2 = localdrive + r"\2"
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
                        if not os.path.isdir(newLoc): os.mkdir(newLoc)
        print 'Lokasi Backup Local 2 '+dirLocal2


        ## CHECK KONFIGURASI di SETUP.CONF
#        configfile = self.glThisScriptPath + "\\..\\..\\..\\..\\SIOD_setup.conf"
        configfile = self.glThisScriptPath + "\\..\\..\\openerp-server.conf"
        p=ConfigParser.SafeConfigParser()
        
        xKodeDepot = ""
        xDBName = ""
        xDBPort = ""
        try:
            p.read([configfile])
            section='options'
            try: xKodeDepot=p.get(section,'kodedepot')
            except: xKodeDepot = ""
            try:
                xDBName=p.get(section,'db_name')
                xDBUser=p.get(section,'db_user')
                xDBPassword=p.get(section,'db_password')
                xDBPort=p.get(section,'db_port')
            except:
                xDBName = "" 
                xDBPassword=''

            
            if xKodeDepot != "" and xDBName != "":
                
                ## ================================
                ## BACKUP TO DEFAULT LOKAL DRIVE
                ## ================================
                
                #Delete Old File
                xDelFile = xKodeDepot + '-1.dmp'
                try: os.remove(dirLocal1 + "\\" + xDelFile)
                except: pass
                #Rename File
                for i in range(11):
                    if i>1:
                        try:
                            xRenFile_old = dirLocal1 + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                            xRenFile_new = dirLocal1 + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                            os.rename(xRenFile_old, xRenFile_new)
                        except: pass
                #Create New File
                xNewFile = xKodeDepot + '-10.dmp '
                pg_dump = "set PGPASSWORD="+xDBPassword+"&" + pg_dump + " -h localhost -p " + xDBPort + " -U "+ xDBUser+" -i -F c -E UTF8 -Z 5 -v -f "+ " " #" -W "+xDBPassword+
                xDumpFile = dirLocal1 + "\\" + xNewFile
                
                if CommandLine(pg_dump + xDumpFile + xDBName): pass

                
                ## ================================
                ## COPY TO OTHER LOKAL DRIVE
                ## ================================
                
                #Delete Old File
                xDelFile = xKodeDepot + '-1.dmp'
                try: os.remove(dirLocal2 + "\\" + xDelFile)
                except: pass
                #Rename File
                for i in range(11):
                    if i>1:
                        try:
                            xRenFile_old = dirLocal2 + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                            xRenFile_new = dirLocal2 + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                            os.rename(xRenFile_old, xRenFile_new)
                        except: pass
                #Create New File
                try:
                    oldLoc = dirLocal1 + "\\" + xKodeDepot + '-10.dmp'
                    newLoc = dirLocal2 + "\\" + xKodeDepot + '-10.dmp'
                    try:
                        shutil.copy2(oldLoc, newLoc)
                    except:
                        print "COPY TO OTHER LOKAL DRIVE, FAILED"
                        print sys.exc_info()[1]
                        pass
                except: pass


                ## ================================
                ## COPY TO MAPPING DRIVE
                ## ================================
                
                for row in mapsts:
                    dirServer = row['local'] + "\\" + xKodeDepot
                    
                    
                    ## CREATE KODE DEPOT
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
                                    except: pass
                    
                    ## COPY BACKUP DB
                    if os.path.isdir(dirServer):
                        #Delete Old File
                        xDelFile = xKodeDepot + '-1.dmp '
                        try: os.remove(dirServer + "\\" + xDelFile)
                        except: pass
                        #Rename File
                        for i in range(11):
                            if i>1:
                                try:
                                    xRenFile_old = dirServer + "\\" + xKodeDepot + "-" + str(i) +'.dmp'
                                    xRenFile_new = dirServer + "\\" + xKodeDepot + "-" + str(i-1) +'.dmp'
                                    os.rename(xRenFile_old, xRenFile_new)
                                except: pass
                        #Create New File
                        try:
                            oldLoc = dirLocal1 + "\\" + xKodeDepot + '-10.dmp'
                            newLoc = dirServer + "\\" + xKodeDepot + '-10.dmp'
                            try: shutil.copy2(oldLoc,newLoc)
                            except: pass
                        except: pass
                
        except: pass
        
        ## GET MAPPING DRIVE 
        CloseMapServer(mapsts)


if __name__ == '__main__':
    
    ## GET CONFIG
    pathname = os.path.dirname(sys.argv[0])
    glThisScriptPath = os.path.abspath(pathname)
    conf = ConfigParser.ConfigParser()
    conf.read([glThisScriptPath+'/setup.conf'])
    localdrive = conf.get('basic','dirLocal')
    
    if len(sys.argv)>1:
        try: mapping = eval(conf.get('basic','mapping_%s' %(sys.argv[1])))
        except: mapping = [] 
    else: mapping = eval(conf.get('basic','mapping'))
        
    mapdrive = []
    for row in mapping:
        data = {}
        data['remote'] = conf.get(row,'remote')
        data['local'] = conf.get(row,'local')
        data['password'] = conf.get(row,'password')
        data['user'] = conf.get(row,'user')
        data['asg_type'] = conf.get(row,'asg_type')
        mapdrive.append(data)
    
    print 'Proses Backup Database Depot......>>>'
    proses = backupdepot()
    proses.goBackup(localdrive,mapdrive)
    print '<<<....Finished Backup Database Depot'
    
