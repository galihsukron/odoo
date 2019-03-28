'''
Created on Jun 26, 2016

@author: Fathony
'''

from openerp.osv import fields, osv
import time
import datetime
from openerp import SUPERUSER_ID #, models

class Asset(osv.Model):
    _inherit = 'asset.asset'
    
    _columns = {
        'pdsi_lastupdate': fields.datetime('Last Update'),            
        'pdsi_kd_asset': fields.integer('KD Asset', help=""),        
        'pdsi_no_movable': fields.char('No. Movable', size=128),        
        'pdsi_epc': fields.char('EPC Number', size=128),        
        'pdsi_no_eqid': fields.char('No. Equipment', size=128),  
        'pdsi_deskripsi': fields.char('Raw Description', size=255),        
        'no_sap': fields.char('No. SAP', size=64),        
    }
    #log_point = fields.GeoPoint('ThePoint', related='asset_move_id.the_point') #parent
    


class AssetType(osv.Model):
    _inherit = 'asset.type'
    _order = "pdsi_dots"
    
    _columns = {
        'pdsi_level': fields.integer('Sub Level'),        
        'pdsi_name': fields.char('Description', size=255),        
        'pdsi_subsection': fields.char('Subsection Code', size=255),        
        'pdsi_dots': fields.integer('Dots'),        
    }    
    
    def dottoint(self, dot = 'A.8.3.11'):
        d = dot.strip().split('.')
        
        a = []
        for c in d:
            if c.isdigit():
                i = int(c) 
            else:
                try:
                    i = ord(c) - ord('A') +1
                except:
                    print 'ERROR ORD:',c, 'DOTS=',dot
                    raise 
            #print i
            a.append(i)
            
        a.reverse()
        n = 0 #a[0]
        for b in range(len(a)):
            n += a[b] << (6*b)
        return n

    def create(self, cr, uid, vals, context=None):
        if 'pdsi_subsection' in vals:
            vals['pdsi_dots'] = self.dottoint(vals['pdsi_subsection']) 
        res_id = super(AssetType, self).create(cr, uid, vals, context=context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'pdsi_subsection' in vals:
            vals['pdsi_dots'] = self.dottoint('pdsi_subsection') 
        super(AssetType, self).write(cr, uid, ids, vals, context=context)
        return True

    
    
class AssetLocation(osv.Model):
    _inherit = 'asset.location'
    
    _columns = {
        'pdsi_lastupdate': fields.datetime('PDSI Last Update'),            
        'pdsi_kd_rig': fields.char('Kode Rig', size=255),        
        #'pdsi_subsection': fields.char('Subsection Code', size=255),        
    }        