'''
Created on 03 November 2010

@author: Aden

description:
Script ini akan dipangil oleh sceduler dan saat eksekusi script ini akan memindahkan file 3 hari dari tanggal sekarang 
kedalam folder sesuai last modified file tersebut. 
'''

import os
import time
import datetime
import shutil


def CekNCreateFolder(dirFolder):
    if not os.path.isdir(dirFolder):
        os.mkdir(dirFolder)
    return dirFolder

def managefile():
    #lokasi = r'E:\datacoba\DATA_TAS'
    lokasi = r'C:\SIODExchange\DATA_TAS'
    #srclokasi = r'E:\datacoba\DATA_TAS\BAK'
    srclokasi = r'C:\SIODExchange\DATA_TAS\BAK'
    nowDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    limitDate = datetime.datetime.strptime(nowDate, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=int(3))
    
    fileList = []
    for file in os.listdir(lokasi):
        dirfile = os.path.join(lokasi, file)
        if os.path.isfile(dirfile):
            #Cek Last Modified
            if(time.strftime("%Y-%m-%d",time.localtime(os.path.getmtime(dirfile)))<=limitDate.strftime("%Y-%m-%d")):              
                ThnLoc = CekNCreateFolder(srclokasi + '\\' + time.strftime("%Y",time.localtime(os.path.getmtime(dirfile))))
                BlnLoc = CekNCreateFolder(ThnLoc + '\\' + time.strftime("%m",time.localtime(os.path.getmtime(dirfile))))
                TglLoc = CekNCreateFolder(BlnLoc + '\\' + time.strftime("%d",time.localtime(os.path.getmtime(dirfile))))
                #Move File To New Location
                shutil.move(dirfile, TglLoc)
            
    
if __name__ == '__main__':
    managefile()



                