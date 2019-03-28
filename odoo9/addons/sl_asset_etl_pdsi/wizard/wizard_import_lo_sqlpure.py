'''
Created on Sep 13, 2014

@author: MPD
'''
import sys

#from runwinscp import genericftpcmd
from pn2.wizard import wizard_export_lo_plant
import csv, string
from pn2.wizard import parsingutil
from pn2.wizard import parsingutil2
from pn2.wizard import parsingutil3
import time
from datetime import datetime, timedelta
from pn2.initconfiguration import pn2_conf
from tools.translate import _
from tools import UpdateableStr, UpdateableDict

import os.path

from pn2.wizard.wizard_import_lo_centralmysap import __mysapSudsClient,__importMySapDoList,__prepareDateRange,__prepareTimeRange,__selectedDepot,__DO_HARVESTING
from pn2.wizard.wizard_import_lo_centralmysap import setProcessedData,getUnprocessedData,parseloarraymysap,writeLOmysap2doraw
from pn2.wizard.parsingutil3 import checkncreate,getThisCompanyData,_default_company
from connector.clientmanual.openerp_object_multi_caller import executefunctioninDepots

#if pn2_conf[section]['data_source'] !='mysap': 
#Jika data sumber bukan MySAP/SIOD_central, mungkin dari TAS
#data['process_log_ref'].write( {'process_log': "Getting data from %s" % pn2_conf[section]['data_source'] } )
from pn2 import pn_do_import_lo_tas_plumpang #.writeLOmysap2doraw(self, cr, 1,params,data)
from connector.clientmanual import remoteorm2
from pn2.initconfiguration import pn2_conf
import pooler
from osv import osv
import wizard
from .. import atemp_spbu

# ---------------------- PARSING TEMP DO  -------------------------
def siapkan_PNDO_untuk_sinkronisasi(cr,uid,fasum):
    # plan_siod.shipmentreq_id = shipreq.id
    # FILL ID
    # 1. fill PN_DO.name_int
    cr.execute('''SELECT count(*) FROM pn_do 
        where  
        name IS NOT NULL 
        and (name_int = 0 or name_int IS NULL)''')
    countNoNameInt = cr.fetchone()[0]
    if countNoNameInt:
        fs_prepareDo = fasum['ref'].create(cr,uid, {'name': 'Preparing DO for synch',
                                                  'parent_id': fasum['parsing'], 'inserted' : countNoNameInt, 
                                                  'started': datetime.now()})
        cr.execute('''UPDATE pn_do 
            SET name_int = cast(name AS bigint)
            WHERE 
                -- name != '' AND 
                name is not null 
                AND (name_int = 0 OR name_int IS NULL)''')
        cr.commit()
        fasum['ref'].write(cr,uid,[fs_prepareDo],
                                       {'finished': datetime.now()})
def tandai_TempDo__ygLinkKe_PnDo(cr):
    # 1. fill PN_DO.name_int
    # 2. 
    # we don't touch the shipment request here.
    cr.execute('''
        UPDATE atemp_pn_do d 
        SET 
            pn_do_id = A.id,
            -- shipment_request_id = A.shipment_request
            update_level = CASE WHEN update_level IS NULL THEN 1 ELSE update_level+1 END
        FROM 
        pn_do A
        WHERE d.name_int = A.name_int
        ''')
    cr.commit()        
def extract_SelectionField_from_AtempDO(cr, shortcut, value, domain):
    #cr.execute(
    sql = '''
    INSERT INTO pn_selection_field (shortcut,name, domain)
    SELECT %(shortcut)s, %(value)s, '%(domain)s' FROM
    (
        SELECT MV.%(shortcut)s,%(value)s,domain
        FROM
            (SELECT DISTINCT %(shortcut)s,%(value)s
            FROM atemp_pn_do) mv
        LEFT JOIN 
            (SELECT * FROM pn_selection_field 
            WHERE domain = '%(domain)s')
        sf ON sf.shortcut = mv.%(shortcut)s
        WHERE domain is null
    ) A
    ''' % locals() 
    cr.execute(sql) 
    cr.commit()

def fixup__shipto(cr):   
    cr.execute('''
        UPDATE atemp_pn_do SET ship_to = trim(ship_to)
        ''')
    cr.commit() 
def fixup__kl_do(cr):
    #khusus utk "kl", formatnya adalah: 40.0 , 35.79 dst
    cr.execute('''
        UPDATE atemp_pn_do SET kl_do = to_char(delivery_qty, 'FM999990.0999')
        ''')
    cr.commit()
    
def fixup__planned_gi_date(cr):

    cr.execute('''
        UPDATE atemp_pn_do 
        SET planned_gi_date_iso = to_date(planned_gi_date, 'DDMMYYYY')
        WHERE planned_gi_date IS NOT NULL 
        ''')
    #        -- SET planned_gi_date_iso = substring(planned_gi_date from 5 for 4) || '-' || substring(planned_gi_date from 3 for 2) || '-' || substring(planned_gi_date from 1 for 2)
    cr.commit()
def fixup__gitime(cr):
    #parse gi_date
#     cr.execute('''
#         UPDATE atemp_pn_do 
#         SET actual_gi_date_date = substring(actual_gi_date from 5 for 4) || '-' || substring(actual_gi_date from 3 for 2) || '-' || substring(actual_gi_date from 1 for 2)
#         WHERE actual_gi_date IS NOT NULL 
#         ''')
    #fill gi_time if empty
    cr.execute('''
        UPDATE atemp_pn_do 
        SET actual_gi_time = '000000'
        WHERE actual_gi_date IS NOT NULL AND actual_gi_time IS NULL
        ''')
    #parse gi_date
#     cr.execute('''
#         UPDATE atemp_pn_do 
#         SET actual_gi_time_time = substring(actual_gi_time from 1 for 2) || ':' || substring(actual_gi_time from 3 for 2) || ':' || substring(actual_gi_time from 5 for 2)
#         WHERE actual_gi_date IS NOT NULL 
#         ''')
    #fill combination     
    cr.execute('''
        UPDATE atemp_pn_do 
        SET gitime = to_timestamp(actual_gi_date || actual_gi_time, 'DDMMYYYYHH24MISS')
        WHERE actual_gi_date IS NOT NULL 
        ''')    
    
    cr.commit()
        
def fixup__date_terima(cr):
    cr.execute('''
        UPDATE atemp_pn_do 
                SET date_terima_iso = to_date(date_terima, 'DDMMYYYY')
        WHERE date_terima IS NOT NULL 
        ''')
    cr.commit()    
    
def count_TempSPBU__ygNOTlinkKe_PnSpbu(cr):
    cr.execute('''SELECT count(*) FROM atemp_pn_do 
        WHERE pn_spbu_id is null''')
    return cr.fetchone()[0]
    
def buat_Spbu_baru(cr,uid, fasum):
    #HAPUS TEMPORARY
    atemp_spbu.Clear_AtempSPBU(cr)
    #ISIKAN
    cr.execute('''
        INSERT INTO atemp_spbu (
            --pemilik, 
            name, shipto, plant, res_company_id
            )
        SELECT DISTINCT 
           --ship_name, 
           ship_to, ship_to, shipping_point, res_company_id
        FROM atemp_pn_do
        WHERE pn_spbu_id IS NULL
        ''')
    cr.commit()
        
    atemp_spbu.Create_SPBU(cr, uid, fasum)
    
        
def cantelin__shipto_keSPBU(cr):
    cr.execute('''
    UPDATE atemp_pn_do m SET pn_spbu_id = A.spbu_id
        FROM 
        (
        SELECT min(s.id) as spbu_id, sm.shipto 
            FROM pn_spbu s
        INNER JOIN pn_spbu_master sm on sm.id = s.pn_spbu_master_id
        where sm.active = true and sm.shipto != '' and shipto IS NOT NULL
        GROUP BY SM.shipto
        ) A
    WHERE m.ship_to = A.shipto
    ''')    
    cr.commit()
    
def cantelin__shippingPoint_keResCompany(cr):
    cr.execute('''
    UPDATE atemp_pn_do m SET res_company_id = A.id
        FROM 
        (
        SELECT MIN(id) as id, ref FROM res_company 
        GROUP BY ref
        ) A
    WHERE m.shipping_point = A.ref
    ''')    
    cr.commit()
    
def deactive_where(cr, where):
    cr.execute('''
        UPDATE atemp_pn_do SET active = false WHERE 
        ''' + where)
    cr.commit()

def bulkInsert_PnDO(cr,uid, mapping={}):
#     cr.execute('''
#         INSERT INTO pn_do (%s)
#         SELECT %s FROM atemp_pn_do A
#         WHERE A.pn_do_id IS NULL
#         ''' % (
#                ','.join(mapping.keys()),
#                ','.join(mapping.values()), 
#                )
#         )
    sql ='''
        INSERT INTO pn_do (create_uid, create_date, date_do, %s)
            SELECT %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s 
                FROM atemp_pn_do A
        WHERE A.pn_do_id IS NULL
        AND A.pn_spbu_id IS NOT NULL --bugfix of avoid error when there was any unknown spbu.
        AND A.active = true --bugfix 55000 KL, exclude sales_org & etc.
        ''' % (
               ','.join(mapping.keys()),
               uid,
               ','.join(mapping.values()), 
               )
    #print sql
    cr.execute(sql)
    cr.commit()
    
def fasum__DO_updatetotal(cr,uid, fasum):    
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
            FROM atemp_pn_do             
        ) B
     ''')
    val = cr.dictfetchone()    
    #fasum['ref'].write(cr,uid,[fasum['root']], val)
    val['finished'] = datetime.now()
    fasum['ref'].write(cr,uid,fasum['lo'], val)   
    
    #BERI TAHU YG GAGAL
    if val['failed'] > 0:
        cr.execute('''        
        SELECT delivery_number, ship_to        
        FROM atemp_pn_do 
        WHERE update_level = 0 OR update_level IS NULL
        ''')        
        res = cr.dictfetchall()
        values = {'parent_id' : fasum['lo'],'failed':1, 'downloaded':0, 'inserted':0,'found':0 }
        for r in res:
            values['name'] = "LO:%s, SHIPTO:%s" % (r['delivery_number'],r['ship_to'])
            fasum['ref'].create(cr,uid, values)      
# 
#     #BERI TAHU YG BARU
#     if val['failed'] > 0:
#         cr.execute('''        
#         SELECT no_spbu, ship_to        
#         FROM ms2view_pn_spbu 
#         WHERE update_level = 1 
#         ''')        
#         res = cr.dictfetchall()
#         values = {'parent_id' : fasum['spbu'],'failed':0, 'downloaded':0, 'inserted':1,'found':0 }
#         for r in res:
#             values['name'] = "SPBU:%s, SHIPTO:%s" % (r['no_spbu'],r['ship_to'])
#             fasum['ref'].create(cr,uid, values)           
#     fasum['ref'].write(cr,uid,fasum['spbu'],  {'finished': datetime.now(),})     
    
def AtempDO_PnDo_Map():
    return {
        'depot'      : 'res_company_id',
        'name'       : 'delivery_number' ,
        'name_int'   : 'name_int',
        'produk_id'  : 'material_code',
        'kl_do'      : 'kl_do',
        'kl_do_float': 'delivery_qty',
        
        #spbu specific           
        'no_spbu'    : 'pn_spbu_id',
        'sonumber'   : 'sonumber',
        'sales_org'  : 'sales_org',
        
        #closing
        'gistatus'   : 'gi_status',           
        #'gi_status_desc'     : 'gi_status_desc',
        'mysapshipmentnum'   : 'shipment_number',
        
        #date
        'planned_gi_date'    : 'planned_gi_date_iso', #mysap
        #'date_shipment_plan' : 'planned_gi_date_iso', #mungkin ms2?
        'gitime'     :'gitime',
        
        #---SIOD SPECIFIC
        'active'     : 'active',
        'state'      : "'0'",
        #'shift_shipment',='0'
        'data_source': 'data_source',
        'date_terima': 'date_terima_iso',
        'date_terima' : 'date_terima_iso',
        'planned_gi_date' : 'planned_gi_date_iso',                                                                                                            
        'sonumber' : 'driver_number',
        'sales_org' : 'sales_org',
    }     
def parseUnprocessedLo(self,cr,uid, fasum):#,reconstruct, data):
    #check if this user (UID) is allowed to write to pn_do table
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'write') ##write baru limited only
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'create') #create baru limited only

    fs_parsing = fasum['ref'].create(cr,uid, {'name': 'Parsing',
                                                  'parent_id': fasum['lo'], 
                                                  'started': datetime.now()})
    fasum['parsing'] = fs_parsing
    
    try:
        #TODO: date_expected di isi tanggal dari temptable
        siapkan_PNDO_untuk_sinkronisasi(cr, uid, fasum)
        tandai_TempDo__ygLinkKe_PnDo(cr)
            
        #jangan langsung inject float karena hasilnya akan 40, 36 dst
        fixup__kl_do(cr)
        extract_SelectionField_from_AtempDO(cr, 'kl_do','kl_do as kl_do2', 'kl')
        
        extract_SelectionField_from_AtempDO(cr, 'material_code','material_name', 'produk')
        deactive_where(cr, 'delivery_qty = 0')
        deactive_where(cr, "sales_org Not IN %s " % (pn2_conf['MachineSpesific']['depot_sales_org_in_list_sql'],) )
        
        #TODO: ISIKAN  shift_shipment request,date_shipment_plan,#gitime=sudah
        fixup__planned_gi_date(cr)
        fixup__gitime(cr)
        fixup__date_terima(cr)
        
        cantelin__shippingPoint_keResCompany(cr)
        fixup__shipto(cr)    
        cantelin__shipto_keSPBU(cr)
        #TODO done: BUAT SPBU-MASTER, GABUNGKAN DGN DATA DARI MS2 KRN MS2 LEBIH LENGKAP DARI MYSAP
        if count_TempSPBU__ygNOTlinkKe_PnSpbu(cr) > 0:
            buat_Spbu_baru(cr,uid, fasum)
            cantelin__shipto_keSPBU(cr)
            pass
        #Okay, everything is ready for now.
        #we have two options to inject PN.DO:
        # 1. using ORM, one by one <<--- very slow since PN.DO is also being used by pn2.reports
        # 2. using SQL, bulk all once. <<--- be careful about the result
        
        
        #--- SQL INJECTION
        #2.1 update available LO. 
        #TODO: is it^ needed? = apakah boleh diupdate LO yg sudah ada?
        #mapping 
        fields_mapping = AtempDO_PnDo_Map()
        bulkInsert_PnDO(cr, uid, fields_mapping)
        
    finally:
        tandai_TempDo__ygLinkKe_PnDo(cr)
        
        fasum['ref'].write(cr,uid,[fs_parsing],
                                       {'finished': datetime.now()})
    
#     #data['process_log_ref'].write( {'process_log': "Now get all unProcessed data from pn_do_raw" } )
# 
#     #print "Now get all unProcessed data from pn_do_raw"
#     unprocessed=False; ids_success=False
#     params={'SemuaOrTerbaru':2}
#     if data.has_key('SemuaOrTerbaru'): #ini utk filtering pengambilan data LO dari pn_do_raw_mysap
#         params={'SemuaOrTerbaru':1}
#         del data['SemuaOrTerbaru']
#     unprocessed = getUnprocessedData(self, cr,uid,'pn_do_raw_mysap',params )
#     
#     #data['process_log_ref'].write( {'process_log': "Retrieved: %s record" % len(unprocessed) } )
#     
#     reader=[]
#     if unprocessed:
#         #data['process_log_ref'].write( {'process_log': "Parsing the unProcessed data to pn_do" } )
#         #print "Parsing the unProcessed data to pn_do"
#         ids_success, reader=parseloarraymysap(self, cr, uid, unprocessed,False,2,reconstruct=reconstruct )     #write new Lo into database
# 
#     #print "Note the successfully PARSED data in pn_do_raw"
#     #data['process_log_ref'].write( {'process_log': "Note the successfully PARSED data in pn_do_raw" } )
#     setProcessedData(self, cr, 1,ids_success, reader) #Note successfully processsed data
    return True


# ---------------------- NON GUI WIZARD -------------------------
LOcentralrunning = False
model_name = 'pn.do' 
# ===============================x2nie
def clean_AtempDO(cr):
    cr.execute('DELETE FROM atemp_pn_do')
    cr.commit()
# copied again from addons.pn2.wizard.wizard_import_lo_centralmysap
def Dump_LOmysap_toAtempDO_okejuga(self,  cr, uid, reader,tanggal_terimalo=False,source_mysap=True):
## copied from def parseloarrayms2(self,  cr, uid, reader):

    #TASK SPECIFIC
    # read the rest of the file
    pn_do_raw_ref=pooler.get_pool(cr.dbname).get("atemp.pn.do")
    mysapLOfields = [ 'Depot' , 'Ship_to' , 'Ship_name' , 'Delivery_Number' , 'Shipment_Number' ,
        'Transporter' , 'Vehicle_Number' , 'Driver_Number' , 'Delivery_Qty' , 'UOM' ,
        'Planned_GI_Date' , 'GI_Status' , 'GI_Status_Desc' , 'Actual_GI_Date' , 'Actual_GI_Time' ,
        'Shipping_point' , 'Material_code' , 'Material_name' , 'Sales_org' , 'Distribution_Channel' ]
    
    atempDO_fields = ', '.join([k.lower() for k in mysapLOfields])
    mysap_fields = ', '.join(['%%(%s)s' % k for k in mysapLOfields])
    SQL ='''
        INSERT INTO atemp_pn_do (data_source, name, name_int, %s)
            VALUES ('mysap',  %%(Delivery_Number)s,  %%(name_int)s, %s)
        ''' %  (atempDO_fields, mysap_fields,) 
           
        
    def PutAtempDO(row):
        my = []
        res = []
        #print "DATA IS::::",
        for k in mysapLOfields:
            if row[k]:
                my.append(k.lower())
                s = str(row[k]).strip()
                res.append(s)
                #if len(s) > 20:
                #    print k,':', `s`,
            pass
        #print ''
        n = str(row['Delivery_Number']).strip()
        my  += ['name','name_int','data_source']        
        res += [n, int(n),'mysap']
        
        cols = ', '.join(my)
        vals = ', '.join(["%s"] * len(my)) 
        sql = '''
        INSERT INTO atemp_pn_do (%s)
            VALUES (%s)
        ''' %  (cols, vals,)
         
        #row['name_int'] = int(row['Delivery_Number'])
        #print "sql=",sql
        #print "row=",res
        #cr.execute(sql,row)
        cr.execute(sql,res)
    
    total=0; written=0
    for row in reader:
        total+=1
        try:
            if (not row):
                continue

            #convert strange row types , to "data" of type dictionary
#             data={'exported':False,'data_source':'mysap' }
#             for field in mysapLOfields:
#                 try:
#                     data[field] = row[field]
#                 except: pass            
            PutAtempDO(row)
            #PutAtempDO(data)
            
            
#             continue
#         
#             #convert strange row types , to "data" of type dictionary
#             if source_mysap:
#                 data={'exported':False,'data_source':'mysap' }
#                 for field in mysapLOfields:
#                     try:
#                         data[field.lower()] = row[field]
#                     except: pass
#                 data['name']=data['delivery_number']
#                 data['name_int']=int(data['delivery_number'])
#                 if not (tanggal_terimalo==False):
#                     data['date_terima']=tanggal_terimalo
#                 #else:
#                     #data['date_terima']= data['planned_gi_date']
#             else:#if source_mysap = from other siod servers, then no need conversion
#                 data=row
#                 data['data_source']='other'
# 
#             data['active']='true'
#             #success,log=parsingutil3.checkncreate( cr, uid,[( 'name', '=', data['delivery_number'] ),('active', 'in', ['false','true'])] ,data,pn_do_raw_ref,alwaysupdate=True,reconstruct=True)
#             pn_do_raw_ref.create(cr, uid, data)
#                 if (success!=0):
#                     written+=1
#                     print 'pn_do_raw = '+ str(success)
        except Exception, e:
            print "insert lo error:", str(e)
            pass
        #break
    cr.commit()
    #print 'Total='+str(total)+" || Written="+str(written)

    return total,written

def Dump_LOmysap_toAtempDO(self,  cr, uid, reader,tanggal_terimalo=False,source_mysap=True):
## copied from def parseloarrayms2(self,  cr, uid, reader):

        #TASK SPECIFIC
        # read the rest of the file
        pn_do_raw_ref=pooler.get_pool(cr.dbname).get("atemp.pn.do")
        mysapLOfields = [ 'Depot' , 'Ship_to' , 'Ship_name' , 'Delivery_Number' , 'Shipment_Number' ,
            'Transporter' , 'Vehicle_Number' , 'Driver_Number' , 'Delivery_Qty' , 'UOM' ,
            'Planned_GI_Date' , 'GI_Status' , 'GI_Status_Desc' , 'Actual_GI_Date' , 'Actual_GI_Time' ,
            'Shipping_point' , 'Material_code' , 'Material_name' , 'Sales_org' , 'Distribution_Channel' ]

        total=0; written=0
        for row in reader:
            total+=1
            try:
                if (not row):
                    continue

                #convert strange row types , to "data" of type dictionary
                if source_mysap:
                    data={'exported':False,'data_source':'mysap' }
                    for field in mysapLOfields:
                        try:
                            data[field.lower()] = row[field]
                        except: pass
                    data['name']=data['delivery_number']
                    data['name_int']=int(data['delivery_number'])
                    if not (tanggal_terimalo==False):
                        data['date_terima']=tanggal_terimalo
                    #else:
                        #data['date_terima']= data['planned_gi_date']
                else:#if source_mysap = from other siod servers, then no need conversion
                    data=row
                    data['data_source']='other'

                data['active']='true'
                #success,log=parsingutil3.checkncreate( cr, uid,[( 'name', '=', data['delivery_number'] ),('active', 'in', ['false','true'])] ,data,pn_do_raw_ref,alwaysupdate=True,reconstruct=True)
                pn_do_raw_ref.create(cr, uid, data)
#                 if (success!=0):
#                     written+=1
#                     print 'pn_do_raw = '+ str(success)
            except:
                pass
        cr.commit()
        #print 'Total='+str(total)+" || Written="+str(written)

        return total,written
        
# def __selectedCompany(p,section,data,cr,params={}):
#     "provide list of depot tobe imported from MySAP"
#     DepotList=[]
#     #    params['depot']
# #    params['datatype']
#     if params.has_key('depot') and params['depot']!=False and params['depot']!='CENTRAL':
#         depots = params['depot']
#         DepotList=depots.split(',')
#     #elif p.get(section,'shipping_point')!='':
#     elif pn2_conf[section]['shipping_point'] !='' :
# 
#         depots= pn2_conf[section]['shipping_point'] #p.get(section,'shipping_point')
#         DepotList=depots.split(',')
#     else:
#         cr.execute("SELECT ref FROM res_company ")
#         cr.commit()
#         depots=cr.fetchall()
#         #DepotList = [depot[0] for depot in depots if depot[0]!=None] #listing daftar depot yg depot!=None
#         DepotList=[]
#         for depot in depots:
#             if depot[0]!=None: DepotList.append(depot[0])
#     return DepotList
    
def __DUMP_HARVESTING(self, cr, uid,data):
    "Fungsi ini akan mendownload LO dary MySAP dan menuliskan ke temporary serta ke DO"
    #print "\n",data,"\n Getting DATA (%s->%s)" % (depot,loStatus),aDay
    data['mode'] = pn2_conf['MySAPLO']['mysap_mode']
    master = 'harvesting MYSAP:%(mode)s: %(shipping_point)s:%(status)s  %(date_From)s %(time_From)s ~ %(date_To)s %(time_to)s '
    if data.has_key('shipto'):
        master +=  " %(shipto)s"
    elif data.has_key('nomorlo'):
        master +=  " %(nomorlo)s"

    #data['process_log_ref'].write( {'process_log': master % data} )
    #print master % data

    #print
    #print "REPLIED:",reply
    imported_summary=''
    LOcurrentlastWritten=''
    msg = ''
    oke_msg = ''
    total = 0
    NO_DATA_FOUND  = "No data found" #mysap: `Text: No data found    `
    
    process_log = ""

    for i in range(1,8): #[1,2,3]        KALO GAK ADA RESPONSE, ULANG2 3x!

        reply=False
        failed=0
        mysap_response = ""
        try:
            reply = __importMySapDoList(data,cr.sudsclient)               #get available real MySAP/LO from pertamina. #output must always be available and correct
            if reply:
                try:
                    mysap_response = str(reply['Message'][0]['Desc_Msg']).strip()
                    if reply['Details']: #success
                        tgl_terimalo=data['date_To']
                        imported_summary+='\n%s(%s):%d' % (data['shipping_point'],data['status'],len(reply['Details']))
                        #process_log = "GOT %d data, owned for (%s->%s)" % (len(reply['Details']),data['shipping_point'],data['status']),str(data['aDay'])
                        process_log = 'Tgl %s ada %s data (%s) untuk (%s)' %( str(data['aDay']) , len(reply['Details']), data['status'], data['shipping_point'],)
                        #            F306 | 2014-09-12 => 1921 data (A)
                        #process_log = '%s %s = %s (%s) data' %( str(data['aDay']) , len(reply['Details']), data['status'], data['shipping_point'],)
                        oke_msg = process_log # 'GOT %d data, owned by (%s)' % (len(reply['Details']),data['shipping_point'],)
                        msg = str(process_log)
                        #Write to pn_do_raw_mysap
                        print msg, 
                        total,written=Dump_LOmysap_toAtempDO(self, cr, uid, reply['Details'],tgl_terimalo)
                        #process_log='Total='+str(total)+" ; Written="+str(written)
                        mysap_response = str(reply['Message'][0]['Desc_Msg']).strip() #we expect string, not text,but suds report as text.
                        process_log = mysap_response
                        print process_log
                        #msg = 'Total='+str(total)+" ; Written="+str(written)
                except: #could be considered success in connecting to MySAP too, only data might not be retrievable
                    #print reply[0]['Desc_Msg']
                    failed=4
                    mysap_response = str(reply['Message'][0]['Desc_Msg']).strip() #we expect string, not text,but suds report as text.
                    process_log = mysap_response
                    msg = 'Error'
            else:
                failed=2
                process_log="mySAP didn't response % errorcode=%s" % failed
                msg = 'Error'

        except:
            process_log= "no reply from MySAP on trial = %s " % i
            failed=3
            msg = 'Error'

        #data['process_log_ref'].write( {'process_log': process_log} )

        if not failed:
            break
        
        #don't ask again when the answer was data not found!
        if mysap_response == NO_DATA_FOUND:
            break
    #if failed:
    fail_cause={3:"Tidak ada koneksi ke MySAP. Yakinkan bahwa server ini terhubung/berada di jaringan Intranet Pertamina dan login credential nya benar", 
                    2: 'MySAP tidak merespon (%sx). Coba beberapa saat lagi' % i, 
                    1: 'MySAP menolak koneksi. Coba beberapa saat lagi',
                    0: oke_msg,
                    4:'LO tidak ditemukan di mySAP'}
    #data['process_log_ref'].write( {'process_log': fail_cause[ str(failed) ] } )
    #msg = 'Tgl '+str(data['aDay'])+', Status ('+data['status']+'), '+fail_cause[ failed ]
    msg = fail_cause[ failed ]
    #raise osv.except_osv(_('Error !'), _(fail_cause[ str(failed)] ))
    #print imported_summary,msg,failed
    #return imported_summary,msg,failed
    return total,msg,failed, mysap_response

def DownloadLO_ByLONumber_FromMySAP(self, cr, uid,params={},fasum={},scenario=1,callsource=1,reconstruct=False,SpbuType=False,loparse=True,spbu = False):
    #Fungsi utk Penarikan data LO yg terdaftar di params['nomorlo']
    #Sumber data bisa dari MySAP atau dari SIOD_central
    
    model_name = 'pn.do'
    
    #check if this user (UID) is allowed to write to pn_do table
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'write') ##write baru limited only
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'create') #create baru limited only
    
    clean_AtempDO(cr)
    
    #reconstruct = (True) Rekonstruksi master data yang tidak ada (False): No Reconstruction
    data_msg = ''
    data={}; process_log=''
    #data['process_log_ref'] = process_log_wrapper( self,cr,uid)    
    
    params['status']='A,C'
    
    data['shipping_point']= parsingutil3.getThisCompanyData(self,cr,uid,context={})[0]['ref']    
    data['date_From']='01012001'
    data['date_To']=False
    data['time_From']='000000'
    data['time_to']='235959'    
    
    data['aDay']=''        

    if reconstruct not in (1,0):
        if string.upper(reconstruct) == 'TRUE': reconstruct = True
        else : reconstruct = False
    
    #cr.sudsclient=__mysapSudsClient()  
    from connector.mysap_suds import MySAP_SUDS
    cr.sudsclient=MySAP_SUDS('mi_osgetListDO').client 
    
    allsuccess=False
    for nolo in params['nomorlo']:
        data['nomorlo'] = nolo
        msg_1lo=''    
        lo_found=0; lo_fail=0        
        for status in params['status'].split(','):            
            data['status']=status
            total,data_msg,failed, mysapResponse = __DUMP_HARVESTING(self, cr, uid,data)
            
            if failed:
                if failed < 4:      #tidak terhubung ke mysap:
                    raise osv.except_osv(_('Error !'), data_msg)
                      
                if failed == 4:   #2= 'MySAP tidak merespon (%sx). Coba beberapa saat lagi' % i,
                    msg_1lo += 'Tgl '+str(data['aDay'])+', Status ('+data['status']+'), '+data_msg +'\n'   #akumulasi akhir msg dari status A+C
                    data_msg = msg_1lo          #jika dua2nya gagal, keluarkan message
                    
            else: # 0                # ada data
                break            
            
        process_log += data_msg
        if failed:
                  
            if failed==4:
                #process_log += 'LO %s tidak ditemukan || ' % nolo
                
                #Non activekan LO tersebut di pn_do
                #TODO:                
                #cr.execute("UPDATE pn_do SET active=false WHERE name='%s' and gistatus='%s';" % (nolo,status) )
                #cr.commit()
                pass
        else:
            lo_found+=1
            #TODO:
            #cr.execute("UPDATE pn_do SET active=true WHERE reasoninactive is null and name='%s';" % (nolo) )
            #cr.commit()
            #process_log  += 'LO %s Sudah Di Upadate Dari MySAP || ' % nolo            
            allsuccess=True
            
        print data_msg
    
    #data['process_log_ref'].write( {'process_log': process_log } )
    data_msg = process_log

    if loparse!=False:# and allsuccess:
        parseUnprocessedLo(self,cr,uid, fasum)#,reconstruct, data)
    if not allsuccess:
        return False,data_msg
        #raise osv.except_osv(_('Error !'), _( 'Ada LO yang tidak ditemukan !' ))
    
    return True,data_msg

def __prepareTimeRange(aDay,data):
    #if ind==1:
    if aDay==data['arrDate'][0]:
        data['time_From']=data['time_start']
        if len(data['arrDate']) > 1: #there is more days?, else: keep settin to this today().time above
            data['time_to']='235959'
    #elif ind==len(arrDate):
    elif aDay==data['arrDate'][-1]:
        data['time_From']='000000'
        data['time_to']=data['time_end']
    else:
        data['time_From']='000000'
        data['time_to']='235959'
    datearr=str(aDay).split('-')
    mydate= datearr[2]+datearr[1]+datearr[0] #set to format ddmmyyyy
    data['date_From']=data['date_To']=mydate
    #return data

def Dump_BulkLO_FromMySAP(self, cr, uid,data,params,spbulist=[]):
    
    LOcurrentlastWritten=''        
    data_msg = ''
    msg = ''
    if params.has_key('status'):
        statusstring  = params['status']
    else:
        statusstring  = pn2_conf['MySAPLO']['status'] 
    statusList = statusstring.split(',')
    
    kodedepot = str( pn2_conf['MachineSpesific']['kodedepot']  ).upper()
    company_ref = pooler.get_pool( cr.dbname ).get( 'res.company' )
    rcompanies = company_ref.read(cr, uid, params['company_id'],['ref'])
    if rcompanies:
        kodedepot = rcompanies['ref']
    depotList = [kodedepot]
# data =
#     {
#     'arrDate': [datetime.date(2014, 9, 23)],
#     'date_From': '23092014',
#     'date_To': '23092014',
#     'date_end': '2014-09-23',
#     'date_start': '2014-09-23',
#     'time_From': '000001',
#     'time_end': '162300',
#     'time_start': '000001',
#     'time_to': '162300'
#     }    
    fasum = params['fasum']
    
    
    fd = 'Import LO MySAP '+ data['date_start'] 
    if data['date_start'] != data['date_end']:
        fd += ' - ' + data['date_end']
    fasum['ref'].write(cr, uid, fasum['lo'], {'name':fd})
    
    #cr.sudsclient=__mysapSudsClient() 
    from connector.mysap_suds import MySAP_SUDS
    cr.sudsclient=MySAP_SUDS('mi_osgetListDO').client 
    
    totalsummary=0; imported_summary=''
    for aDay in data['arrDate']:                        #--- PER DAY. bila date_to != date_from mk iterasi utk setiap harinya                
        data['aDay']=aDay
        __prepareTimeRange(aDay,data)            #set time_from & time_to  for each day
                    
        for depot in depotList:                                     #PER DEPOT if not int(depot['active']): continue        
            data['shipping_point']=depot
            
            for loStatus in statusList:                             #--- PER LO STATUS
                data['status']= loStatus
                
                #print "----------------- CATEGORY:", plan
                fs_cat = fasum['ref'].create(cr,uid, {'name': '%s %s [%s]' % (depot, aDay,loStatus,),
                                                  'parent_id': fasum['lo'], 
                                                  'started': datetime.now()})
                mysapResponse = ''
                try:
                    if spbulist==[]:                    
                        #tarik LO dari MySAP dan tuliskan ke lokal database pn_do
                        #if __DO_HARVESTING(self, cr, uid,data):
                        total,msg,failed,mysapResponse = __DUMP_HARVESTING(self, cr, uid,data)
                        if msg != "Error":
                            data_msg += '\n' + msg  
                            totalsummary+=1
    
                    else:
                        for spbu in spbulist: #get LO for each spbu
                            data['shipping_point']=spbu[0]
                            data['shipto']=spbu[1]
    
                            total, msg,failed,mysapResponse = __DUMP_HARVESTING(self, cr, uid,data)
                            if msg != "Error":
                                data_msg += '\n' + msg  
                                totalsummary+=1
                            #del data['shipto']
                    
                finally:
                    fasum['ref'].write(cr,uid,[fs_cat],
                                   {'finished': datetime.now(),
                                    'downloaded':total,
                                    'note': mysapResponse})
                
    return totalsummary,data_msg


def routineprocess_parametrized(self, cr, uid,params={},scenario=1,callsource=1,reconstruct=False,SpbuType=False,loparse=True,spbu = False):
    #Fungsi utk Penarikan data sekumpulan LO yg sesuai dgn kriteria tertentu
    #Sumber data bisa dari MySAP atau dari SIOD_central
    #callsource= (1) This routine is called internally (2)Called from Planning MS2
    #scenario = (1) Get new LO data from mySAP (Other than 1): only Reimport from LO master raw (2)Only get LO to raw without parsing to LO master
    #reconstruct = (True) Rekonstruksi master data yang tidak ada (False): No Reconstruction
    #spbulist=[]: if this is given, then the LO will be taken from mySAP per SPBU based on shipto number
    
    
    
    #check if this user (UID) is allowed to write to pn_do table
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'write') ##write baru limited only
    pooler.get_pool(cr.dbname).get('ir.model.access').check(cr, uid, model_name, 'create') #create baru limited only
      
    global LOcentralrunning
    data_msg="Import LO tampaknya tidak sukses"
    
    #from datetime import datetime, timedelta
    
#    def loggingscript(msg):
#        #write to scriptlogrun tabel
#        if msg!='': 
#            LOcentralrunning=False 
#            raise osv.except_osv( _( 'Error !' ), _( msg ) )
#        
#        return True
    
    #cleaning params
    for key in params.keys():
        if params[key]==False: 
            del params[key]
    
    
    
    #process_log=''
    #data['process_log_ref'] = process_log_wrapper( self,cr,uid)
    
    if LOcentralrunning:
        data_msg="Dibatalkan! Fungsi yang sama masih berjalan"
        #data['process_log_ref'].write( {'process_log': data_msg } )
        print data_msg
        return '',data_msg
    
    #---------------------------------------- START
    LOcentralrunning=True
    
    spbulist = []; 
    data={}
    
    fs = pooler.get_pool( cr.dbname ).get( 'fast.summary' )
    fd = 'Import LO MySAP '
    fasum = {
     'ref'  : fs,
     'lo' : fs.create(cr, uid,{'name':fd, 'started': datetime.now()}),
     #'company_id' : company_id,
    } 
    params['fasum'] = fasum
    
    
    
    try: 
        clean_AtempDO(cr)
        if getThisCompanyData(self,cr,uid)[0]['ref']=='CENTRAL':
            #data['process_log_ref'].write( {'process_log': "Function running from CENTRAL" } )
            params['depotonly']=False
            data_msg = executefunctioninDepots(cr, uid, 'pn.do','getLOfromMySAP',params)['error']
            LOcentralrunning=False
            return '',data_msg
    
            
    
            
        shipping_point = parsingutil3.getThisCompanyData(self,cr,uid,context={})[0]['ref']
        
        if params.has_key('spbu') and params['spbu']:
            spbulist_sql, spbulist_list= parsingutil3.findAllSpbuRecordWithTheSameNumber(self,cr, 1,params['spbu'],'shipto')
    
            for spbu in spbulist_list:
                spbulist.append( (shipping_point,spbu) )
        elif SpbuType != False:        
            cr.execute("select c.ref,b.shipto from pn_spbu_master b inner join res_company c on c.id=b.company_id where b.type='%s' order by c.ref" % SpbuType)
            #cr.commit()
            spbulist = cr.fetchall()
        else: pass
    
        if reconstruct not in (1,0):
            if string.upper(reconstruct) == 'TRUE': reconstruct = True
            else : reconstruct = False
    
#         "Get LO from MySAP, and then send to depots"
#         thisScriptPath=os.path.split(__file__)[0]+'\\'
#         configfile='ms2connection.conf'
#         logfilePath=thisScriptPath+"..\\"; logfile = 'pn2_log.conf'
#         p=parsingutil.configparserload(logfilePath,logfile)    
        
        section='MySAPLO'
        totalsummary=0; imported_summary=''
        if scenario==1: #Get New LO data from MySAP        
            data,lasttime = __prepareDateRange(pn2_conf,section,data,params)          #Get & fixup datetime range
            __minDate=data['date_From']                                 #save. because next loop will replace it value
            print data['date_From']
            __maxDate=data['date_To']    
            print data['date_To']        
            
            if pn2_conf[section]['data_source'] !='mysap': #Jika data sumber bukan MySAP/SIOD_central, mungkin dari TAS
                #data['process_log_ref'].write( {'process_log': "Getting data from %s" % pn2_conf[section]['data_source'] } )
                pn_do_import_lo_tas_plumpang.writeLOmysap2doraw(self, cr, 1,params,data)
            else:
                #depotList = __selectedDepot(pn2_conf,section,data,cr,params)              #Get data depot yg terdaftar
                
                success =False
                #Coba tarik LO dari SIOD_central dulu. Hasilnya taruh di tabel pn_do_raw_mysap
                if (pn2_conf['MachineSpesific']['kodedepot']).upper()!='CENTRAL' and pn2_conf['MySAPLO']['getcentrallo']=='1': 
                    #data['process_log_ref'].write( {'process_log': "Try to get data from SIOD Central by synchronizing table pn_lo_raw of this database with SIOD central" } )
                    success = syncLocalTableWithThatInRemoteServer(self,cr, uid,params, depotList,data)
               
                if not success: 
                    #data['process_log_ref'].write( {'process_log': "This site is not configured for getting data from SIOD-Central. Try to get data directly from MySAP" } )
                    success,data_msg =Dump_BulkLO_FromMySAP(self, cr, 1,data,params,spbulist)
                
                if not success :  #If data never imported within this session? 
                                                                            #only erro while real no data retrieve from whole DEPOTs
                                                                            #all STATUSes configurated
                    if callsource==1: #GILA NIH, APAAN?
                        LOcentralrunning=False
                        raise osv.except_osv(_('Error !'), _("Data baru dari belum tersedia. Silahkan kira-kira beberapa saat lagi." )) #% reply['Message']['Desc_Msg']
                    else:
                        LOcentralrunning=False 
                        return 0
                else:
                    pass
                    
                    #write lastrecord yg ditulis ke LastWrittenCurrent.conf
            #            section='LastWritten'
            #            #lolastwritten=float('0'+p.get(section,'lolastwritten'))
            #            lolastwritten=p.get(section,'lolastwritten')
            #            #write lastrecord yg ditulis ke LastWrittenCurrent.conf
                    
            ##            if LOcurrentlastWritten>lolastwritten:
            ##                parsingutil.setConfigValue(p,section,{'lolastwritten':str(LOcurrentlastWritten)},thisScriptPath+configfile)
            ##                
                    # dogol
#                     section='MySAPLO'
#                     if (not params.has_key('datauntil'))  or params['datauntil']==False:
#                         parsingutil.setConfigValue(p,section,{'datetime_lastwritten':lasttime.strftime('%Y-%m-%d %H:%M:%S'), 
#                                                               'date_lastwritten':data['date_To'], 
#                                                               'time_lastwritten' : data['time_to'],  
#                                                               },logfilePath+logfile)
#         
        #Ambil data dari pn_do_raw_mysap, lalu parsing (link dgn master data spt pn_spbu dll). 
        #Dan hasilnya masukkan ke pn_do
        if loparse!=False:            
            parseUnprocessedLo(self,cr,uid, fasum)#,reconstruct, data)
            
            
    except Exception, e:
        #logger.error('Failed to upload to ftp: '+ str(e))
        #print "Unexpected error:", sys.exc_info()[0]
        print "Unexpected error:", str(e)
#     except:
#         pass #unhandled exception
    finally:
        LOcentralrunning=False
        fasum__DO_updatetotal(cr,uid, fasum)
    #if Done: Open Lock Process
    
    return imported_summary,data_msg

# ---------------------- WIZARD GUI -------------------------
fields_form_start={
    #'via': {'selection':getcentrals, 'type':'selection','string':'Jalur import','required':True},
    #'datatype': {'string':'Kriteria','selection': [['1','Tanggal Pengiriman']], 'type':'selection'},
    'reconstruct': {'string':'Rekonstruksi','selection': [['True','Ya'],['False','Tidak']], 'type':'selection','help':'Kosongkan saja bila anda tidak benar2 mengerti fungsi kolom ini'},
    'datafrom':  {'string':'Mulai ', 'type':'datetime','help':'Bila kolom ini kosong, maka system akan memasukkan waktu terakhir penarikan sebelumnya','required': True},
    'datauntil':  {'string':'Sampai dengan', 'type':'datetime', 'help':'Bila kolom ini kosong, maka waktu saat ini akan dimasukkan oleh system'},
    
    #'depot':  {'string':'Kode Depot', 'size':'7', 'type':'char', 'help':'Bila kolom ini kosong, maka otomatis LO depot ini yang ditarik'},
    'company_id': {'string': 'Depot', 'type': 'many2one', 'relation': 'res.company', 'required': True},
    
    'spbu': {'string':'Kode spbu', 'type':'many2one','relation':'pn.spbu','help':'Bila kolom ini kosong, maka otomatis LO seluruh SPBU depot ini akan ditarik'},
    'nomorlo': {'string':'Nomor LO','size':'20','type':'char', 'help':'Bila kolom ini diisi, kolom yang lain akan diabaikan'}
    #'spbu':  {'string':'Kode spbu', 'type':'many2one','relation':'pn.spbu'},
    #,'export': {'string':'Export ke Depot2 (klik kalau ini SIOD Central)', 'type':'boolean'}
    #No way! dont do that. 
}
import copy
fields_form_start_spbu=copy.deepcopy(fields_form_start)
fields_form_start_spbu['spbu']= {'string':'Kode spbu', 'type':'many2one','relation':'pn.spbu','required':True}


_QUEST_FORM = UpdateableStr()

def _data_load1(self, cr, uid, data,ids={}):
    #data['form']['datafrom']=time.strftime('%Y-%m-%d'
    data['form']['datafrom'] = str( datetime.today() ).split()[0] + ' 00:00:00'
    #data['form']['datauntil']=time.strftime('%Y-%m-%d')
    #data['form']['depot']=str(pn2_conf['MachineSpesific']['kodedepot']).upper()
    data['form']['company_id']=_default_company(self,cr,uid)
    #    data['form']['datatype']='0'
    #data['form']['nomorlo'] = '8052314434'
    return data['form']

view_form_start="""<?xml version="1.0"?>
<form string="Import Data LO %s">
    <image name="gtk-dialog-info" colspan="1"/>
    <label align="0.0" string="Pilih LO yang akan diambil. Field yg kosong, akan diisi secara otomatis" colspan="3"/>
    <group colspan="4" col="2">
        <field name="datafrom" />
        <field name="datauntil" />
        <field name="company_id" />        
        <!-- field name="depot" / -->
        <field name="spbu" />        
        <field name="nomorlo" />        
    </group>
</form>"""

view_form_startspbu="""<?xml version="1.0"?>
<form string="Import Data LO %s (fast)">
    <image name="gtk-dialog-info" colspan="1"/>
    <label align="0.0" string="Pilih LO yang akan diambil. Field yg kosong, akan diisi secara otomatis" colspan="3"/>
    <group colspan="4" col="2">
        <field name="datafrom" />
        <field name="datauntil" />
        <field name="depot" />        
        <field name="spbu" />        
    </group>
</form>"""

view_form_end = """<?xml version="1.0"?>
<form string="Import Data LO">
    <image name="gtk-dialog-info" colspan="2"/>
    <group colspan="4" col="4">
        <separator string="LO Import Done" colspan="4"/>
        <label align="0.0" string="LO sudah di import dari MySAP dengan sukses.\n Silahkan lihat hasilnya di menu LO Master." colspan="4"/>
    </group>
</form>"""

#import datetime,mx.DateTime

### IMPORT SHIPMENT CENTRAL ###
view_form_start_reimport="""<?xml version="1.0"?>
<form string="Reimport LO Master Raw to LO Master">
    <image name="gtk-dialog-info" colspan="1"/>
    <label align="0.0" string="Pilih LO yang akan diambil. Field yg kosong, akan diisi secara otomatis" colspan="3"/>
    <group colspan="4" col="2">
        <field name="reconstruct" />
    </group>
</form>"""

view_form_abort = '''<?xml version="1.0"?>
<form string="Import Data LO (fast)">
  <label string="Dibatalkan! Fungsi yang sama masih berjalan" colspan="4" />
</form>
'''
    
class wizard_import_lo_fast(wizard.interface):

    lo_centralmysap_log=''
    def _get_file(self, cr, uid,data,context):
#        if data['form'].has_key('nomorlo') and not data['form']['nomorlo']==False:
#            params=data['form']
#        elif data['form']['datafrom']  and not data['form']['datafrom']==False:
#            params=data['form']
#        else:
#            params={}
        params=data['form']
        params['status']='A,C'
        data_msg = ''
        view_msg = ''
        company_id = data['form']['company_id']

        #Kalau ada params['nomorlo'] maka berarti user ingin mengupdate data LO tertentu saja
        #Kalau tidak berarti, akan ditarik sekumpulan LO dalam rentang waktu tertentu        
        if params.has_key('nomorlo') and params['nomorlo']!=False: #1st priority, if this is filled other variable is not important            
            fs = pooler.get_pool( cr.dbname ).get( 'fast.summary' )
            fd = 'Import LO MySAP [%s]' % (params['nomorlo'],)
            fasum = {
                'ref'  : fs,
                'lo' : fs.create(cr, uid,{'name':fd, 'started': datetime.now()}),
                'company_id' : company_id,
            }
            params['nomorlo'] = params['nomorlo'].split(',') 
            
            self.lo_centralmysap_log,data_msg = DownloadLO_ByLONumber_FromMySAP(self, cr, uid,params, fasum, scenario=1, callsource=1, reconstruct=False)
        else:
            self.lo_centralmysap_log,data_msg = routineprocess_parametrized(self, cr, uid, params, scenario=1, callsource=1, reconstruct=False)
            #---DEBUG PARSING
#             parseUnprocessedLo(self,cr,uid)
#             self.lo_centralmysap_log='DEBUG PARSING DONE'
#             data_msg='OKE DEH'
        
        
        data_msg = data_msg.split('\n')
        for msg in data_msg:
            view_msg += """<label align="0.0" string=" - %s" colspan="8"/>""" %(msg)

        view_form_end1 = """<?xml version="1.0"?>
        <form string="Import Data LO">
            <image name="gtk-dialog-info" colspan="8"/>
            <group colspan="8" col="8">
                <separator string="LO Import Done" colspan="8"/>
                <label align="0.0" string="LO sudah di import dari MySAP dengan sukses.\n Silahkan lihat hasilnya di menu LO Master." colspan="8"/>
                <label align="0.0" string="Result : " colspan="8"/>
                %s
            </group>
        </form>"""  %(view_msg)  
           
        
        _QUEST_FORM. __init__(view_form_end1)
        
        return {}
    def _check_process_running(self,cr,uid,data,context):        
        if LOcentralrunning:
            return 'abort'
        else:
            return 'start'
    states={
        'init': {
            'actions': [],
            'result' : {'type': 'choice', 'next_state': _check_process_running }
        },
        'abort':{
            'actions': [],
            'result': {'type': 'form', 'arch': view_form_abort, 'fields': {},
                'state': [
                    ( 'end', 'Ok', 'gtk-ok', True )
                ]
            }
        },
        'start':{
            'actions': [_data_load1],
            'result': {'type': 'form', 'arch': view_form_start % 'Open dan Close', 
                'fields': fields_form_start,
                'state': [
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('finish', 'Ok', 'gtk-ok', True)
                ]
            }
        },

        'finish':{
            'actions': [_get_file],
            'result': {'type': 'form', 'arch': _QUEST_FORM, 'fields': {},
                       'state': [
                                 ('end', 'Ok', 'gtk-ok', True)
                                 ]
                       }
                    },        
                }

wizard_import_lo_fast('pn.import.lo.fast')
