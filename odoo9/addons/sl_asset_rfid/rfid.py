'''
Created on Maret 03, 2016

@author: Fathony
'''

from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

class tracking_item(osv.Model):
    _inherit = 'asset.asset'
    _columns = {
        'rfid': fields.char('RFID', required=False, help="Radio Frequency ID"),        
    }
    #_sql_constraints = [('asset_rfid_unique','unique(rfid)', 'RFID already exists')]
    
    
class tracking_department(osv.Model):
    _inherit = "asset.location"
    _columns = {
        'rfid': fields.char('RFID', required=False, help="Radio Frequency ID"),        
    }
    #_sql_constraints = [('location_rfid_unique','unique(rfid)', 'RFID already exists')]

class tracking_progress_party(osv.Model):
    _inherit='asset.move.party'
    _columns = {
        'rfid_raw': fields.char('Location RFID', required=False, help="Radio Frequency ID"),        
    }
    
class tracking_progress_log(osv.Model):
    _inherit='asset.move'
    _columns = {
        'rfid_raw': fields.char('Asset RFID', required=False, help="Radio Frequency ID"),        
    }
        