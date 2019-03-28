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

def Clear_AtempAssetType(cr):
    cr.execute('''
        DELETE 
        FROM atemp_pdsi_asset_type       
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

def tandai_AtempSpbu_ygLinkKe_PnSpbu(cr):
    cr.execute('''
        UPDATE atemp_spbu m 
        SET 
            pn_spbu_id = A.id            
        FROM 
            pn_spbu A 
        WHERE m.pn_spbu_master_id = A.pn_spbu_master_id
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
    tandai_AtempSpbu_ygLinkKe_PnSpbu(cr)
    
    cr.execute('''
        INSERT INTO pn_spbu (pn_spbu_master_id)
        SELECT pn_spbu_master_id
        FROM atemp_spbu
        WHERE pn_spbu_id IS NULL
        ''')
    cr.commit()
    
def Ambil_type_from_asset(cr):
    #'Jika udah ada assetnya, gak usah dicari asset typenya'
    cr.execute('''
        INSERT INTO atemp_pdsi_asset_type (kd_subsection, level_subsection, update_level)
        SELECT DISTINCT kd_subsection03, 3, 1
        FROM atemp_pdsi_tbl_trs_aset
        WHERE kd_subsection03 IS NOT NULL
            --asset_id IS NULL
        ''' )       
    cr.commit()    
    
def build_psudeo_type03_from_asset(cr):
    #'Jika udah ada assetnya, gak usah dicari asset typenya'
    cr.execute('''
        SELECT deskripsi, kd_subsection03 FROM
        atemp_pdsi_tbl_trs_aset a 
        INNER JOIN (
            SELECT max(id) AS id FROM
            atemp_pdsi_tbl_trs_aset
            WHERE asset_type_id IS NULL
            GROUP BY kd_subsection03
            ) i
            ON a.ID = i.ID
        ''' )       
        # "MUD PUMP DUPLEX; SN:216; IDECO";"E.1.1.19"
        # "ENGINE CAT C.4.4; SN:44410598; CATERPILLAR";"B.1.1.39"
        # "MUD PUMP FD-1600; SN: 1243-C; NOV";"E.1.1.17"
        # "ENGINE CAT D-346; SN:39J16465; CATERPILLAR";"B.1.1.40"
        # "ENGINE ROLL ROYCE";"B.1.1.42"
        # "MUD PUMP WH-1612-401; 1600 HP; LETOURNEOU";"E.1.1.18"
    
    depots=cr.fetchall()
    DepotList=[]
    for d in depots:
        name, code = tuple(d) 
        name = name.split(';')[0]
        cs = code.split('.')
        parent = '.'.join(cs[:3])
        
        cr.execute('''
            INSERT INTO atemp_pdsi_asset_type (deskripsi, kd_subsection, kd_subsection_parent, level_subsection, update_level)
            VALUES(%s, %s, %s, 3, 1)
            ''', (name, code, parent) )        
    cr.commit()    

def build_psudeo_type02(cr):
    #'Jika udah ada assetnya, gak usah dicari asset typenya'
    cr.execute('''
        SELECT deskripsi, kd_subsection03 FROM
        atemp_pdsi_tbl_trs_aset a 
        INNER JOIN (
            SELECT max(id) AS id FROM
            atemp_pdsi_tbl_trs_aset
            WHERE asset_type_id IS NULL
            GROUP BY kd_subsection03
            ) i
            ON a.ID = i.ID
        ''' )       
        # "MUD PUMP DUPLEX; SN:216; IDECO";"E.1.1.19"
        # "ENGINE CAT C.4.4; SN:44410598; CATERPILLAR";"B.1.1.39"
        # "MUD PUMP FD-1600; SN: 1243-C; NOV";"E.1.1.17"
        # "ENGINE CAT D-346; SN:39J16465; CATERPILLAR";"B.1.1.40"
        # "ENGINE ROLL ROYCE";"B.1.1.42"
        # "MUD PUMP WH-1612-401; 1600 HP; LETOURNEOU";"E.1.1.18"
    
    depots=cr.fetchall()
    DepotList=[]
    for d in depots:
        name, code = tuple(d) 
        name = name.split(';')[0]
        cr.execute('''
            INSERT INTO atemp_pdsi_asset_type (deskripsi, kd_subsection, level_subsection, update_level)
            VALUES(%s, %s, 3, 1)
            ''', (name, code) )        
    cr.commit()    
        
def cantelin__type_id(cr):
    cr.execute('''
    UPDATE atemp_pdsi_asset_type m 
    SET 
        asset_type_id = A.id
        ,update_level = update_level +1
    FROM 
        asset_type A
    WHERE m.kd_subsection = A.pdsi_subsection
    ''')    
    cr.commit()  

def fetch_unavailable_subsection03(tbl_asset, cr, uid):
    cr.execute('''
        SELECT kd_subsection
        FROM atemp_pdsi_asset_type 
        WHERE asset_type_id IS NULL
    ''')    
    depots=cr.fetchall()
    DepotList=[]
    for depot in depots:
        #print 'dEpot1-=', depot
        if depot[0]!=None: DepotList.append("'%s'" % depot[0])
    
    if not DepotList:
        return
    print 'dEPOTLISTZ:',DepotList
    depots = ','.join(DepotList)
    print 'dEpozts=',depots
    #etl_pdsi
    SQLquery = '''SELECT  
                cast(nm_subsection03 as varchar(500)),
                cast(kd_subsection02 as varchar(500)),
                cast(kd_subsection03 as varchar(500)) 
                FROM [tbl_mst_subsection03] 
                WHERE kd_subsection03 IN (%s)''' % depots
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    #keys = ['kd_asset', 'deskripsi', 'kd_subsection03']
    for row in rows:
        print 'dEpot1row-=', row
        cr.execute('''UPDATE atemp_pdsi_asset_type 
            SET deskripsi = %s, 
                kd_subsection_parent = %s 
            WHERE kd_subsection= %s''', tuple(row))

    cr.commit()  
    
def fetch_unavailable_subsection02(tbl_asset, cr, uid):
    cr.execute('''
        SELECT kd_subsection_parent
        FROM atemp_pdsi_asset_type 
        WHERE 
            kd_subsection_parent IS NOT NULL
            AND level_subsection = 3
            AND asset_type_id IS NULL
    ''')    
    depots=cr.fetchall()
    DepotList=[]
    for depot in depots:
        #print 'dEpot1-=', depot
        if depot[0]!=None: DepotList.append("'%s'" % depot[0])
    
    if not DepotList:
        return
    print '02.dEPOTLISTZ:',DepotList
    depots = ','.join(DepotList)
    print 'dEpozts=',depots
    #etl_pdsi
    SQLquery = '''SELECT  
                cast(nm_subsection02 as varchar(500)),
                cast(kd_subsection01 as varchar(500)),
                cast(kd_subsection02 as varchar(500)) 
                FROM [tbl_mst_subsection02] 
                WHERE kd_subsection02 IN (%s)''' % depots
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    for row in rows:
        #vals = dict(zip(keys, row))
        #tbl_asset.create(cr,uid, vals)
        row = row + (2,1,)
        cr.execute('''INSERT INTO atemp_pdsi_asset_type 
            (deskripsi, kd_subsection_parent, kd_subsection, level_subsection, update_level)
            VALUES (%s,%s,%s,%s,%s)''', tuple(row))

    cr.commit()      
        
        
def fetch_unavailable_subsection01(tbl_asset, cr, uid):
    cr.execute('''
        SELECT kd_subsection_parent
        FROM atemp_pdsi_asset_type 
        WHERE 
            kd_subsection_parent IS NOT NULL
            AND level_subsection = 2
            AND asset_type_id IS NULL
    ''')    
    depots=cr.fetchall()
    DepotList=[]
    for depot in depots:
        #print 'dEpot1-=', depot
        if depot[0]!=None: DepotList.append("'%s'" % depot[0])
    
    if not DepotList:
        return
    print '01.dEPOTLISTZ:',DepotList
    depots = ','.join(DepotList)
    print 'dEpozts=',depots
    #etl_pdsi
    SQLquery = '''SELECT  
                cast(nm_subsection01 as varchar(500)),
                cast(kd_section as varchar(500)),
                cast(kd_subsection01 as varchar(500)) 
                FROM [tbl_mst_subsection01] 
                WHERE kd_subsection01 IN (%s)''' % depots
    print 'sqLquery01=',SQLquery
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    for row in rows:
        #vals = dict(zip(keys, row))
        #tbl_asset.create(cr,uid, vals)
        row = row + (1,1,)
        cr.execute('''INSERT INTO atemp_pdsi_asset_type 
            (deskripsi, kd_subsection_parent, kd_subsection, level_subsection, update_level)
            VALUES (%s,%s,%s,%s,%s)''', tuple(row))

    cr.commit()       
    

def fetch_unavailable_subsection00(tbl_asset, cr, uid):
    cr.execute('''
        SELECT kd_subsection_parent
        FROM atemp_pdsi_asset_type 
        WHERE 
            kd_subsection_parent IS NOT NULL
            AND level_subsection = 1
            AND asset_type_id IS NULL
    ''')    
    depots=cr.fetchall()
    DepotList=[]
    for depot in depots:
        #print 'dEpot1-=', depot
        if depot[0]!=None: DepotList.append("'%s'" % depot[0])
    
    if not DepotList:
        return
    print '00.dEPOTLISTZ:',DepotList
    depots = ','.join(DepotList)
    print 'dEpozts=',depots
    #etl_pdsi
    SQLquery = '''SELECT  
                cast(nm_section as varchar(500)),
                cast(kd_section as varchar(500))
                FROM [tbl_mst_section] 
                WHERE kd_section IN (%s)''' % depots
    print 'sqLquery01=',SQLquery
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    keys = ['deskripsi',  'kd_section' ]
    for row in rows:
        #vals = dict(zip(keys, row))
        #tbl_asset.create(cr,uid, vals)
        row = row + (0,1,)
        cr.execute('''INSERT INTO atemp_pdsi_asset_type 
            (deskripsi, kd_subsection, level_subsection, update_level)
            VALUES (%s,%s,%s,%s)''', tuple(row))

    cr.commit()      
            
            
def inject_subsection00(osvobj, cr, uid):
    cr.execute('''
        SELECT deskripsi, kd_subsection
        FROM atemp_pdsi_asset_type 
        WHERE 
            level_subsection = 0
            AND asset_type_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_type = osvobj.pool.get('asset.type')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_name', 'pdsi_subsection' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_name']
        tbl_asset_type.create(cr,uid, vals)

    cr.commit()    
    
    
def inject_subsection01(osvobj, cr, uid):
    cr.execute('''
    SELECT a.deskripsi, a.kd_subsection,t.id
        FROM atemp_pdsi_asset_type a
    INNER JOIN asset_type t ON a.kd_subsection_parent = t.pdsi_subsection
        WHERE 
            a.level_subsection = 1
            AND a.asset_type_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_type = osvobj.pool.get('asset.type')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_name', 'pdsi_subsection', 'parent_id' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_name']
        tbl_asset_type.create(cr,uid, vals)

    cr.commit()    


def inject_subsection02(osvobj, cr, uid):
    cr.execute('''
    SELECT a.deskripsi, a.kd_subsection,t.id
        FROM atemp_pdsi_asset_type a
    INNER JOIN asset_type t ON a.kd_subsection_parent = t.pdsi_subsection
        WHERE 
            a.level_subsection = 2
            AND a.asset_type_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_type = osvobj.pool.get('asset.type')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_name', 'pdsi_subsection', 'parent_id' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_name']
        tbl_asset_type.create(cr,uid, vals)

    cr.commit()    
                       
                       
def inject_subsection03(osvobj, cr, uid):
    cr.execute('''
    SELECT a.deskripsi, a.kd_subsection,t.id
        FROM atemp_pdsi_asset_type a
    INNER JOIN asset_type t ON a.kd_subsection_parent = t.pdsi_subsection
        WHERE 
            a.level_subsection = 3
            AND a.asset_type_id IS NULL
    ''')    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_type = osvobj.pool.get('asset.type')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_name', 'pdsi_subsection', 'parent_id' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_name']
        tbl_asset_type.create(cr,uid, vals)

    cr.commit()    
                       
                       
#-----------------------------
schm = [('tbl_mst_section',         {'nm_section':     'deskripsi', 'kd_section':                                                'kd_subsection'}),
        ('tbl_mst_subsection01',    {'nm_subsection01':'deskripsi', 'kd_section':     'kd_subsection_parent', 'kd_subsection01': 'kd_subsection'}),
        ('tbl_mst_subsection02',    {'nm_subsection02':'deskripsi', 'kd_subsection01':'kd_subsection_parent', 'kd_subsection02': 'kd_subsection'}),
        ('tbl_mst_subsection03',    {'nm_subsection03':'deskripsi', 'kd_subsection02':'kd_subsection_parent', 'kd_subsection03': 'kd_subsection'}),
        ]

def fetch_all_subsectionOf(level, tbl_asset, cr, uid):
    table, cols = schm[level]
    selects = ['cast(%s as varchar(500))' % c for c in cols]
    SELECT = ',\n'.join(selects) 
    
    SQLquery = '''SELECT  
                %s
                FROM %s 
                ''' % (SELECT,table) 
    
    #print SQLquery
    
    #print [k for k in cols.iterkeys()]
    
    err,rows = etl_pdsi.load_asset(SQLquery)
    rows = rows or []
    #tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
    #keys = ['deskripsi',  'kd_section' ]
    
    #print [v for v in cols.itervalues()]
    final_cols = cols.values() + ['level_subsection'] 
    columns = '(%s)' % ', '.join( final_cols )
    ss = ','.join( ['%s']* len(final_cols))
    sql = 'INSERT INTO atemp_pdsi_asset_type ' + columns 
    sql += 'VALUES (%s)' %  ss
    for row in rows:
        #vals = dict(zip(keys, row))
        #tbl_asset.create(cr,uid, vals)
        row = row + (level,)
        cr.execute(sql, tuple(row))

    cr.commit()                  
    
    
def inject_subsectionOf(level, osvobj, cr, uid):
    cr.execute('''
    SELECT a.deskripsi, a.kd_subsection,t.id, level_subsection
        FROM atemp_pdsi_asset_type a
    INNER JOIN asset_type t ON a.kd_subsection_parent = t.pdsi_subsection
        WHERE 
            a.level_subsection = %s
            AND a.asset_type_id IS NULL
    ''', (level,))    
    rows=cr.fetchall()    
    rows = rows or []
    tbl_asset_type = osvobj.pool.get('asset.type')
    #keys = ['deskripsi', 'kd_subsection_parent', 'kd_subsection' ]
    keys = ['pdsi_name', 'pdsi_subsection', 'parent_id', 'pdsi_level' ]
    for row in rows:
        vals = dict(zip(keys, row))
        vals['name'] = vals['pdsi_name']
        tbl_asset_type.create(cr,uid, vals)

    cr.commit()    
    
def fill_emptysubsection02(cr):
    cr.execute('''
        UPDATE atemp_pdsi_tbl_trs_aset SET kd_subsection02 = p.pdsi_subsection
        FROM (  
            SELECT a.id, deskripsi, kd_subsection03,kd_subsection02, tp.pdsi_subsection FROM
            atemp_pdsi_tbl_trs_aset a
        
            INNER JOIN asset_type t ON a.kd_subsection03 = t.pdsi_subsection
            INNER JOIN asset_type tp ON tp.id = t.parent_id
            WHERE a.kd_subsection02 IS NULL
            ) p
        WHERE atemp_pdsi_tbl_trs_aset.id = p.id        ''')    

    cr.commit()        
                 
class atemp_aset_type(osv.Model):
    _name = "atemp.pdsi.asset.type"
    _description = "TEMPORARY Asset from PDSI"
    _columns = {
        'update_level': fields.integer('UPDATED',help="Berapa kali di singkronkan?"),
        'level_subsection': fields.integer('Level', required=True, help=""),        
        'kd_subsection': fields.char('Name',size=128, select=True),
        'kd_subsection_parent': fields.char('Parent',size=128, select=True),
        'deskripsi': fields.char('Deskripsi', size=255),        
        #'asset_id' : fields.integer('Asset ID'),
        'asset_type_id' : fields.integer('Asset Type ID'),
#         'res_company_id' : fields.integer_big('DEPOT ID SIOD'),
    }
    _defaults = {
       'update_level': lambda *a: 1,
    }
    def clear_atemp(self, cr):
        Clear_AtempAssetType(cr)


    def load_all_type(self, cr, uid):
        for level in [0,1,2,3]:
            print "loading type level",level,
            self.clear_atemp(cr) 
            fetch_all_subsectionOf(level, self, cr, uid)
            cantelin__type_id(cr)
            if level:
                inject_subsectionOf(level, self, cr, uid)
            else:
                inject_subsection00(self, cr, uid) #LEVEL 0
            print 'DONE'
        #fetch_all_subsectionOf(1, self, cr, uid)
    
    def make_type_assumption(self, cr, uid):
        'type ada di aset, tapi gak ada di PDSI master type'
        Clear_AtempAssetType(cr)
        #down to up
        build_psudeo_type03_from_asset(cr)

#         fetch_unavailable_subsection03(self, cr,uid)#update
#         fetch_unavailable_subsection02(self, cr,uid)#create
        cantelin__type_id(cr)
#         fetch_unavailable_subsection01(self, cr,uid)#create
#         cantelin__type_id(cr)
#         fetch_unavailable_subsection00(self, cr,uid)#create
#         cantelin__type_id(cr)
#         
#         #up to down
#         #inject_subsection00(self, cr, uid)
#         #inject_subsection01(self, cr, uid)
#         inject_subsection02(self, cr, uid)
        inject_subsection03(self, cr, uid)
        fill_emptysubsection02(cr)
        
    
    def prepare_type_from_asset(self, cr, uid):
        Clear_AtempAssetType(cr)
        #down to up
        Ambil_type_from_asset(cr)
        cantelin__type_id(cr)
        fetch_unavailable_subsection03(self, cr,uid)#update
        fetch_unavailable_subsection02(self, cr,uid)#create
        cantelin__type_id(cr)
        fetch_unavailable_subsection01(self, cr,uid)#create
        cantelin__type_id(cr)
        fetch_unavailable_subsection00(self, cr,uid)#create
        cantelin__type_id(cr)
        
        #up to down
        #inject_subsection00(self, cr, uid)
        #inject_subsection01(self, cr, uid)
        #inject_subsection02(self, cr, uid)
        #inject_subsection03(self, cr, uid)
        for level in [0,1,2,3]:
            if level:
                inject_subsectionOf(level, self, cr, uid)
            else:
                inject_subsection00(self, cr, uid) #LEVEL 0

