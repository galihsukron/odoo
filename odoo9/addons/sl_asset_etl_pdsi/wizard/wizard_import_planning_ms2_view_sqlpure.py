# -*- coding: iso-8859-1 -*-
##############################################################################

##############################################################################
# 2009.11.15    bugfix: I make sure that target-download is always available. via httplib 
# 2009.11.15    bugfix: also, it decrease download-time, that is no error/exception occur while running this script (timeout-error) 

import sys
import csv, string
import os.path
import re
import pymssql
from tools.translate import _
#from runwinscp import genericftpcmd
from pn2.wizard import wizard_export_lo_plant
from pn2.wizard import parsingutil, parsingutil3
from pn2.wizard.parsingutil import _listdate
from connector.clientmanual.openerp_object_multi_caller import executefunctioninDepots
from pn2.wizard.parsingutil3 import checkncreate,getThisCompanyData,_default_company
#from pn2.wizard.wizard_import_lo_fromCentral2 import updateLOByNumberFromMySAP
from wizard_import_lo_sqlpure import DownloadLO_ByLONumber_FromMySAP
from pn2.pn_process_log import process_log_wrapper

from pn2.initconfiguration import pn2_conf
from tools import UpdateableStr, UpdateableDict
from datetime import datetime, timedelta    
#from threading import Thread
import subprocess
from .. import atemp_spbu

def siapkan_shipment_request_untuk_sinkronisasi(cr,date_expected):
    # plan_siod.shipmentreq_id = shipreq.id
    # FILL ID
    cr.execute('''SELECT count(*) FROM pn_shipment_request 
        where name != '' 
        AND name is not null 
        and name_int = 0
        and date_expected = %s ''', (date_expected,) )
    if cr.fetchone()[0]:
        cr.execute('''UPDATE pn_shipment_request
                SET name_int = cast(name AS bigint)
                WHERE 
            --state = '0'
            date_expected = %s
                    AND name != '' 
                    AND name is not null 
                    AND (name_int = 0 OR name_int IS NULL)
                    AND SUBSTR(NAME,1,1) != 'M'
            ''', (date_expected,) )
        cr.commit()

def tandai_TempPlanning__levelZero(cr):
    cr.execute('''
        UPDATE ms2view_plan_siod d 
        SET 
            update_level = 0,
            pn_shipment_request_id = NULL        
        ''')
    cr.commit()
    
def tandai_TempPlanning__ygLinkKe_ShipmentRequest(cr):
    # sync
    cr.execute('''
        UPDATE ms2view_plan_siod d 
        SET 
            pn_shipment_request_id = A.id,
            update_level = update_level+1
        FROM pn_shipment_request A
        WHERE d.ms2_id = A.name_int
        ''')
    cr.commit()
    
def tandai_TempPlanning__ygLinkKe_SpbuMaster(cr):
    cr.execute('''
    UPDATE ms2view_plan_siod d SET pn_spbu_id = A.pn_spbu_id
        FROM ms2view_pn_spbu A
        WHERE d.no_spbu = A.no_spbu
        ''')
    cr.commit()
    
def tandai_TempPlanning__ygLinkKe_ResCompany(cr):
    cr.execute('''
    UPDATE ms2view_plan_siod d SET res_company_id = A.id
        FROM res_company A
        WHERE d.plant = A.ref
        ''')
    cr.commit()

def fill_plan_siod__date(cr,datefind, datenow):
    query ='''
    UPDATE ms2view_plan_siod d SET 
        date_expected = '%(datenow)s',
        date_order = CASE WHEN status_plan = 'H-1' THEN DATE '%(datenow)s'  - interval '1 day' ELSE DATE  '%(datenow)s' END       
        WHERE tgl_kirim = '%(datefind)s' 
        ''' % locals()
    #print query
    cr.execute(query)
    cr.commit()
    
def fasum__root_updatetotal(cr,uid, fasum):
    
    cr.execute('''        
        SELECT SUM(NOTFOUND) AS failed, SUM(NEW1) AS inserted, SUM(ANY1) AS downloaded, SUM(FOUND1) AS found
        FROM (
            SELECT 
                CASE WHEN update_level = 0 THEN 1 END AS NOTFOUND,
                CASE WHEN update_level = 1 THEN 1 END AS NEW1,
                CASE WHEN update_level = 2 THEN 1 END AS FOUND1,
                1 AS ANY1
        
            FROM ms2view_plan_siod 
            --WHERE update_level < 2
            UNION
            SELECT 0,0,0,0
    
        ) B
     ''')
    val = cr.dictfetchone()
    val['company_id'] = fasum['company_id']
    val['finished'] = datetime.now()
    fasum['ref'].write(cr,uid,[fasum['root']], val)
    return    
#     cr.execute('''
#         UPDATE fast_summary fs SET inserted = A.totalnew, failed= A.totalfailed, found=totalaccept, downloaded = A.totalall
#     FROM (
#         SELECT SUM(NOTFOUND) AS totalfailed, SUM(NEW1) AS totalnew, SUM(ANY1) AS totalall, SUM(FOUND1) AS totalaccept
#         FROM (
#             SELECT 
#                 CASE WHEN update_level = 0 THEN 1 END AS NOTFOUND,
#                 CASE WHEN update_level = 1 THEN 1 END AS NEW1,
#                 CASE WHEN update_level = 2 THEN 1 END AS FOUND1,
#                 1 AS ANY1
#             FROM ms2view_plan_siod 
#             --WHERE update_level < 2
#     
#         ) B
#     ) A
#     WHERE fs.id = %s
#         ''', fasum['root'])
#     cr.commit()
    
def fasum__DO_updatetotal(cr,uid, fasum):    
    cr.execute('''        
        SELECT SUM(NOTFOUND) AS failed, SUM(NEW1) AS inserted, SUM(ANY1) AS downloaded, SUM(FOUND1) AS found
        FROM (
            SELECT 
                CASE WHEN update_level = 0 OR update_level IS NULL THEN 1 END AS NOTFOUND,
                CASE WHEN update_level = 1 THEN 1 END AS NEW1,
                CASE WHEN update_level = 2 THEN 1 END AS FOUND1,
                1 AS ANY1
            FROM ms2view_pn_do 
            --WHERE update_level < 2
    
        ) B
     ''')
    val = cr.dictfetchone()
    #val['name'] = 'Download LO'
    #val['parent_id'] = fasum['root']
    #val['company_id'] = fasum['company_id']
    #fasum['ref'].write(cr,uid,[fasum['root']], val)
    val['finished'] = datetime.now()
    #fasum['ref'].create(cr,uid, val)
    fasum['ref'].write(cr,uid,[fasum['lo']], val)

def fasum__SPBU_updatetotal(cr,uid, fasum):    
    cr.execute('''        
        SELECT 
            SUM(NOTFOUND) AS failed, 
            SUM(NEW1) AS inserted, 
            SUM(ANY1) AS downloaded, 
            SUM(FOUND1) AS found
        FROM (
            SELECT 
                CASE WHEN update_level = 0 OR update_level IS NULL THEN 1 ELSE 0 END AS NOTFOUND,
                CASE WHEN update_level = 1 THEN 1 ELSE 0 END AS NEW1,
                CASE WHEN update_level = 2 THEN 1 ELSE 0 END AS FOUND1,
                1 AS ANY1
            FROM ms2view_pn_spbu 
            --WHERE update_level < 2
        ) B
     ''')
    val = cr.dictfetchone()    
    #fasum['ref'].write(cr,uid,[fasum['root']], val)
    fasum['ref'].write(cr,uid,fasum['spbu'], val)   
    
    #BERI TAHU YG GAGAL
    if val['failed'] > 0:
        cr.execute('''        
        SELECT no_spbu, ship_to        
        FROM ms2view_pn_spbu 
        WHERE update_level = 0 OR update_level IS NULL
        ''')        
        res = cr.dictfetchall()
        values = {'parent_id' : fasum['spbu'],'failed':1, 'downloaded':0, 'inserted':0,'found':0 }
        for r in res:
            values['name'] = "SPBU:%s, SHIPTO:%s" % (r['no_spbu'],r['ship_to'])
            fasum['ref'].create(cr,uid, values)      

    #BERI TAHU YG BARU
    if val['inserted'] > 0:
        cr.execute('''        
        SELECT no_spbu, ship_to        
        FROM ms2view_pn_spbu 
        WHERE update_level = 1 
        ''')        
        res = cr.dictfetchall()
        values = {'parent_id' : fasum['spbu'],'failed':0, 'downloaded':0, 'inserted':1,'found':0 }
        for r in res:
            values['name'] = "SPBU:%s, SHIPTO:%s" % (r['no_spbu'],r['ship_to'])
            fasum['ref'].create(cr,uid, values)           
    fasum['ref'].write(cr,uid,fasum['spbu'],  {'finished': datetime.now(),})     


def count_TempPlanning__ygNOTlinkKe_ShipmentRequest(cr):
    cr.execute('''SELECT count(*) FROM ms2view_plan_siod 
        WHERE pn_shipment_request_id is null''')
    return cr.fetchone()[0]
    
       
def inject_pn_shipment_request(cr):
    #update TempPlanning
    cr.execute('''
    UPDATE ms2view_plan_siod d SET pn_shipment_request_id = A.id
        FROM pn_shipment_request A
        WHERE d.ms2_id = A.name_int        
        ''' )
    cr.commit()
    
    #---1. update shipreq dgn data terbaru
    # perhatikan jangan diupdate yg sudah terkirim
    #BUGFIX: https://www.facebook.com/photo.php?fbid=10205052048165664&set=pcb.726860514061267&type=1&theater
    cr.execute('''
    UPDATE pn_shipment_request SR  SET
        produk_id = M.jenis_bbm, date_expected=M.date_expected, date_order=M.date_order, plancategory=M.status_plan, 
        shift_request=M.shift_request, shift_shipment=M.shift,
        stokclaimed=M.ketahanan_hari, depot=M.res_company_id, no_spbu=M.pn_spbu_id, 
    kl_do = to_char(M.qty, 'FM999990.0999'), 
    kl_do_float =M.qty, 
    qty_ori =M.qty_ori,
        no_hp_raw=M.no_hp,
        no_spbu_raw=M.no_spbu, shipto_raw=M.ship_to, plant_raw=M.plant,
        loading_order_raw=M.loading_order
        --active, planningsource = 'ms2' 
        --create_date, create_uid, state_planning
    FROM ms2view_plan_siod M
    WHERE M.pn_shipment_request_id = SR.id
        ''')
    cr.commit()    
    
    
    #---2. insert
    # insert ke shipreq yg id= null     
    cr.execute('''
    INSERT INTO pn_shipment_request  (
        produk_id, date_expected, date_order, plancategory, 
        shift_request, shift_shipment,
        stokclaimed,depot, no_spbu, 
    kl_do, 
    kl_do_float, 
    qty_ori,
        name, name_int, no_hp_raw,
        no_spbu_raw, shipto_raw, loading_order_raw, plant_raw,
        active, planningsource, 
        create_date, create_uid, state_planning
        )
    SELECT
        jenis_bbm, date_expected, date_order, status_plan, 
        shift_request, shift,
        ketahanan_hari,res_company_id, pn_spbu_id, 
    to_char(qty, 'FM999990.0999'), 
    qty,
    qty_ori, 
        ms2_id, ms2_id, no_hp,
        no_spbu, ship_to, loading_order, plant,
        true, 'ms2', 
        localtimestamp, 1, '1'
    FROM ms2view_plan_siod SRC
    WHERE SRC.pn_shipment_request_id IS NULL
        ''')
    cr.commit()    
    pass
    
    
    

    
def create_unnest(cr):
    cr.execute('''
    create or replace function unnest(anyarray) returns setof anyelement
    language sql as $$
       select $1[i] from generate_series(array_lower($1, 1),
                                         array_upper($1, 1)) as i;
    $$;  ''')
    cr.commit()
    
def extract_TempDo__from_MS2(cr):
    cr.execute('''
        INSERT INTO ms2view_pn_do (name_int, name, plan_siod_id, spbu_name, ship_to, plant)
        select cast(name as bigint) as name_int,* from (
        select unnest(string_to_array(loading_order, ', ')) as name, 
        ms2_id, 
        replace(no_spbu,'.','') as spbu_name,
        ship_to,
        plant
        from ms2view_plan_siod
        ) a
        ''')  
    cr.commit()  
#     select ms2_id, cast(lo as bigint) from (
# select ms2_id, unnest(string_to_array(loading_order, ', ')) as lo
# from ms2view_plan_siod
# ) a
# 
# select cast(name as bigint) as name_int,* from (
# select unnest(string_to_array(loading_order, ', ')) as name, 
# ms2_id, 
# replace(no_spbu,'.','') as spbu_name,
# ship_to,
# plant
# from ms2view_plan_siod
# ) a
# """

def extract_SelectionField_from_MS2(cr, ms2field, ms2fieldval, domain):
    cr.execute('''
    INSERT INTO pn_selection_field (shortcut,name, domain)
    SELECT %(ms2field)s, %(ms2field)s, '%(domain)s' FROM
    (
        SELECT MV.*, sf.name,shortcut,domain
        FROM
            (SELECT DISTINCT %(ms2fieldval)s
            FROM ms2view_plan_siod) mv
        LEFT JOIN 
            (SELECT * FROM pn_selection_field 
            WHERE domain = '%(domain)s')
        sf ON sf.shortcut = mv.%(ms2field)s
        WHERE domain is null
    ) A
    ''' % locals() ) 
    cr.commit()
    
def tandai_TempDo__ygLinkKe_PnDo(cr):
    # 1. fill PN_DO.name_int
    cr.execute('''SELECT count(*) FROM pn_do 
        where  
        name IS NOT NULL 
        and (name_int = 0 or name_int IS NULL)''')
    if cr.fetchone()[0]:
        cr.execute('''UPDATE pn_do 
            SET name_int = cast(name AS bigint)
            WHERE 
                -- name != '' AND 
                name is not null 
                AND (name_int = 0 OR name_int IS NULL)''')
        cr.commit()
    # sync do >> ms2.do
    cr.execute('''
        UPDATE ms2view_pn_do d 
        SET 
            pn_do_id = A.id,
            shipment_request_id = A.shipment_request,
            update_level = CASE WHEN update_level IS NULL THEN 1 ELSE update_level+1 END
        FROM 
        pn_do A
        WHERE d.name_int = A.name_int
        ''')
    cr.commit()

def tandai_TempDo__AddUpdateLevel(cr):
    "ini dibutuhkan ketika tidak ada download LO, agar informasi summary-nya sesuai"
    cr.execute('''
        UPDATE ms2view_pn_do d 
        SET             
            update_level =  update_level+1 
        FROM 
        pn_do A        
        WHERE update_level IS NOT NULL 
        ''')
    cr.commit()
        
def tandai_pndo2(cr):    
    cr.execute('''UPDATE ms2view_plan_siod d 
        SET pn_shipment_request_id = A.id
        FROM pn_shipment_request A
        WHERE d.ms2_id = A.name_int''')
    cr.commit()
    # sync ms2.do > do
    
def tandai_TempDo__ygLinkKe_ShipmentRequest(cr):
    cr.execute('''
        UPDATE ms2view_pn_do d 
        SET shipment_request_id = A.pn_shipment_request_id
        FROM ms2view_plan_siod A
        WHERE d.plan_siod_id = A.ms2_id
        ''')
    cr.commit()  
          
def update_agregate_ShipmentRequest(cr,req_date_expected):
#     cr.execute('''
#         UPDATE pn_shipment_request s
#         SET kl_found = a.kl_found
#         FROM (
#             SELECT SUM(d.kl_do_float) AS kl_found, t.shipment_request_id
#                      FROM ms2view_pn_do t
#                     INNER JOIN pn_do d ON d.id = t.pn_do_id
#             GROUP BY t.shipment_request_id
#         )A
#         WHERE A.shipment_request_id = s.id
#         ''')
    cr.execute('''
        UPDATE pn_shipment_request s
        SET kl_found = a.kl_found
        FROM (
            SELECT SUM(d.kl_do_float) AS kl_found, d.shipment_request
            FROM pn_do d             
            WHERE d.req_date_expected = %s -- '2014-10-16'
            AND d.shipment_request IS NOT NULL
            GROUP BY d.shipment_request
        )A
        WHERE A.shipment_request = s.id
        ''', (req_date_expected,) )
    cr.commit()

def update_klSisa_ShipmentRequest(cr,date_expected):
    cr.execute('''
        UPDATE pn_shipment_request s
        SET kl_sisa = kl_do_float - kl_found
        WHERE date_expected = %s 
        ''', (date_expected,) )
        
    cr.commit()
    
def tandai_PnDo__linkKe_ShipmentRequest_byInnerJoin(cr):    
    cr.execute('''
        UPDATE pn_do d 
        SET shipment_request = A.pn_shipment_request_id,
            req_date_expected = A.date_expected
        FROM (
            SELECT d.pn_do_id, s.pn_shipment_request_id, ms2_id, s.date_expected
            FROM ms2view_pn_do d
            INNER JOIN ms2view_plan_siod s ON d.plan_siod_id = s.ms2_id
        )A WHERE A.pn_do_id = d.id
        ''')
    cr.commit()
    
def cantelkan_PnDo__Ke_ShipmentRequest__by_TempDO(cr):        
    cr.execute('''
        UPDATE pn_do d
        SET shipment_request = vdo.shipment_request_id,
            req_date_expected = vreq.date_expected,
            shift_shipment = vreq.shift, 
            plancategory = vreq.status_plan, 
            active=true
        FROM ms2view_pn_do vdo
        LEFT JOIN ms2view_plan_siod vreq ON (vdo.plan_siod_id = vreq.ms2_id)
        WHERE vdo.pn_do_id = d.id
        ''')
    cr.commit()    
#    cr.execute('''
#        UPDATE pn_do d 
#        SET shipment_request = A.shipment_request_id
#        FROM ms2view_pn_do A 
#        WHERE A.pn_do_id = d.id
#        ''')
#    cr.commit()
     
def extract_TempSpbu_from_MS2(cr):
    cr.execute('''
        INSERT INTO ms2view_pn_spbu (spbu_name, no_spbu, ship_to, pasti_pas, no_hp, nama_kota, id_kota, plant)
        SELECT DISTINCT 
        replace(no_spbu,'.','') as spbu_name, no_spbu,
        ship_to,
        pasti_pas,
        no_hp,
        nama_kota,
        id_kota,
        plant
        from ms2view_plan_siod
        ''')
    cr.commit()
    
def tandai_TempSpbu_ygLinkKe_SpbuMaster(cr):
    #isi ID spbu, by shipto
    cr.execute('''
        UPDATE ms2view_pn_spbu m 
        SET 
            pn_spbu_id = A.spbu_id,
            update_level = CASE WHEN update_level IS NULL THEN 1 ELSE update_level+1 END
        FROM 
        (
            SELECT min(s.id) as spbu_id, sm.name, sm.shipto 
            FROM pn_spbu s
            INNER JOIN pn_spbu_master sm on sm.id = s.pn_spbu_master_id
            WHERE sm.active=true
            GROUP BY SM.NAME,sm.shipto 
        ) A
        --- WHERE m.spbu_name = A.name
        WHERE m.ship_to = A.shipto
        ''')    
    # isi name siod, by id
    cr.execute('''
        UPDATE ms2view_pn_spbu m 
        SET 
            spbu_name_siod = A.name,
            pn_spbu_master_id = A.spbu_master_id
        FROM 
        (
            SELECT s.id as spbu_id, sm.id as spbu_master_id, sm.name 
            FROM pn_spbu s
            INNER JOIN pn_spbu_master sm on sm.id = s.pn_spbu_master_id
            WHERE sm.active=true
        ) A        
        WHERE m.pn_spbu_id = A.spbu_id
        ''')
    cr.commit()
    
def koreksi_SpbuMasterName_ygSamaDgn_ShipTo(cr):
    cr.execute('''
        UPDATE pn_spbu_master m 
        SET 
            name = A.spbu_name,
            name2 = A.no_spbu
        FROM 
            ms2view_pn_spbu A        
        WHERE 
            A.spbu_name_siod = A.ship_to
            AND A.pn_spbu_master_id = m.id
        ''')
    cr.commit()
        
def count_TempSPBU__ygNOTlinkKe_PnSpbu(cr):
    cr.execute('''SELECT count(*) FROM ms2view_pn_spbu 
        WHERE pn_spbu_id is null''')
    return cr.fetchone()[0]
    
def buat_Spbu_baru(cr,uid, fasum):
    #HAPUS TEMPORARY
    atemp_spbu.Clear_AtempSPBU(cr)
    #ISIKAN
    cr.execute('''
        INSERT INTO atemp_spbu (name, name2, shipto, plant, res_company_id,
            smsnumber, id_kota, nama_kota)
        SELECT DISTINCT 
           spbu_name, no_spbu, ship_to, plant, %s AS company_id,
           no_hp, id_kota, nama_kota
                       
        FROM ms2view_pn_spbu
        WHERE pn_spbu_id IS NULL
        ''', (fasum['company_id'],))
    cr.commit()
        
    atemp_spbu.Create_SPBU(cr, uid, fasum)
    
def read_planning_from_MS2_view(cr,SQLquery):
    import pymssql
    from pprint import pprint
    global MS2centralrunning
    msg = ''
    dt_csvarray =[]       
    planning_ref = pooler.get_pool( cr.dbname ).get( 'ms2view.plan_siod' )
    #===============================================================================
    # Read Planning From MS2 View
    #===============================================================================
    section = 'SQLServerMS2'
    dbserver = str( pn2_conf[section]['dbserver'] )
    dbuser = str( pn2_conf[section]['dbuser'] )
    dbpassword = str( pn2_conf[section]['dbpassword'] )
    dbname = str( pn2_conf[section]['dbname'] )

    #Connect To MS2 Server    
    try:
        conn_mssql = pymssql.connect(host=dbserver, user=dbuser, password=dbpassword, database=dbname)
        cr_mssql = conn_mssql.cursor()
        
        #Execute Query
        try:
            cr_mssql.execute(SQLquery)        
            rows = cr_mssql.fetchall_asdict()
        
            #Parse To CsvArray
            csvarray = []
            KEYS = ['NO_SPBU', 'SHIP_TO', 'PASTI_PAS', 'JENIS_BBM', 'SHIFT', 'QTY', 'PLANT', 
                    'KETAHANAN_HARI', 'LOADING_ORDER', 'NO_HP', 'QTY_ORI', 'SHIFT_REQUEST', 
                    'ID_KOTA', 'NAMA_KOTA', 'STATUS_PLAN','TGL_KIRIM']
            keys =dict((k.lower(),k,) for k in KEYS)
            KEYS.append('ID')
            
            keys['ms2_id'] ='ID'
            #pprint(keys)
            csvarray.append(KEYS)
            try:
                irow = 0
                for row in rows:
                    csvarray.append([str(row['ID']), str(row['NO_SPBU']), str(row['SHIP_TO']), str(row['PASTI_PAS']), str(row['JENIS_BBM']), row['SHIFT'], str(row['QTY']), str(row['PLANT']), str(row['KETAHANAN_HARI']), str(row['LOADING_ORDER']), str(row['NO_HP']), str(row['QTY_ORI']), str(row['SHIFT_REQUEST']), str(row['ID_KOTA']), str(row['NAMA_KOTA'])])
                    irow += 1
                    #print "ROOOOOOOOOOOOODADDDDAAAT:" #,row
                    dat = dict((k,str(row[v])) for k,v in keys.iteritems() if row[v])
                    #pprint(keys)
                    #print "^^^^^^^^^^^^@@d:",dat
                    #pprint(dat)
                    planning_ref.create(cr,1,dat)
                #cr.commit()
                    
                    
                return csvarray,'',irow
            except:
                print sys.exc_info()[1]
                msg =  "Get Data Planning MS2 gagal"
                MS2centralrunning = False            
                return [3],msg,0

        except:
            print sys.exc_info()[1]
            msg =  "Data Planning Tidak Tersedia! Silahkan coba beberapa saat lagi"
            MS2centralrunning = False
            return [2],msg,0            
        
    except:
        print sys.exc_info()[1]            
        msg =  "Koneksi dengan Server MS 2 gagal! Silahkan coba beberapa saat lagi"
        MS2centralrunning = False
        return [1],msg,0

def count_TempDo__ygNOTlinkeKe_PnDO(cr):
    cr.execute('''SELECT count(*) FROM ms2view_pn_do 
        WHERE pn_do_id is null''')
    return cr.fetchone()[0]
            
def count_TempDo__ygNOTlinkeKe_ShipmentRequest(cr):
    cr.execute('''SELECT count(*) FROM ms2view_pn_do 
        WHERE shipment_request_id is null''')
    return cr.fetchone()[0]
            

def download_unavailable_pndo(self, cr, uid, fasum):
    # 1. fill PN_DO.name_int
    unavailable_lonumbers = []
    cr.execute('''SELECT count(*) FROM ms2view_pn_do where pn_do_id is null''')
    if cr.fetchone()[0]:
        cr.execute('''SELECT name 
            FROM ms2view_pn_do 
            WHERE pn_do_id is null''')
        rows = cr.fetchall()
        for row in rows:
            unavailable_lonumbers.append(str(row[0]))
        print "DOWNLOADING %s LOS" % len(unavailable_lonumbers)
    #print unavailable_lonumbers
    if not unavailable_lonumbers:
        return []
    
    
    #---download if necessary
    fs_mysap = fasum['ref'].create(cr,uid, {'name': 'Download %s LO from MySAP' % len(unavailable_lonumbers),
                                                     'started': datetime.now(), 
                                                     'parent_id' : fasum['lo']}) 
    try:
        #lo_centralmysap_log = True
        param={} 
        param['nomorlo'] = unavailable_lonumbers
        #lo_centralmysap_log,data_msg =      updateLOByNumberFromMySAP( self, cr, uid,param, scenario=1, callsource=1, reconstruct=False)
        lo_centralmysap_log,data_msg = DownloadLO_ByLONumber_FromMySAP( self, cr, uid,param, fasum)
        if lo_centralmysap_log:
            print 'Success Download New LO',lo_centralmysap_log
            print "LO NUMBERS:",len(unavailable_lonumbers)
        else:
            print 'Not Success Download New LO',lo_centralmysap_log
            print "MESSAGE:",data_msg
    #except:
        # KOneksi ke MySAP Gagal
        #print sys.exc_info()[1]
        pass
    except Exception, e:
        #logger.error('Failed to upload to ftp: '+ str(e))
        #print "Unexpected error:", sys.exc_info()[0]
        print "Unexpected error:", str(e)
    finally:
        fasum['ref'].write(cr,uid, fs_mysap, {'finished' : datetime.now()})
    
    return unavailable_lonumbers    
# Untuk Proses Reconstruksi LO baru yg di dapat dari data MS2 !!!!  
# def reconstructNewLOMS2( self, cr, uid, pooler, req_id = 0, nolo = '0'):
#     try:
#         #lo_centralmysap_log = True
#         param={} 
#         param['nomorlo'] = [nolo]
#         lo_centralmysap_log,data_msg = updateLOByNumberFromMySAP( self, cr, uid,param, scenario=1, callsource=1, reconstruct=False)
#         if lo_centralmysap_log:
#             print 'Success Download New LO',nolo
#             # Get DATA SHIPMENT REQUEST
#             reqref = pooler.get_pool( cr.dbname ).get( 'pn.shipment.request' )
#             req_ids = reqref.search( cr, uid, [( 'id', '=', req_id )] )
#             dicReqVal=reqref.read(cr,uid,req_ids,[])[0]
#             #print 'dicReqVal: ',dicReqVal 
#             ### Proses berikutnya Update data PN_DO untuk merelasikan dengan PN_SHIPMENT_REQUEST !!!
#             query = "UPDATE pn_do SET date_shipment_plan='%s',shift_shipment=%s,plancategory='%s',shipment_request='%s',active=true WHERE name_int=%s" % \
#                 ( dicReqVal['date_expected'], dicReqVal['shift_shipment'], dicReqVal['plancategory'], req_id, str(nolo).strip() )
#             try:
#                 cr.commit()
#                 #print 'Query: ',query
#                 cr.execute( query )
#                 #To actually record the operation above to database do this:
#                 cr.commit()                
#                 print 'Successfully Update LO Master [%s] Link Planning [%s]'% (nolo,dicReqVal['name'])
#                 
#                 ### Proses berikutnya jalankan function calculateT_VAL untuk mendapatkan t_val_min dan t_val_max di shipment request !!!
#                 todoobj=pooler.get_pool(cr.dbname).get( "pn.shipment.request" )
#                 todoobj.calculateT_VAL(cr,uid,dicReqVal['date_expected'])
#                 
#                 print 'Successfully Calculate t_val_min / t_val_max Found'
#                 
#                 ### Proses berikutnya jalankan function CalculateKLFound untuk mendapatkan kl found di shipment request !!!
#                 shipreqobj = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#                 shipreqobj.calculateKLFound(cr,uid,[req_id])
#                 ### TODO: Buat informasi LO berhasi di relasikan dengan pn_Shipment_request
#                 #print 'ADD LO',jmllo
#                 print 'Successfully Calculate KL Found'
#             
#                 ### Proses berikutnya jalankan function untuk membandingkan kl yg diminta dengan maxmt SPBU !!!
#                 validobj = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#                 validobj.calculateValidFound(cr,uid,[req_id])
#                 
#                 print 'Sukses membandingkan KL yang diminta dengan maxmt SPBU'
#                 
#             
#             except:
#                 cr.rollback()
#                 print 'Gagal Update DATA LO !!!!',nolo
#                 pass
#             pass
#         else:
#             print 'Not Success Download New LO',nolo
#     except:
#         # KOneksi ke MySAP Gagal
#         print sys.exc_info()[1]
#         pass
#     
#     return {}

# def reconstructLOMS2( cr, uid, pooler, data, waktuGIGO = [], spbuinsertname = 0 ):
#     try:
#         do_ids = [];msg="";
#         doref = pooler.get_pool( cr.dbname ).get( 'pn.do' )
#         datefields = ['date_shipment_plan', 'date_terima']
#         for datefield in datefields: #clean up bad data
#             try:
#                 if data[datefield] in [None]:
#                     del data[datefield] 
#             except: pass
#         parsingutil.cleanText2( data, ['name'] )    
#         do_ids = doref.search( cr, uid, [( 'name', '=', data['name'] )] )
#         query=''
#         if do_ids: #Kalau data DO sudah ada (berarti data SPBU juga sudah ada)
#             ### Proses berikutnya Update data PN_DO untuk merelasikan dengan PN_SHIPMENT_REQUEST !!!
#             query = "UPDATE pn_do SET date_shipment_plan='%s',shift_shipment=%s,plancategory='%s',shipment_request='%s' WHERE id=%s" % \
#                 ( data['date_shipment_plan'], data['shift_shipment'], data['plancategory'], data['pnshipreq_id'], do_ids[0] )
#             try:
#                 cr.commit()
#                 cr.execute( query ) 
#                 #To actually record the operation above to database do this:
#                 cr.commit
#                 
#                 ### Proses berikutnya jalankan function calculateT_VAL untuk mendapatkan t_val_min dan t_val_max di shipment request !!!
#                 todoobj=pooler.get_pool(cr.dbname).get( "pn.shipment.request" )
#                 todoobj.calculateT_VAL(cr,uid,data['date_shipment_plan'])
#                 
#                 ### Proses berikutnya jalankan function add_LO untuk mendapatkan kl found di shipment request !!!
#                 shipreqobj = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#                 shipreqobj.calculateKLFound(cr,uid,[data['pnshipreq_id']])
#                 
#                 ### Proses berikutnya jalankan function untuk membandingkan kl yg diminta dengan maxmt SPBU !!!
#                 validobj = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#                 validobj.calculateValidFound(cr,uid,[data['pnshipreq_id']])
#                 
#                              
#                 ### TODO: Buat informasi LO berhasi di relasikan dengan pn_Shipment_request
#                 #print 'ADD LO',jmllo
#                 return True,do_ids[0],msg
#             except:
#                 msg = "Error Update LO Master [No.LO:%s]" % data['name']
#                 return False,0,msg
#             
#         else:
#             #print 'No.LO',data['name']
#             msg = ""
#             return False,0,msg
#     except:
#         msg = "Error Update Reconstruct LO MS2:  [No.LO:%s]" % data['name']
#         return False,0,msg
#     
#     
# 
# 
# def parseloarrayplanningms2( self, cr, uid, reader, importDefinitionCsvFilePath = '', data = {'plancategory':'H-1'} ):
#     #'plancategory' : fields.selection([('0','H-1'),('1','H0'), ('2','HI')], 'Kategori Planning', readonly=True),
#     msg = '';new_dataLO=[]
#     # read the first line of the file (it contains columns titles)
#     for row in reader:
#         if row:
#            f = row
#            break
#     
#     #ambil index tiap header e.g. 'kl_do=0'
#     for i in range( 0, len( f ) ):
#         exec( '%s = %s' % ( f[i], i ) )
#     
#     #cocokkan field internal dgn field dari file yg diimport
#     try:
#         importEquivalences = csv.reader( open( importDefinitionCsvFilePath, "rb" ) )
#     except:
#         raise osv.except_osv( _( 'Error !' ), _( "File ini tidak bisa dibuka: %s" % ( importDefinitionCsvFilePath ) ) )
#         msg = "File ini tidak bisa dibuka: %s" % ( importDefinitionCsvFilePath )
#         return '',msg    
#     
#     equivalencesImpor = [equivalence for equivalence in importEquivalences]
#     
#     shipmentrequestref = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#     spburef = pooler.get_pool( cr.dbname ).get( 'pn.spbu' )
#     partnerref = pooler.get_pool( cr.dbname ).get( 'res.partner' )
#     companyref = pooler.get_pool( cr.dbname ).get( 'res.company' )
#     klref = pooler.get_pool( cr.dbname ).get( 'pn.selection.field' )
#     
#     #TASK SPECIFIC
#     # read the rest of the file
#     data['name'] = 0
#     rowi = 0
#     reader = list( reader )
#     rowm = len( reader )
#     depotcode = parsingutil.cleanText( data['kodedepot'] )
#     from math import ceil
#     jml_in = 0
#     for row in reader: #the variable name gk boleh diganti krn dipakai di equivalencesImpor
#         #print row
#         if (rowi==0):
#             rowi += 1
#             continue
#         
#         rowi += 1
#         #parsingutil.showProgress( rowi, rowm, '(%d/%d) MS2ID:%s' % ( rowi, rowm, row[0] ) )
#         # skip empty rows and rows
#         if ( not row ):
#             continue
#         
#         #assign the value to data dictionary (value from csv to data dictionary )
#         for equivalence in equivalencesImpor:
#             data[equivalence[0]] = eval( equivalence[1] )
#             
#         
#         if depotcode != 'CENTRAL' and data['depot'] != depotcode : continue
# 
#         data['no_spbu'] = re.sub( '[%s]' % re.escape( string.punctuation ), '', data['no_spbu'] ) #remove punctuation
#         data['shipto'] = re.sub( '[%s]' % re.escape( string.punctuation ), '', data['shipto'] ) #remove punctuation
#         if data['shipto'] in ('','0'):
#             data['shipto'] = data['no_spbu']
#         #print data
#         
#         #shipmentrequest
#         # def checkncreate(cr, uid, context,val,sel_obj,update=False): 
#         kl_id,log = parsingutil3.reconstructSelectionField( cr, uid, pooler, data['shipment_kl_do'],alwaysupdate=False,reconstruct=True,log=False )
#         parsingutil3.reconstructSelectionField( cr, uid, pooler, '', data['produk_id'] )
#         #shift_id=parsingutil.reconstructShiftSelectionField(cr,uid,pooler,{'shift_shipment': data['shift_shipment']})
#         #data['spbu_id']=checkncreate( cr, uid,[('shipto', '=',data['shipto'] )] ,{
#         company__id = parsingutil3._default_company(self,cr,uid)
#         try:
#             #search by shipto as its some spbu can have several unique spbu name
#             #output is the id of pn.spbu, not id of pn.spbu.master! Remember they are INHERITS
# #                data['spbu_id'],log = checkncreate( cr, uid, [( 'shipto', '=', data['shipto'] )] , {
# #                                                                                     'company_id':company__id,     
# #                                                                                      'name':data['no_spbu'],
# #                                                                                      'shipto':data['shipto']}, spburef, alwaysupdate=True,reconstruct=True,log=False ) #SPBU
#             #phone number formatting
#             try:
#                 data['smsnumber'] = data['smsnumber'].strip()
#                 if data['smsnumber'][0]=='0': #021525
#                     data['smsnumber']=data['smsnumber'].lstrip('0')
#                     data['smsnumber']='+62'+data['smsnumber']
#                 elif data['smsnumber'][0]!='+': #6221525
#                     data['smsnumber']='+'+data['smsnumber']
#                 else: #+6221525
#                     pass
#             except:
#                 pass
#             # data kota 
#             data['city']=data['city'].strip()
#             data['city_id']=data['city_id']
#             
#             data['spbu_id'],log = checkncreate( cr, uid, [( 'shipto', '=', data['shipto'] )] , {
#                                                                                  'company_id':company__id,     
#                                                                                   'name':data['no_spbu'],
#                                                                                   'shipto':data['shipto'],'smsnumber':data['smsnumber'],'city':data['city'],'city_id':data['city_id']}, spburef, alwaysupdate=True,reconstruct=False,log=False ) #SPBU
# 
#         except:
#             print 'error spbu:',data['spbu_id']
#             msg += ' || Error spbu:'+str(data['spbu_id'])+ ' || No Reg:'+str(data['spbureq_id'])
#             continue
#         
#         if data['spbu_id']=='NA': 
#             msg += ' || Error spbu:'+str(data['spbu_id'])+' || No Reg:'+str(data['spbureq_id'])
#             continue
# 
#         #create depot
#         data['partner_id'],log = checkncreate( cr, uid, [( 'ref', '=', data['depot'] )] , {'name':data['depot'], 'ref':data['depot']}, partnerref ) 
#         data['company_id'],log = checkncreate( cr, uid, [( 'ref', '=', data['depot'] )] , {'name':data['depot'], 'ref':data['depot'], 'partner_id':data['partner_id']}, companyref )
#         
#         #cret kl
#         data['shipment_kl_do'] = str( float( '0' + data['shipment_kl_do'] ) )
#         data['shipment_kl_do_float'] = float( '0' + data['shipment_kl_do'] )
#         
#         dummykl,log = checkncreate( cr, uid, [( 'ref', '=', data['depot'] )] , {'name':data['depot'], 'ref':data['depot']}, partnerref,alwaysupdate=False,reconstruct=True,log=False )
# 
#         #===================================================================
#         # query="INSERT INTO pn_shipment_request(name,no_spbu,kl_do,produk_id,stokclaimed,active,state,date_expected,shift_shipment) \
#         #         VALUES ('%s',%s,'%s','%s',%s,True,'0', '%s','%s') \
#         #         " % (data['spbureq_id'],data['spbu_id'],data['shipment_kl_do'],data['produk_id'],data['stokclaimed'], data['date_shipment_plan'],data['shift_shipment'])
#         # #cr.execute(query)        
#         #=========================================r==========================
#         #cr.commit() #Write to database            
#         #shipmentreq_id= shipmentrequestref.search(cr, uid, [('name', '=',data['spbureq_id'])])
#         
#         #shipmentrequest_id=parsingutil.checkncreate( cr, uid,[('name', '=',data['spbureq_id'] )] ,{'name':data['spbureq_id'],'no_spbu':data['no_spbu'], 'date_expected':data['date_shipment_plan'], 'kl_do':data['kl_do'], 'stokclaimed':data['stokclaimed'], 'produk_id':data['produk_id'],'shift_shipment':data['shift_shipment'] },shipmentrequestref) #SPBU==>ERROR
#         
#         #=======================================================================
#         #
#         # INSERT DATA PN_SHIPMENT REQUEST
#         #
#         #=======================================================================
#         data['id'] = row[0]
#         data['pnshipreq_id']=False
#         data['pnshipreq_id'],msg_update = _checkncreate_pnshipmentreq( cr, uid, data )
#         if(msg_update==''):
#             jml_in += 1
#         else:
#             msg += msg_update
#         #=======================================================================
#         
# #===============================================================================
# #            data['spbureq_id']=''+str(data['plancategory'])+str(data['spbu_id'])+str(data['produk_id'])
# # 
# #            query="INSERT INTO pn_shipment_request(name,no_spbu,kl_do,produk_id,stokclaimed,active,state,date_expected,shift_shipment) \
# #                     VALUES (%(spbureq_id)s,%(spbu_id)s,%(shipment_kl_do)s,%(produk_id)s,%(stokclaimed)s,True,'0',%(date_shipment_plan)s,%(shift_shipment)s) " 
# #                     #" % (data['spbureq_id'],data['spbu_id'],data['shipment_kl_do'],data['produk_id'],data['stokclaimed'], data['date_shipment_plan'],data['shift_shipment'])
# #            #print "data:===================:",data
# #            cr.execute(query, (data))
# #===============================================================================
# 
#         #print cr.query        
#         
#         #LO data dianggap sudah ada di DBase
#         try:
#             if ( str(data['lonames']).upper() != 'NONE' and str(data['lonames']).upper() != 'NULL' ):
#                 lonames = data['lonames'].split( ',' ) #split lo number 
#                 for loname in lonames:
#                     data['name'] = loname
#                     #Keterangan Untuk View SQL (tidak ada data kl per do)
#                     #data['name'], data['kl_do'] = loname.split( '-' )
#                     #data['kl_do'] = ceil(float(data['kl_do']))
#                     #
#                     state,do_ids,msg_recLOms2 = reconstructLOMS2( cr, uid, pooler, data, [], 1 )
#                     #===========================================================
#                     #Cek Hasil Reconstruct LO MS2
#                     if(state==False):
#                         if (msg_recLOms2==""): 
#                         ### Jika LO tidak tersedia di Tabel LO Simpan dalam LOArray untuk dilakukan proses berikutnya [DOWNLOAD LO FORM MYSAP with NO LO] 
#                         ### Note : Proses [DOWNLOAD LO FORM MYSAP with NO LO] dilakukan Setelah proses INPUT SHIPMENT SELESAI !!!! data di tampung dalam arry
#                             #print 'ADD LO :',data
#                             new_dataLO.append([loname,data['pnshipreq_id']])
#         except:
#             pass
#     
#     #End Of loop
#     return data['pnshipreq_id'],msg,jml_in,new_dataLO
# 
# def _checkncreate_pnshipmentreq( cr, uid,data ):
#     msg = ''
#     data_req = {}
#     shipmentrequestref = pooler.get_pool( cr.dbname ).get( "pn.shipment.request" )
#     data_req['name']=data['spbureq_id']
#     data_req['no_spbu']=data['spbu_id']
#     data_req['kl_do']=data['shipment_kl_do']
#     data_req['kl_do_float']=data['shipment_kl_do_float']
#     data_req['produk_id']=data['produk_id']
#     data_req['stokclaimed']=data['stokclaimed']
#     data_req['active']=True
#     data_req['state']='0'
#     data_req['date_expected']=data['date_shipment_plan']
#     data_req['shift_shipment']=data['shift_shipment']
#     data_req['depot']=data['company_id']
#     data_req['planningsource']='ms2'
#     data_req['plancategory']=data['plancategory']
#     data_req['date_order']=data['date_order']
#     data_req['qty_ori']=data['qty_ori']
#     data_req['shift_request']=data['shift_request']
#     
#     try:
#         pnshipreq_id,log = checkncreate( cr, uid, [( 'name', '=', data['spbureq_id'] )] , data_req, shipmentrequestref,alwaysupdate=True,reconstruct=True,log=True,cleaningfields=False )
#         print 'planning id = ' + str(pnshipreq_id)
#         return pnshipreq_id,''  
#     except:
#         #Data Shipment Request sudah ada
#         msg = '[Double No Reg:%s]' %(data['spbureq_id'])
#         return 0,msg    
#             
# 
# def _createupdate_pnshipmentreq( cr, uid,data ):
#     msg = ''
#     data['spbureq_id'] = data['id']
#         #'%(no_spbu)s@%(date_shipment_plan)s#%(shift_shipment)s:%(produk_id)s=%(shipment_kl_do)s' % (data)
#         #'%(plancategory)s@%(date_shipment_plan)s#%(shift_shipment)s||%(no_spbu)s:%(produk_id)s=%(shipment_kl_do)s' % (data)
# 
#     cr.execute( "SELECT count(*) FROM pn_shipment_request where name = %(spbureq_id)s", ( data ) )
#     #cr.commit()
#     jml = cr.fetchall()[0][0]
#     print "U=%d" % jml
#     #DepotList = [depot[0] for depot in depots if depot[0]!=None] #listing daftar depot yg depot!=None            
#     if not jml:
#         query = "INSERT INTO pn_shipment_request(name,no_spbu,kl_do,kl_do_float,produk_id,stokclaimed,active,state,date_expected,shift_shipment,depot,planningsource,plancategory,date_order) \
#              VALUES ( %(spbureq_id)s,%(spbu_id)s,%(shipment_kl_do)s,%(shipment_kl_do_float)s,%(produk_id)s,%(stokclaimed)s,True,'0',%(date_shipment_plan)s,%(shift_shipment)s,%(company_id)s,'ms2',%(plancategory)s,%(date_order)s )" 
# 
#     #" % (data['spbureq_id'],data['spbu_id'],data['shipment_kl_do'],data['produk_id'],data['stokclaimed'], data['date_shipment_plan'],data['shift_shipment'])
#     #print "data:===================:",data
#     #===========================================================================
#     # else:
#     #    query="UPDATE pn_shipment_request(name,no_spbu,kl_do,produk_id,stokclaimed,active,state,date_expected,shift_shipment) \
#     #         SET no_spbu=%(spbu_id)s,%(shipment_kl_do)s,%(produk_id)s,%(stokclaimed)s,True,'0',%(date_shipment_plan)s,%(shift_shipment)s) " 
#     #===========================================================================
#         try:
#             cr.execute( query, ( data ) )
#             cr.commit()
#             # GET ID
#             query = "SELECT ID FROM pn_shipment_request where name = %(spbureq_id)s" 
#         
#             #" % (data['spbureq_id'],data['spbu_id'],data['shipment_kl_do'],data['produk_id'],data['stokclaimed'], data['date_shipment_plan'],data['shift_shipment'])
#             #print "data:===================:",data
#             #===========================================================================
#             # else:
#             #    query="UPDATE pn_shipment_request(name,no_spbu,kl_do,produk_id,stokclaimed,active,state,date_expected,shift_shipment) \
#             #         SET no_spbu=%(spbu_id)s,%(shipment_kl_do)s,%(produk_id)s,%(stokclaimed)s,True,'0',%(date_shipment_plan)s,%(shift_shipment)s) " 
#             #===========================================================================
#             cr.execute( query, ( data ) )
#             req_id = cr.fetchall()[0][0]
#             return req_id,''
#         except:
#             #Insert Gagal
#             msg = '[failed No Reg:%s]' %(data['spbureq_id'])
#             return 0,msg    
#     else:
#         #Data Shipment Request sudah ada
#         msg = '[Double No Reg:%s]' %(data['spbureq_id'])
#         return 0,msg    
#     
#     
#import centraldatacourier2
def clean_temp_table(cr, delete_previous_MS2plan):
    if delete_previous_MS2plan:
        cr.execute('DELETE FROM ms2view_plan_siod')    
    cr.execute('DELETE FROM ms2view_pn_spbu')    
    cr.execute('DELETE FROM ms2view_pn_do')
    cr.commit()
    

def prepare_dateRange(cr, params={}):
    section = 'PlanningMS2'
    #from datetime import datetime, timedelta    
    #format tanggal 09/27/09
    if params.has_key( 'datafrom' ) and params['datafrom'] != '':
        d1 = params['datafrom']
        planninguntil = d1
    else: 
        out = datetime.strptime( pn2_conf[section].get( 'planninglastwritten2' ) , '%Y-%m-%d' ) + timedelta( 1 ) 
        d1, timestring = str( out ).split()
        planninguntil = ''

    if params.has_key( 'datauntil' ) and params['datauntil'] != False:
        d2 = params['datauntil']
        planninguntil2 = d2
        lastwrittendate = ''
    else: 
        temp = str( datetime.today() ).split()
        todaysdate = temp[0]; todaystime = temp[1]
        d2 = todaysdate[0:4] + '-' + todaysdate[5:7] + '-' + todaysdate[8:10]
        planninguntil2 = ''
        lastwrittendate = d2

    arrdate = _listdate( d1, d2 ) #pecah tanggal mencadi harian
    return arrdate

def download_planning(cr, uid, kodedepot, arrdate, params,fasum):
    fs_ms2 = fasum['ref'].create(cr,uid, {'name':'Download Planning MS2',
                                          'parent_id': fasum['root'], 
                                          'started': datetime.now()})
    
    #fasum['ref'].write(cr,uid,[fasum['root']], val)
    #fasum['ref'].create(cr,uid, val)
    
    plancategory = {'H-1':'H_1', 'H0':'H_0', 'HI':'H_I'}
    total_row = 0            
    #Loop For Date 
    for datenow in arrdate:
        print "\n============= DONWLOAD SHIPMENT REQUEST:", datenow
        #Loop For Plan Category
        for plan in plancategory:
            #print "----------------- CATEGORY:", plan
            fs_cat = fasum['ref'].create(cr,uid, {'name': '%s (%s)' % (datenow,plan,),
                                                  'parent_id': fs_ms2, 
                                                  'started': datetime.now()})
            
            datesplit = str( datenow ).split( '-' )
            for ii in range( 0, len( datesplit ) ):
                datesplit[ii] = str( int( datesplit[ii] ) )
            [yyyy, mm, dd] = datesplit
            
            #For Filter Query
            if (plan=='H-1'):
                datefind = datetime.strptime( dd + '/' + mm + '/' + yyyy , '%d/%m/%Y' ) - timedelta( 1 )
                datefind = str(datefind).replace(' 00:00:00', '')
                xplan = "(STATUS_PLAN = 'H-1' or STATUS_PLAN is null)"
            else:
                datefind = datetime.strptime( dd + '/' + mm + '/' + yyyy , '%d/%m/%Y' ) - timedelta( 1 )
                datefind = str(datefind).replace(' 00:00:00', '')
                xplan = "STATUS_PLAN = '%s' " %(plan)

            print "----------------- CATEGORY:", plan, '@', datefind
            #AMBIL DATA DARI SERVER MS2 dan taruh di ARRAY
            query = """
                    SELECT ID, NO_SPBU, SHIP_TO, PASTI_PAS, JENIS_BBM, SHIFT, QTY, PLANT, KETAHANAN_HARI, 
                        LOADING_ORDER, NO_HP, QTY_ORI, SHIFT_REQUEST, ID_KOTA, NAMA_KOTA,
                        STATUS_PLAN, TGL_KIRIM
                    FROM View_Plan_SIOD 
                    WHERE 
                        TGL_KIRIM = '%s'
                    and PLANT = '%s'
                    and %s
            """ %(datefind,kodedepot,xplan)
            #===================================================================
            # Parse Field to CsvArray
            # Save CsvArray To ms2view.plan_siod
            #===================================================================
            #datalog['process_log_ref'].write( {'process_log': 'Getting data Server MS2' } )
            csvarray,csvmsg,jml_dt_ms2 = read_planning_from_MS2_view(cr, query )
            total_row += jml_dt_ms2
            fasum['ref'].write(cr,uid,[fs_cat],  {'finished': datetime.now(),'downloaded':jml_dt_ms2})
            
            saveToFile = False
            if saveToFile:
                fn = str(datetime.now()).replace(':','.')                
                f = open('C:\\%s.txt' % fn, 'w')
                f.writelines("%s\n" % item  for item in csvarray)
        
        # each day:
        # set date_expected to ms2view_plan_siod
        fill_plan_siod__date(cr,datefind, datenow) 
        siapkan_shipment_request_untuk_sinkronisasi(cr,datenow)   
         
    fasum['ref'].write(cr,uid,[fs_ms2],  {'finished': datetime.now(),'downloaded': total_row})

#global variable to ensure that only one of this script running, to avoid overlapping
MS2centralrunning=False 

def routineprocessgui( self, cr, uid, params = {}, schedule = 'daily', 
                       tipeplanning = '0', depotonly=False ):
    
    #---check: running in CENTRAL
    if getThisCompanyData(self,cr,uid)[0]['ref']=='CENTRAL':
        raise osv.except_osv( _( 'Error !' ), "Function running from CENTRAL" ) 
    
    global MS2centralrunning
    
    #---check: single-instance-only
    if MS2centralrunning:
        msg_info="Dibatalkan! Fungsi yang sama masih berjalan"
        raise osv.except_osv( _( 'Error !' ), msg_info )
    else:
        MS2centralrunning=True
        
    
    if not params.has_key('override'): params['override'] = False    
    msg_info = ''
    msg_warning=''
    company_id = params['form'].get('company_id',1)
    
    
    #get plandate
    #format tanggal 09/27/09
    arrdate = prepare_dateRange(cr, params)
    
    fs = pooler.get_pool( cr.dbname ).get( 'fast.summary' )
    fd = 'Import Planning MS2 '+ str(arrdate[0]) 
    if arrdate[0] != arrdate[-1]:
        fd += ' - ' + str(arrdate[-1])
    
    fasum = {
         'ref'  : fs,
         'root' : fs.create(cr, uid,{'name':fd, 'started': datetime.now()}),
         'company_id' : company_id,
         }

        
    #---TRY:
    # catch jika ada error apapun kembalikan nilai MS2centralrunning ke False
    try:
        #---[1] DOWNLOAD PLANNING FROM MS2
        

        kodedepot = str( pn2_conf['MachineSpesific']['kodedepot']  ).upper()
        company_ref = pooler.get_pool( cr.dbname ).get( 'res.company' )
        rcompanies = company_ref.read(cr, uid, [company_id],['ref'])
        if rcompanies:
            kodedepot = rcompanies[0]['ref']
        
        
    
        #--clean up the temporary tables
        #--jangan hapus dulu deh, coba cek apakah hanya perlu inject yg gagal saja?
        if params['form'].get('download_planning',True):            
            clean_temp_table(cr, delete_previous_MS2plan=True)
            download_planning(cr, uid, kodedepot, arrdate, params,fasum)
            
        else:
            clean_temp_table(cr, delete_previous_MS2plan=False)
        
            
        
            
        #---[2] PARSING SHIPMENT REQUEST TEMP        
        tandai_TempPlanning__levelZero(cr)
        tandai_TempPlanning__ygLinkKe_ShipmentRequest(cr)
        
        #f_sum.write(cr, uid, [fs_id], {'downloaded': })
        
        #--stop jika semua planning MS2 >> sudah ada di SIOD
        #if count_TempPlanning__ygNOTlinkKe_ShipmentRequest(cr) > 0:
        #bugfix: selalu update meskipun semua sudah ada: #BUGFIX: https://www.facebook.com/photo.php?fbid=10205052048165664&set=pcb.726860514061267&type=1&theater
        #if True: #ini akan selalu dijalankan
        
        fasum['spbu'] = fasum['ref'].create(cr,uid, {'name': 'Download Master SPBU',
                                                     'started': datetime.now(), 
                                                     'parent_id' : fasum['root']})    
        #---SPBU: buat spbu master jika diperlukan
        extract_TempSpbu_from_MS2(cr) 
        tandai_TempSpbu_ygLinkKe_SpbuMaster(cr)
        #TODO Done: BUAT SPBU BARU JIKA DITEMUKAN "pn_spbu_id" YG KOSONG
        if count_TempSPBU__ygNOTlinkKe_PnSpbu(cr) > 0:
            buat_Spbu_baru(cr,uid, fasum)
            #asumsikan ini telah disinkronkan, sekarang update ulang agar total summary benar:
        tandai_TempSpbu_ygLinkKe_SpbuMaster(cr)
        
        koreksi_SpbuMasterName_ygSamaDgn_ShipTo(cr)
        
            
        fasum__SPBU_updatetotal(cr, uid, fasum)

        #[2] SELECTION FIELD
        extract_SelectionField_from_MS2(cr, 'jenis_bbm', 'jenis_bbm', 'produk')
        #khusus utk "kl", formatnya adalah: 40.0 , 35.79 dst
        #jangan langsung inject float karena hasilnya akan 40, 36 dst
        extract_SelectionField_from_MS2(cr, 'qty', "to_char(qty, 'FM999990.0999') AS qty", 'kl')
        
        
        #[3] COMPANY
        #check partner
        #check company by ref   
        tandai_TempPlanning__ygLinkKe_SpbuMaster(cr)
        tandai_TempPlanning__ygLinkKe_ResCompany(cr) 
        
        #---BIKIN SHIPMENT-REQUEST  
        #date iterasi
        for datenow in arrdate:        
            siapkan_shipment_request_untuk_sinkronisasi(cr,datenow)
        
        inject_pn_shipment_request(cr)
        tandai_TempPlanning__ygLinkKe_ShipmentRequest(cr) #dipakai nanti oleh DO
        
        
        
        #fasum__root_updatetotal(cr,uid, fasum)
        #--- LO
        fasum['lo'] = fasum['ref'].create(cr,uid, {'name': 'Download LO',
                                                     'started': datetime.now(), 
                                                     'parent_id' : fasum['root']}) 
        create_unnest(cr) #fungsi yg diperlukan utk ekstrak dari string ke rows
        extract_TempDo__from_MS2(cr)
        # pass 1: link incoming from ms2: alakadarnya dulu..                        
        tandai_TempDo__ygLinkKe_PnDo(cr) #termasuk shiprequest.id
        
        #---stop download LO jika smua LO >> sudah ada
        if params['form'].get('download_lo',True) and  count_TempDo__ygNOTlinkeKe_PnDO(cr) > 0:            
            #---download if necessary
#             fs_mysap = fasum['ref'].create(cr,uid, {'name': 'Download LO from MySAP',
#                                                      'started': datetime.now(), 
#                                                      'parent_id' : fasum['lo']}) 
            #try:                
            download_unavailable_pndo(self,cr,uid, fasum)
                
            
                 
            # pass 2: link incoming from downloaded
            tandai_TempDo__ygLinkKe_PnDo(cr) #termasuk shiprequest.id
        else:
            tandai_TempDo__AddUpdateLevel(cr) #agar summary-nya sesuai
        
        fasum__DO_updatetotal(cr,uid, fasum)
        
        #--- connect LO ke shipment request
        if count_TempDo__ygNOTlinkeKe_ShipmentRequest(cr) > 0:
            #TODO: Optimize me. kasih flag LO mana saja yg harus diupdate utk mempersingkat waktu
            #    ini akan rancu antara yg sudah masuk dan baru akan masuk
            #    tapi langkah ini diperlukan oleh update_agreate()
            tandai_TempDo__ygLinkKe_ShipmentRequest(cr) 
            
            #tandai_PnDo__linkKe_ShipmentRequest_byInnerJoin(cr) #ini boleh, tapi tidak meninggalkan jejak. 
            cantelkan_PnDo__Ke_ShipmentRequest__by_TempDO(cr)
            pass
        
        #--- hitung_agregate_TempPlanning(cr)
        
        for datenow in arrdate:
            update_agregate_ShipmentRequest(cr,datenow)
            update_klSisa_ShipmentRequest(cr,datenow)
        
    # catch jika ada error apapun kembalikan nilai MS2centralrunning ke False 
    #except:
    except Exception, e:
        #logger.error('Failed to upload to ftp: '+ str(e))
        #print "Unexpected error:", sys.exc_info()[0]
        print "Unexpected error:", str(e)
        raise
        pass
    
    #--- FINALLY
    finally:
        MS2centralrunning=False
        #mungkin baris berikut akan error, gpp sdh boleh mengulagi proses dgn 1 baris diatas
        fasum__root_updatetotal(cr,uid, fasum)
        #fasum['ref'].write(cr,uid,fasum['root'],  {'finished': datetime.now()})    
        
    return msg_warning,msg_info


    
    

import wizard
import tools
import pooler
import time
import sys
import base64 

from osv import fields, osv
#from toolsrep.csvprocessing import read_csv2array


view_form_start = """<?xml version="1.0"?>
<form string="Import Planning from MS2 Server">
    <image name="gtk-dialog-info" colspan="1"/>
    <label align="0.0" string="Pilih Tanggal Planning yang akan diambil. Field yg kosong, akan diisi secara otomatis" colspan="3"/>
    <group colspan="4" col="2">
        <!--<field name="datatype"/>-->
        <field name="datafrom"/>
        <field name="datauntil"/>
        <field name="company_id" colspan="3"/>
        <field name="download_planning" />
        <field name="download_lo" />
        
        <!--<field name="override" colspan="3"/>-->        
    </group>
</form>"""
view_form_abort = '''<?xml version="1.0"?>
<form string="Import Planning from MS2 Server">
  <label string="Dibatalkan! Fungsi yang sama masih berjalan" colspan="4" />
</form>
'''

view_form_end = """<?xml version="1.0"?>
<form string="Import Data LO">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="2" col="4">
        <separator string="LO Import Done" colspan="4"/>
        <label align="0.0" string="Planning sudah dilakukan dengan sukses.\n Silahkan lihat hasilnya di tabel Pesanan." colspan="4"/>
    </group>
</form>"""

fields_form_finish = {
    #'via': {'selection':getcentrals, 'type':'selection','string':'Jalur import','required':True},
    #'datatype': {'string':'Kriteria', 'selection': [['1', 'Tanggal Pengiriman']], 'type':'selection'},
    'datafrom':  {'string':'Mulai', 'type':'date', 'required': True },
    'datauntil':  {'string':'Sampai dengan','type':'date'},
    'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},    
    'override': {'string': 'Replace bila sudah ada?', 'type': 'boolean', 'help': 'Bila sudah ada data di tabel ini untuk hari yang diminta, apakah akan di Replace?'},
    'download_lo' : {'string': 'Download LO bila tidak ditemukan?', 'type': 'boolean'},
    'download_planning' : {'string': 'Download Planning MS2?', 'type': 'boolean'},
}

def _data_load(self, cr, uid, data,ids={}):
    data['form']['company_id']=_default_company(self,cr,uid)
    data['form']['datafrom'] = str( datetime.today() ).split()[0]
    if True:
        data['form']['download_lo']=True #Live
        data['form']['download_planning']=True #LIVE
    else:
        data['form']['download_planning']=False #DEBUG
        data['form']['download_lo']=False #DEBUG
    return data['form']



### IMPORT PLANNING ###

_QUEST_FORM = UpdateableStr()

class wizard_import_planning_from_MS2( wizard.interface ):

    def _download_Planning_MS2( self, cr, uid, data, context ):
        view_info = ""
        view_warning = ""
        
        if data['form'] and not data['form']['datafrom']==False:            
            params = data['form']            
        else:
            params = {}
        params['form'] = data['form']
        
        msg_warning,msg_info = routineprocessgui( self, cr, uid, params, schedule = 'daily', tipeplanning = '0' )
        
        msg_info = msg_info.split('\n')
        for inf in msg_info:
            view_info += """<label align="0.0" string=" - %s" colspan="16"/>""" %(inf)
            
        msg_warning = msg_warning.split('\n')
        for msg in msg_warning:
            view_warning += """<label align="0.0" string=" - %s" colspan="16"/>""" %(msg)
        
        view_form_end1 = """<?xml version="1.0"?>
        <form string="Import Data Planning">
            <image name="gtk-dialog-info" colspan="16"/>
            <group colspan="16" col="16">
                <separator string="Import Planning..........................................................[ Done ]" colspan="16"/>
                <label align="0.0" string="Planning sudah dilakukan dengan sukses.\n Silahkan lihat hasilnya di tabel Pesanan." colspan="16"/>
                <separator string="Info" colspan="16"/>
                %s
                <separator string="Warning" colspan="16"/>
                %s
            </group>
        </form>""" % (view_info,view_warning)
        
        _QUEST_FORM. __init__(view_form_end1)
        
        return {} 
        
    def _check_process_running(self,cr,uid,data,context):        
        if MS2centralrunning:
            return 'abort'
        else:
            return 'started'

    states = {
        'init': {
            'actions': [],
            'result' : {'type': 'choice', 'next_state': _check_process_running }
        },
        'started':{
            'actions': [_data_load],
            'result': {'type': 'form', 'arch': view_form_start,
                'fields': fields_form_finish,
                'state': [
                    ( 'end', 'Cancel', 'gtk-cancel' ),
                    ( 'run', 'Ok', 'gtk-ok', True )
                ]
            }
        },

        'run':{
            'actions': [_download_Planning_MS2],
            'result': {'type': 'form', 'arch': _QUEST_FORM, 'fields': {},
                'state': [
                    ( 'end', 'Ok', 'gtk-ok', True )
                ]
            }
        },
        'abort':{
            'actions': [],
            'result': {'type': 'form', 'arch': view_form_abort, 'fields': {},
                'state': [
                    ( 'end', 'Ok', 'gtk-ok', True )
                ]
            }
        },
    }

wizard_import_planning_from_MS2( 'pn.import.planning2.MS2.sqlpure' )
