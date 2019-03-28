'''
Created on 26 Mei 2014

@author: MPD
'''
from pn2.wizard import parsingutil
from pn2.wizard import parsingutil2
from pn2.wizard import parsingutil3
from osv import fields, osv

class ms2view_Plan_SIOD(osv.osv):
    "Temporary table MS2 planning"
    _name = "ms2view.plan_siod"
    _description = "ImportPlanningMS2 planning"
    _columns = {
        'pn_shipment_request_id' : fields.integer_big('Shipment Request ID SIOD'),
        'pn_spbu_id' : fields.integer_big('SPBU ID SIOD'),
        'res_company_id' : fields.integer_big('DEPOT SIOD'),
        'date_expected':fields.date('Tanggal Rencana Kirim',select=True),
        'date_order':fields.date('Tanggal Pemesanan'),
        
                
        'ms2_id' : fields.integer_big('MS2 ID',required=True),        
        'no_spbu': fields.char('SPBU', size=20),
        'ship_to': fields.char('Shipto', size=20), 
        'pasti_pas': fields.char('PastiPas', size=20), 
        'jenis_bbm': fields.char('SPBU', size=20), 
        'shift': fields.integer('Shift'), 
        'qty': fields.float('QTY'), 
        'plant': fields.char('KodeDepot', size=20), 
        'ketahanan_hari':fields.float('MS2 ID'), 
        'loading_order' : fields.char('SPBU', size=200), 
        'no_hp' : fields.char('SPBU', size=30), 
        'qty_ori':fields.float('QTY Ori'), 
        'shift_request': fields.integer('Shift'), 
        'id_kota' : fields.integer('Kota ID'), 
        'nama_kota': fields.char('SPBU', size=20),
        'status_plan': fields.char('SPBU', size=20),
        'tgl_kirim': fields.datetime('TGL_KIRIM'),
        
        #additional injection        
        'kl_found': fields.float('KL ada LO'),
        'kl_sisa': fields.float('KL tanpa LO'),   
        'update_level': fields.integer('UPDATED',help="Berapa kali di singkronkan?"),
    }
                
ms2view_Plan_SIOD()

class ms2view_pn_do(osv.osv):
    "Temporary table MS2 Loading Orders"
    _name = "ms2view.pn_do"
    _description = "ImportPlanningMS2 LO"
    
    _columns = {
        'pn_do_id' : fields.integer_big('DO ID SIOD'),
        
        'plan_siod_id' : fields.integer_big('MS2 ID',required=True),        
        'name': fields.char('No.LO', size=20, select=True, readonly=True,required=True, states={'0':[('readonly',False)],'4':[('readonly',False)]}),
        'name_int' : fields.integer_big('No.LO (int)', select=True, readonly=True),
        
        'spbu_name': fields.char('SPBU', size=20),
        'plant': fields.char('KodeDepot', size=20),         
        'ship_to': fields.char('SPBU', size=20), 
        
        'pasti_pas': fields.char('PastiPas', size=20), 
        'jenis_bbm': fields.char('SPBU', size=20), 
        #'shift': fields.integer('Shift',required=True), 
        
        #additional injection
        'shipment_request_id': fields.integer_big('Shipment Request'),
        'update_level': fields.integer('Shift',help="Berapa kali di singkronkan?"),

    }
                
ms2view_pn_do()

class ms2view_pn_spbu(osv.osv):
    "Temporary table MS2 Loading Orders"
    _name = "ms2view.pn_spbu"
    _description = "ImportPlanningMS2 SPBU"
    
    _columns = {
        'pn_spbu_id' : fields.integer_big('SPBU ID SIOD', select=1),
        'pn_spbu_master_id' : fields.integer_big('SPBU_Master ID SIOD'),
        'spbu_name_siod': fields.char('SPBU Name SIOD', size=20,   help="diambil dari SIOD|digunakan sbg koreksi jika sama dgn shipto|seperti 51601118"),
        
                        
        'spbu_name': fields.char('SPBU', size=20,   help="seperti 51601118"),
        'no_spbu': fields.char('SPBU MS2', size=20, help="seperti 51.601.118"),
        #'spbu_name_int' : fields.integer_big('No.LO (int)', select=True, readonly=True),
        'plant': fields.char('KodeDepot', size=20),         
        'ship_to': fields.char('SPBU', size=20),         
        'pasti_pas': fields.char('PastiPas', size=20),
         
        
         
        'no_hp' : fields.char('SPBU', size=30), 
        'id_kota' : fields.integer('Kota ID',required=True), 
        
        'nama_kota': fields.char('SPBU', size=20),
        #'ketahanan_hari':fields.float('MS2 ID',required=True), 
        'update_level': fields.integer('Shift',help="Berapa kali di singkronkan?"),
        
        
    }
                
ms2view_pn_spbu()

########################################################

class pn_do(osv.osv):
    _name = "pn.do"
    _inherit = "pn.do"
    _columns = {
       'name_int' : fields.integer_big('No.LO (int)', select=True, readonly=True),
    }
    def write(self, cr, uid, ids, vals, context={}):
        if vals and vals.has_key('name'):
            parsingutil.cleanText2(vals,['name'])
            vals['name_int'] = int(vals['name'])
        result = super(osv.osv, self).write(cr, uid, ids, vals)

        return result

pn_do()


class pn_shipment_request(osv.osv):
    _name = "pn.shipment.request"
    _inherit = "pn.shipment.request"
    _columns = {
       'name_int' : fields.integer_big('MS2 ID ', select=True, readonly=True),
    }
pn_shipment_request()
