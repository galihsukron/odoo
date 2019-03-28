'''
Created on Jul 31, 2016

@author: Fathony
'''

from openerp.osv import fields, osv
#import pooler
import etl_pdsi



def Ambil_location_from_asset(cr):
    #print "Ambil_location_from_asset()"
    #'Jika udah ada assetnya, gak usah dicari asset locationnya'
    cr.execute('''
        INSERT INTO atemp_pdsi_asset_location (kd_rig, update_level)
        SELECT DISTINCT kd_rig, 1
        FROM atemp_pdsi_tbl_trs_aset
        WHERE kd_rig IS NOT NULL
            --asset_id IS NULL
        ''' )       
    cr.commit()    


def cantelin__location_id(cr):
    #print "cantelin__location_id()"
    cr.execute('''
    UPDATE atemp_pdsi_asset_location m 
    SET 
        asset_location_id = A.id,
		name = A.name
        ,update_level = update_level +1
    FROM 
        asset_location A
    WHERE m.kd_rig = A.pdsi_kd_rig
    ''')    
    cr.commit()  


def fetch_unavailable_rig(tbl_asset, cr, uid):
    #print "fetch_unavailable_rig()"
    cr.execute('''
        SELECT kd_rig
        FROM atemp_pdsi_asset_location 
        WHERE asset_location_id IS NULL
    ''')    
    depots=cr.fetchall()
    DepotList=[]
    for depot in depots:
        #print 'dEpot1-=', depot
        if depot[0]!=None: DepotList.append("'%s'" % depot[0])
    
    if not DepotList:
        return
    #print 'dEPOTLISTZ:',DepotList
    depots = ','.join(DepotList)
    #print 'dEpozts=',depots
    #etl_pdsi
    SQLquery = '''SELECT  tglCreate,
                cast(nm_rig as varchar(500)), 
                cast(kd_rig as varchar(500))
                FROM [tbl_mst_rig] 
                WHERE kd_rig IN (%s)''' % depots
    print SQLquery
#     fetch_rig_by_Query(cr, SQLquery)
#                 
# def fetch_rig_by_Query(cr, SQLquery):                
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    #keys = ['kd_asset', 'deskripsi', 'kd_subsection03']
    for row in rows:
        #print 'dEpRIGF-=', row
        cr.execute('''UPDATE atemp_pdsi_asset_location 
            SET 
            pdsi_lastupdate = %s,
            name = %s 
            WHERE kd_rig = %s''', tuple(row))

    cr.commit()  

def insert_atemp_location(cr, SQLquery):
    #print "insert_atemp_location()"
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    #keys = ['kd_asset', 'deskripsi', 'kd_subsection03']
    for row in rows:
        print 'InstoRIGF-=', row
        cr.execute('''INSERT INTO atemp_pdsi_asset_location 
            (pdsi_lastupdate,
            name,
            kd_rig)
            VALUES (%s,%s,%s) ''', tuple(row))

    cr.commit()  
        
    
def check_if_equal(cr):
    #print "check_if_equal()"
    cr.execute('''
    UPDATE atemp_pdsi_asset_location m 
    SET isequal = True
        FROM asset_location A
    WHERE 
        m.asset_location_id = A.id
        AND m.pdsi_lastupdate = A.pdsi_lastupdate
    ''')    
    cr.commit()            

    
def __inject_location_old(osvobj, cr, uid):
    #print "__inject_location_old()"
    cr.execute('''
        SELECT name, kd_rig
        FROM atemp_pdsi_asset_location 
        WHERE 
            asset_location_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_location = osvobj.pool.get('asset.location')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['name', 'pdsi_kd_rig' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['name'] or '(%s)' % vals[ 'pdsi_kd_rig']
        tbl_asset_location.create(cr,uid, vals)

    cr.commit()    
        
def inject_location(osvobj, cr, uid):
    #print "inject_location()"
    check_if_equal(cr)
    
    cr.execute('''
        SELECT name, kd_rig
        ,pdsi_lastupdate,asset_location_id, isequal
        FROM atemp_pdsi_asset_location 
        --WHERE asset_location_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_location = osvobj.pool.get('asset.location')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['name', 'pdsi_kd_rig',
            'pdsi_lastupdate', 'location_id', 'isequal' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['name'] or '(%s)' % vals[ 'pdsi_kd_rig']
        #tbl_asset_location.create(cr,uid, vals)
        location_id = vals.pop('location_id')
        isequal = vals.pop('isequal')
        #print "halooooooooo vals ini"
        #print vals
		
		
        if location_id: #UPDATE
            if isequal:
                #print 'skip', location_id
                continue
            
            tbl_asset_location.write(cr,uid, location_id,  vals)
            #print 'write', location_id
        #vals['name'] = vals['name'] or '(%s)' % vals['pdsi_deskripsi']
        else:
            location_id = tbl_asset_location.create(cr,uid, vals)
            #print 'create', location_id

    cr.commit()    
        
class atemp_aset_location(osv.Model):
    _name = "atemp.pdsi.asset.location"
    _description = "TEMPORARY Asset from PDSI"
    _columns = {
        'pdsi_lastupdate': fields.datetime('Last Update'),
        'isequal': fields.boolean('Equal sign',help="already sinchronized. skip this row"),                                
        
        'update_level': fields.integer('UPDATED',help="Berapa kali di singkronkan?"),
        'kd_rig': fields.char('Kd Rig',size=128, select=True),
        'deskripsi': fields.char('Deskripsi', size=255),        
        #'asset_id' : fields.integer('Asset ID'),
        'asset_location_id' : fields.integer('Asset Location ID'),
#         'res_company_id' : fields.integer_big('DEPOT ID SIOD'),
        'name': fields.char('Nama Rig',size=128, select=True),
    }
    _defaults = {
       'update_level': lambda *a: 1,
    }
 
    def clear_atemp(self, cr):
        #print "clear_atemp()"
	    
        cr.execute('''
            DELETE 
            FROM atemp_pdsi_asset_location       
            ''')   
        cr.commit() 

    def get_own_pdsi_last_update(self, cr):
        #print "get_own_pdsi_last_update"
	    
        #tbl_asset = self.pool.get('asset.asset')
        cr.execute('SELECT MAX(pdsi_lastupdate) FROM asset_location')
        res = cr.fetchone()
        res = res and res[0] or None
        return res
        

    def load_all_location_from_pdsi(self, cr, uid, loadLocation='all'):
        print "load_all_location_from_pdsi()"
	    
        self.clear_atemp(cr) 
        SQLquery = '''SELECT  tglCreate,
                cast(nm_rig as varchar(500)), 
                cast(kd_rig as varchar(500))
                FROM tbl_mst_rig M
                ''' 
        if loadLocation=='requiring':
            last = self.get_own_pdsi_last_update(cr)
            if last:
                SQLquery += "WHERE M.tglCreate > '%s'" % last #2016-08-02 00:00:00''
                #SQLparam = (last,)
        #print '*'*30, SQLquery
            
        #fetch_rig_by_Query(cr, SQLquery)
        insert_atemp_location(cr, SQLquery)
        print "insert_atemp_location()"
        cantelin__location_id(cr)
        print "cantelin__location_id(cr)"
        inject_location(self, cr, uid)   
        print "inject_location(self, cr, uid)"		


    def prepare_location_from_asset(self, cr, uid):
        print "prepare_location_from_asset()"
	    
        self.clear_atemp(cr)
        print "self.clear_atemp()"
        Ambil_location_from_asset(cr)
        print "Ambil_location_from_asset()"
        cantelin__location_id(cr)
        print "cantelin__location_id()"
        fetch_unavailable_rig(self, cr,uid)#update
        print "fetch_unavailable_rig()"

        cantelin__location_id(cr)
        print "cantelin__location_id()"
        
        inject_location(self, cr, uid)
        print "inject_location()"