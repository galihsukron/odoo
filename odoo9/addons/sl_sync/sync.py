'''
Created on Maret 07, 2016

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
    _name = 'sl.sync.model'

    _columns = {
        'sequence': fields.integer('Sequence', select=True),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'model': fields.related('model_id', 'model', type='char', string="osv model name"),
        'mode': fields.selection(
            [('master', 'Master Data'),
             ('transaction', 'Business Transaction'),
            ],
            string='Synchronization Mode', required=True),
    }
    
    _defaults = {
        'mode': lambda self, cr, uid, c: 'master',
    }
    
    # UNTUK SINKRONISASI
    def getmastertables(self, cr, uid, *args, **kwdargs):
        #dipakai utntuk sinkronisasi master
        model_list = self.search_read(cr, uid, [], ['model'])
        #print "paramsz::",cr, uid,",", model_list
        model_array= [
            field['model']  for field in model_list
        ]
        #print model_array
        return model_array
        #return['sl.crew']
#         return['res.company', 'res.users',
#                'sl.distributor', 
#                'sl.vehicle', 'sl.vehicle.distributor',
#                'sl.hr.employee', 
#                'sl.lo',
#                'sl.shipment', 'sl.shipment.lolines',
#                'sl.crew', 
#                'sl.crew.distributor',
#                'sl.selection_field']

    def getmasteruniqueness(self, *args, **kwdargs):
        return{'res.company':'id',
               'res.users':'id',
               'sl.vehicle':'name',
               'sl.hr.employee':'id',
               'sl.lo': 'name',        
               'sl.shipment':'id',
               'sl.distributor':'id',
               'sl.distributor.master':'id',
               'sl.shipment.lolines':'id',
               'sl.crew':'nip',
               'sl.selection_field':'shortcut'}
        
    def getacceptablefunctiontables(self, *args, **kwdargs):
        '''
            Normalnya, fields.related & fields.function tidak disingkronkan.
            Tetapi, ada kebutuhan khusus field.functions disingkronkan
        '''
        #dipakai utntuk sinkronisasi master
        #return['sl.crew']
        return['res.company', 'res.users']