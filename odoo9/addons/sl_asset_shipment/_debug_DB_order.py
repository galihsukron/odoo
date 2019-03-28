'''
Created on Apr 4, 2016

@author: Fathony
'''


from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
import pprint

class DBorder(osv.Model):
    #_inherit = 'asset.shipment'
    def create(self, cr, uid, vals, context=None):
        print 'Create.','='*10, self._name, 'ctx:',context 
        pprint.pprint(vals)
        res_id = super(DBorder, self).create(cr, uid, vals, context=context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        print 'Write.','-'*10, self._name, 'ctx:',context
        pprint.pprint(vals)
        super(DBorder, self).write(cr, uid, ids, vals, context=context)
        return True

#class shipment( osv.Model, DBorder ):
#    _inherit = 'asset.shipment'
    
class shipment( DBorder ):
    _inherit = 'asset.shipment'
#     def create(self, cr, uid, vals, context=None):
#         print 'Create.'*10, self._name, vals
#         res_id = super(shipment, self).create(cr, uid, vals, context=context)
#         return res_id
#  
#     def write(self, cr, uid, ids, vals, context=None):
#         print 'Write.'*10, self._name, vals
#         super(shipment, self).write(cr, uid, ids, vals, context=context)
#         return True

     
class tracking_progress_party(DBorder):
    _inherit='asset.move.party'
    
    
class tracking_progress(DBorder):
    _inherit='asset.move'
    