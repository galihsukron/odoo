'''
Created on Sep 18, 2014

@author: MPD

    Ini akan dipakai oleh wizard.
    Wizard hanya akan create + download MySAP.
    Tolong pastikan sendiri (sebelum memanggil wizard) bahwa SPBU yg diminta belum ada.

    Cara menggunakan:
    Hapus tabel atemp_spbu
    INSERT tabel. Minimal field yg harus diisi adalah `shipto`
    
'''
#from osv import fields, osv
from openerp.osv import fields, osv
#import pooler
import etl_pdsi

def Clear_AtempSPBU(cr):
    cr.execute('''
        DELETE 
        FROM atemp_pdsi_tbl_trs_aset       
        ''')   
    cr.commit() 

def tandai_AtempSpbu_ygLinkKe_SpbuMaster(cr):
    cr.execute('''
        UPDATE atemp_spbu m 
        SET 
            pn_spbu_master_id = A.id            
        FROM 
            pn_spbu_master A 
        WHERE m.shipto = A.shipto
        ''')    
    cr.commit()

def tandai_SpbuMaster_ActiveTrue__ygLinkKe_AtempSpbu(cr):
    cr.execute('''
        UPDATE pn_spbu_master m 
        SET 
            active = true            
        FROM 
             atemp_spbu A 
        WHERE m.id = A.pn_spbu_master_id
        ''')    
    cr.commit()
def cantelin__plant_keResCompany(cr):
    cr.execute('''
    UPDATE atemp_spbu m SET res_company_id = A.id
        FROM 
        (
        SELECT MIN(id) as id, ref FROM res_company 
        GROUP BY ref
        ) A
    WHERE m.plant = A.ref
    ''')    
    cr.commit()            
def Create_SPBU(cr,uid, fasum={}):
    #diasumsikan data yg dibutuhkan sudak komplit.
#     cr.execute('''
#         SELECT name,name2, shipto, smsnumber, id_kota, nama_kota
#         FROM atemp_spbu       
#         ''')
#     rows = cr.dictfetchall()
#     spbu_ref = pooler.get_pool( cr.dbname ).get( 'pn.spbu' )    
#     for row in rows:
#         dat = dict((k,v) for k,v in row.iteritems() if v)
#         spbu_ref.create(cr,1,dat)

    #---SPBU MASTER
    tandai_AtempSpbu_ygLinkKe_SpbuMaster(cr)
    # INSERT
#     cr.execute('''
#         INSERT INTO pn_spbu_master (name,name2, shipto, smsnumber, city_id, city, company_id)
#         SELECT name,name2, shipto, smsnumber, id_kota, nama_kota, %s AS CMP_ID
#         FROM atemp_spbu
#         WHERE pn_spbu_master_id IS NULL
#         ''', (fasum['company_id'],) )   
    cr.execute('''
        INSERT INTO pn_spbu_master (name,name2, shipto, smsnumber, city_id, city, company_id)
        SELECT name,name2, shipto, smsnumber, id_kota, nama_kota, res_company_id
        FROM atemp_spbu
        WHERE pn_spbu_master_id IS NULL
        ''' )       
    cr.commit()
    
    #UPDATE
    tandai_AtempSpbu_ygLinkKe_SpbuMaster(cr)
    #PASTIKAN AKTIF
    tandai_SpbuMaster_ActiveTrue__ygLinkKe_AtempSpbu(cr)
     
    #---PN SPBU
    tandai_AtempAsset_ygLinkKe_AssetAsset(cr)
    
    cr.execute('''
        INSERT INTO pn_spbu (pn_spbu_master_id)
        SELECT pn_spbu_master_id
        FROM atemp_spbu
        WHERE pn_spbu_id IS NULL
        ''')
    cr.commit()
    
def tandai_AtempAsset_ygLinkKe_AssetAsset(cr):
    cr.execute('''
        UPDATE atemp_pdsi_tbl_trs_aset m 
        SET 
            asset_id = A.id  
            ,update_level = update_level +1          
        FROM 
            asset_asset A 
        WHERE m.kd_asset = A.pdsi_kd_asset
        ''')    
    cr.commit()
        
def cantelin__type_ke_atempAsset(cr):
    cr.execute('''
    UPDATE atemp_pdsi_tbl_trs_aset m 
    SET asset_type_id = A.id
        FROM asset_type A
    WHERE m.kd_subsection02 = A.pdsi_subsection
    ''')    
    cr.commit()            
    
def cantelin__location_ke_atempAsset(cr):
    cr.execute('''
    UPDATE atemp_pdsi_tbl_trs_aset m 
    SET asset_location_id = A.id
        FROM asset_location A
    WHERE m.kd_rig = A.pdsi_kd_rig
    ''')    
    cr.commit()            
    

def cantelin__name_ke_atempAsset(cr):
    cr.execute('''
    UPDATE atemp_pdsi_tbl_trs_aset m 
    SET asset_name = A.name
        FROM asset_type A
    WHERE m.kd_subsection03 = A.pdsi_subsection
    ''')    
    cr.commit()            

def __inject_asset_old(osvobj, cr, uid):
    #TODO: add update, currently only insert
    cr.execute('''
    SELECT a.deskripsi, a.kd_asset, no_movable, no_sap,
        asset_location_id,
        asset_type_id, rfid, asset_name, no_eqid as pdsi_no_eqid
        FROM atemp_pdsi_tbl_trs_aset a
        WHERE 
            a.asset_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset = osvobj.pool.get('asset.asset')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_deskripsi', 'pdsi_kd_asset', 'pdsi_no_movable', 'no_sap', 
            'log_location',
            'type_id', 'rfid', 'name','pdsi_no_eqid' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_deskripsi']
        #vals['name'] = vals['name'] or '(%s)' % vals['pdsi_deskripsi']
        tbl_asset.create(cr,uid, vals)
        
        #print 'create'

    cr.commit()


def check_if_equal(cr):
    cr.execute('''
    UPDATE atemp_pdsi_tbl_trs_aset m 
    SET isequal = True
        FROM asset_asset A
    WHERE 
        m.asset_id = A.id
        AND m.pdsi_lastupdate = A.pdsi_lastupdate
    ''')    
    cr.commit()            

def inject_asset(osvobj, cr, uid):
    #TODOne: add update, currently only insert
    check_if_equal(cr)
    
    cr.execute('''
    SELECT a.deskripsi, a.kd_asset, no_movable, no_sap,
        asset_location_id, pdsi_lastupdate,
        asset_id, isequal,
        asset_type_id, rfid, asset_name, no_eqid as pdsi_no_eqid
        FROM atemp_pdsi_tbl_trs_aset a
        --WHERE a.asset_id IS NULL
    ''')    
    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset = osvobj.pool.get('asset.asset')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
#    keys = ['pdsi_deskripsi', 'pdsi_kd_asset', 'pdsi_no_movable', 'no_sap', 
#            'log_location', 'pdsi_lastupdate',
#            'asset_id', 'isequal',
#            'type_id', 'rfid', 'name','pdsi_no_eqid' ]
    keys = ['pdsi_deskripsi', 'pdsi_kd_asset', 'pdsi_no_movable', 'no_sap', 
            'log_location', 'pdsi_lastupdate',
            'asset_id', 'isequal',
            'type_id', 'pdsi_epc', 'name','pdsi_no_eqid' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_deskripsi']
        
        asset_id = vals.pop('asset_id')
        isequal = vals.pop('isequal')
        
        if asset_id: #UPDATE
            if isequal:
                #print 'skip', asset_id
                continue
            vals.pop('log_location')
            tbl_asset.write(cr,uid, asset_id,  vals)
            #print 'write', asset_id
        #vals['name'] = vals['name'] or '(%s)' % vals['pdsi_deskripsi']
        else:
            asset_id = tbl_asset.create(cr,uid, vals)
            #print 'create', asset_id

    cr.commit()
        

        
class atemp_tbl_trs_aset(osv.Model):
    _name = "atemp.pdsi.tbl_trs_aset"
    _description = "TEMPORARY Asset from PDSI"
    _columns = {
        'pdsi_lastupdate': fields.datetime('Last Update'),
        'isequal': fields.boolean('Equal sign',help="already sinchronized. skip this row"),                                
                
        'update_level': fields.integer('UPDATED',help="Berapa kali di singkronkan?"),
        'kd_rig': fields.char('Kd Rig',size=128, select=True),
        'kd_asset': fields.integer('KD Asset', required=True, help=""),        
        'no_movable': fields.char('No. Movable', size=128),
        'no_eqid': fields.char('No. Equipment', size=128),                                
        'no_sap': fields.char('No. SAP', size=128),                                
        'deskripsi': fields.char('Deskripsi', size=255),        
        'kd_subsection03': fields.char('Delivery_Number',size=128, select=True),
        'rfid': fields.char('RFID', required=True, help="Radio Frequency ID"),
        'kd_subsection02': fields.char('Delivery_Number',size=128, select=True),
        
        
#         'name2': fields.char( 'Name2 SPBU', size = 50 ),
#         'shipto':fields.char('Ship_to',size=64, readonly=True),
#         
#         'plant': fields.char('KodeDepot', size=20),         
#         'pasti_pas': fields.char('PastiPas', size=20),
#          
#         'smsnumber': fields.char('Nomor SMS', size = 15),
#         'id_kota' : fields.integer('Kota ID'), 
#         
#         'nama_kota': fields.char('SPBU', size=20),
#           
#         'pn_spbu_master_id' : fields.integer_big('SPBU ID SIOD'),    
         'asset_id' : fields.integer('Asset ID'),
         'asset_type_id' : fields.integer('Asset Type ID'),
         'asset_location_id' : fields.integer('Asset Type ID'),
         'asset_name' : fields.char('asset name',size=128, select=True),
#         'res_company_id' : fields.integer_big('DEPOT ID SIOD'),
    }
    _defaults = {
       'update_level': lambda *a: 1,
    }


    def clear_atemp(self, cr):
        Clear_AtempSPBU(cr)
        
    def get_own_pdsi_last_update(self, cr):
        #tbl_asset = self.pool.get('asset.asset')
        cr.execute('SELECT MAX(pdsi_lastupdate) FROM asset_asset')
        res = cr.fetchone()
        res = res and res[0] or None
        return res
        
        
    def load_asset_from_pdsi(self, cr, uid, loadAsset='requiring'):
        'Called by wizard'
        Clear_AtempSPBU(cr)
        #SQLquery = 'select top 10 kd_aset, cast(deskripsi as varchar(500)) as deskripsi, cast(kd_subsection03 as varchar(500)) as kd_subsection03 from [tbl_trs_aset]'
        #SQLquery = 'SELECT kd_aset, cast(deskripsi as varchar(500)) as deskripsi, cast(kd_subsection03 as varchar(500)) as kd_subsection03 from [tbl_trs_aset]'
        SQLquery = '''SELECT kd_mst_aset as kd_aset,
            CAST(kd_rig as varchar(128)) as kd_rig,
            CAST(no_movable as varchar(128)) as no_movable,
            CAST(no_sap as varchar(128)) as no_sap,
            lsUpdate,
            cast(deskripsi as varchar(500)) as deskripsi, cast(m.kd_subsection03 as varchar(500)) as kd_subsection03, no_rfid as rfid
            , cast(s3.kd_subsection02 as varchar(500)) as kd_subsection02
            , CAST(no_eqid as varchar(128)) as no_eqid
            from tbl_mst_trs_new m
            left join tbl_mst_subsection03 s3 on m.kd_subsection03 = s3.kd_subsection03
            '''
        #SQLparam = None
        if loadAsset=='requiring':
            last = self.get_own_pdsi_last_update(cr)
            if last:
                SQLquery += "WHERE M.LSUPDATE > '%s'" % last #2016-08-02 00:00:00''
                #SQLparam = (last,)
        #print '*'*30, SQLquery
            
        err,rows = etl_pdsi.load_asset(SQLquery)
        tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
        keys = ['kd_asset','kd_rig', 'no_movable', 'no_sap', 
                'pdsi_lastupdate',
                'deskripsi', 'kd_subsection03', 'rfid', 'kd_subsection02','no_eqid']
        
        for row in rows:
            vals = dict(zip(keys, row))
            #vals['name'] = vals['name'] or '(%s)' % vals['kd_subsection03']
            tbl_asset.create(cr,uid, vals)
            
        tandai_AtempAsset_ygLinkKe_AssetAsset(cr)

    def inject_atemp_to_AssetAsset(self, cr, uid):        
        cantelin__type_ke_atempAsset(cr)
        cantelin__name_ke_atempAsset(cr)
        cantelin__location_ke_atempAsset(cr)
        inject_asset(self, cr, uid)

#     _sql_constraints = [
#        ('atemp_pn_do_id_uniq', 'unique (name_int)', 'LO Number must be unique !'),
#        ]

#atemp_spbu()

