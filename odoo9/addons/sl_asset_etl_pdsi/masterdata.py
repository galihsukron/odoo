from openerp.osv import fields,osv
from openerp import tools
from openerp import pooler
import types
import datetime,time

resultobj=False # switch khusus tas honeywell

def runsql(cr, sql):
    start = time.clock()
    cr.commit()        
    cr.execute(str(sql))  
    cr.commit()      
    try:
        end = time.clock()
        #=======================================================================
        # return <result>, <code time executed>
        #=======================================================================        
        return cr.dictfetchall()                    
    except:
        return False

def create_priveliges(cr):
    #=======================================================================
    # Grant select to tasgroup jika ada di database
    #=======================================================================
    cr.execute('SELECT * FROM pg_roles WHERE rolname = \'tas\' ')
    if not cr.fetchone():
        query=[]
        query.append("CREATE USER tas WITH PASSWORD 'tas123'")
        query.append("CREATE GROUP tasgroup WITH USER tas;")
        query.append("GRANT SELECT ON report_master_crew to tasgroup;")
        query.append("GRANT SELECT ON report_master_mt to tasgroup;")
        query.append("GRANT SELECT ON report_master_spbu to tasgroup;")
        query.append("GRANT SELECT ON report_master_lo to tasgroup;")
        query.append("GRANT SELECT ON report_shipment to tasgroup;")
        query.append("GRANT SELECT ON report_shipment_cancel to tasgroup;")
        query.append("GRANT SELECT ON report_shipment_lo to tasgroup;")
        query.append("GRANT SELECT ON report_shipment_history to tasgroup;")
        print 'Setting Priviliges TAS'
        for dat in query:
            try: runsql(cr,dat)
            except: pass
    return True

class master_data_location(osv.osv):
    _name = "master.data.location"
    _description = "master data location"
    _auto = False

    def init(self, cr):       
        # JIKA MENAMBAH FIELD BARU JALANKAN FUNGSI DROP INI SEKALI SAJA SETELAH ADA ERROR DI INIT.
        tools.sql.drop_view_if_exists(cr, 'master_data_location')  
        
        query="""
            create or replace view master_data_location as 
            (
                SELECT a.name asset, l.name locations, a.rfid, a.pdsi_kd_asset, a.pdsi_no_movable, l.pdsi_kd_rig,a.log_date tanggal
                FROM asset_asset a
                INNER JOIN asset_move m ON a.asset_move_id = m.id
                LEFT JOIN asset_location l ON m.location_id = l.id
            )
        """
        
        runsql(cr,query)
        
        #-----------------------------------------------------------------------
        # Buat Priveliges
        #-----------------------------------------------------------------------
        create_priveliges(cr)        
        
#master_data_location()

#===============================================================================
# FOR INTEGRATION ASSET THROUGHT XML RPC
#===============================================================================
class data_asset(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'data.asset'
    _description = 'data asset'
    
    # get username
    def setlog(self, cr, uid, function, result):
        dicVal = {}        
        obj_users = pooler.get_pool(cr.dbname).get('res.users')                
        try:
            username=obj_users.read(cr, uid, [uid],[])
            dicVal['user']=username[0]['name']
        except Exception,e:            
            print e.value            
            dicVal['user']='Unknown'
            pass
        
        dicVal['function_name']=function
        dicVal['result']=result
        return self.create(cr, uid, dicVal)
    
    def convertNonetoquote(self, dictoflist):
        data= [dict([k, v if v is not None else ''] 
                    for k, v in d.iteritems())
                         for d in dictoflist]        
        return data
    
    def sendsql(self, cr, query):
        cr.execute(query)
        datas=cr.dictfetchall()
        if len(datas)>0:
            return self.convertNonetoquote(datas)        #
        return False
    
    def getasset(self, cr, uid, asset, no_moveable, tgl):
        query2 = """
        """
        query3 = """
        """
        query4 = """
        """
        query1="""
        SELECT a.name asset, a.pdsi_epc as rfid, a.pdsi_kd_asset, a.pdsi_no_movable, a.log_date tanggal, l.pdsi_kd_rig as pdsi_kd_rig, s.name as shipment_number, s.state as shipment_state
                FROM asset_asset a
                INNER JOIN asset_move m ON a.asset_move_id = m.id
                INNER JOIN asset_move_party p ON m.party_id = p.id
                INNER JOIN asset_shipment s ON p.shipment_id = s.id
                INNeR JOIN asset_location l ON a.log_location = l.id
                WHERE a.asset_move_id = m.id
        """		
		
				
#        query1="""
#        SELECT a.name asset, a.rfid, a.pdsi_kd_asset, a.pdsi_no_movable, a.log_date tanggal
#                FROM asset_asset a
#                INNER JOIN asset_move m ON a.asset_move_id = m.id
#                WHERE a.asset_move_id = m.id
#        """
        if (asset != ""):
            query2 = """
            and a.pdsi_epc = '%s'
            """%(asset)
        if (no_moveable != ""):
            query3 = """
            and a.pdsi_no_movable = '%s'
            """%(no_moveable)
        if(tgl != ""):
            query4 = """
            and cast(a.log_date as date) = '%s'
            """%(tgl)
        query = query1 + query2+ query3 + query4
        print query
        datas=self.sendsql(cr, query)
        if datas:
            messages = 'True'
            result=datas
        else: 
            result = False
            messages = 'False, Data not found.'        
        
        # simpan ke log
        if result: 
            return['True','',result]
        else: return['False',messages.replace('False,',''),[]] 
        
        
    def getassetlocation(self, cr, uid, location):
        query="""
        SELECT cast(id as varchar), asset, locations
        FROM master_data_location
        WHERE locations = '%s'
        """ %(location)
                             
        # get data
        datas=self.sendsql(cr, query)
        if datas:
            messages = 'True, Data found'
            result=datas
        else:
            nodata = True
            messages = 'False, Data not found.'
        if not resultobj: return result
        if result: return['True','',result]
        else: return['False',messages.replace('False,',''),[]]
        
    _columns = {
            'create_date':fields.datetime('Waktu Trigger', size=64, required=False, readonly=True),
            'user':fields.char('User', size=64, required=False, readonly=True),
            'function_name':fields.char('Fungsi', size=64, required=False, readonly=True),
            'result':fields.text('Hasil', required=False, readonly=True),
    }
#data_asset()