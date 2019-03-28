'''
Created on Jun 16, 2016

@author: Fathony
'''
#import sys,pymssql
#print pymssql.__version__

# WE NEED CROSS DB (SUCH SQLALCHEMY) FOR REAL DB, BUT I HAVE NO TIME. SO WE SWITCH BETWEEN PROCS BELOW: 

#global config for etl_pdsi
CONFIG = {}

def get_con_sqlserver(config):
    "USE IT IF MSSQL AVAILABLE"
    import pymssql
    #dbserver = r'TONY-PC\MSSQL2008R2'# r'(local)\SQLEXPRESS'
    dbserver = r'10.13.1.49'
    #dbuser = r'TONY-PC\MPD'
    dbuser = r'sa'
    dbpassword = 'pDsI123'
    dbname = 'smart_dev20160321'
    
    config = CONFIG
    dbserver    = config['server']
    dbname      = config['name']
    dbuser      = config['user']
    dbpassword  = config['password']
    
    #USE THE CONFIG
    #Connect To MS2 Server    
    try:
        conn_mssql = pymssql.connect(host=dbserver, #host=dbserver, 
                                    user=dbuser, password=dbpassword,
                                        database=dbname,
                                        #as_dict=True
                                        )
    except:
        return False
    #print "WOKE1"
    #cr_mssql = conn_mssql.cursor()
    #print "WOKE"
    #return cr_mssql
    return conn_mssql
        
        
def get_con_sqlite():
    "USE IT IF MSSQL IS NOT AVAILABLE"
    import os
    import openerp.modules
    import sqlite3 as lite
    
    modpath = openerp.modules.get_module_path('sl_asset_etl_pdsi')
    dbfile = os.path.join(modpath, 'data', 'dat2.sqlite')
    
    sqlite_con = lite.connect(dbfile)
    #cur = con.cursor()        
    #return cur
    return sqlite_con        
        
        

def load_asset(SQLquery):
    '''
    return : ErrorMsg, data
    '''
    import sys
    
    #get_con = get_con_sqlite
    
    #ir_values = self.pool.get('ir.values').get_default(cr, uid, 'project.config.settings', 'generate_project_alias')    
    #db_connection = get_con()
    #Connect To MS2 Server    
    try:
        #db_connection = get_con()
        config = CONFIG
        print 'loading query. etl_pdsi.CONFIG=', config
        if config and config.get('source',None):
            db_connection = get_con_sqlserver(config)
            if db_connection == False:
                result = sys.exc_info()[1], None
                msg =  "Data Planning Tidak Tersedia! Silahkan coba beberapa saat lagi"
                MS2centralrunning = False
                #return [2],msg,0
                return result
        else:
            db_connection = get_con_sqlite()
            
        cr = db_connection.cursor()
        
        #Execute Query
        #SQLquery = 'select top 10 cast(deskripsi as varchar(100)) as woles from [tbl_trs_aset]'
        #SQLquery = 'select top 10 deskripsi from [tbl_trs_aset]'
        try:
            cr.execute(SQLquery)        
            #rows = cr_mssql.fetchall_asdict()
            rows = cr.fetchall()
            db_connection.close()
            return False, rows
            #rows = cr_mssql.fetchall()
            #print 'OKE'
            #for row in rows:
            #    print `row`,  type(row)
                #for col in row:
                #    print  row[col]
                #print 
            
        except:
                result = sys.exc_info()[1], None
                msg =  "Data Planning Tidak Tersedia! Silahkan coba beberapa saat lagi"
                MS2centralrunning = False
                #return [2],msg,0
                return result            
            
    except:
        result = sys.exc_info()[1], None            
        msg =  "Koneksi dengan Server MS 2 gagal! Silahkan coba beberapa saat lagi"
        MS2centralrunning = False
        #return [1],msg,0
        return result
    
if __name__ == '__main__':
    SQLquery = 'select top 10 kd_aset, cast(deskripsi as varchar(500)) as deskripsi, cast(kd_subsection03 as varchar(500)) as kd_subsection03 from [tbl_trs_aset]'
    err,rows = load_asset(SQLquery)   
    for row in rows:
        print `row`,  type(row) 