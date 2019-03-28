'''
Created on Jun 16, 2016

@author: Fathony
'''
import sys,pymssql
print pymssql.__version__
dbserver = r'TONY-PC\MSSQL2008R2'# r'(local)\SQLEXPRESS'
#dbserver = r'(local)\SQLEXPRESS'
#dbuser = r'TONY-PC\MPD'
dbuser = r'tas'
dbpassword = 'tas'

dbname = 'smart_dev6'

#Connect To MS2 Server    
try:
    conn_mssql = pymssql.connect(host=dbserver, #host=dbserver, 
								user=dbuser, password=dbpassword,
                                    database=dbname,
                                    #as_dict=True
                                    )
    print "WOKE1"
    cr_mssql = conn_mssql.cursor()
    print "WOKE"
    
    #Execute Query
    SQLquery = 'select top 10 cast(deskripsi as varchar(100)) as woles from [tbl_trs_aset]'
    #SQLquery = 'select top 10 deskripsi from [tbl_trs_aset]'
    try:
        cr_mssql.execute(SQLquery)        
        #rows = cr_mssql.fetchall_asdict()
        rows = cr_mssql.fetchall()
        print 'OKE'
        for row in rows:
            print `row`,  type(row)
            #for col in row:
            #    print  row[col]
            #print 
        
    except:
            print sys.exc_info()#[1]
            msg =  "Data Planning Tidak Tersedia! Silahkan coba beberapa saat lagi"
            MS2centralrunning = False
            #return [2],msg,0            
        
except:
    print 'gagal', sys.exc_info()[1]            
    msg =  "Koneksi dengan Server MS 2 gagal! Silahkan coba beberapa saat lagi"
    MS2centralrunning = False
    #return [1],msg,0