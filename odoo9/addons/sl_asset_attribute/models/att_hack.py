'''
Created on Nov 14, 2016

@author: x2nie
'''

from openerp import fields, models, api
import time
import datetime
#from odoo import SUPERUSER_ID #, models
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
#from dateutil.relativedelta import relativedelta

import  pprint

RES= [('binary', 'binary'), 
             ('boolean', 'boolean'), 
             ('char', 'char'), 
             ('date', 'date'), 
             ('datetime', 'datetime'), 
             ('float', 'float'), 
             ('html', 'html'), 
             ('integer', 'integer'), 
             ('many2many', 'many2many'), 
             ('many2one', 'many2one'), 
             ('monetary', 'monetary'), 
             ('one2many', 'one2many'), 
             ('reference', 'reference'), 
             ('selection', 'selection'), 
             ('serialized', 'serialized'), 
             ('text', 'text')]

ORDEREDFIELDTYPE= [ 
             ('boolean', 'Yes / No',        'Simple yes or no'), 
             ('char',    'Small text',      'Limited text info'),
             ('text',    'Long text',       'Note and long info'),
             ('integer', 'Number',          '-2147483648 to +2147483647'),
             ('float',   'Fraction Number', 'Number with digits eg: 0.269'), 
             ('date',    'Date',            'Date without time'), 
             ('datetime','Date and time',   'Date + time'),
             ('selection', 'Options',       'Pick one from values'),
             ('binary',  'File or Photo',   'Document or picture attachment'), 
             ('html',    'HTML'),
            ] 
class tracking_attribute(models.Model):    
    #_name = 'asset.attribute'    
    _inherit = 'ir.model.fields'
    
    @api.model
    def _get_field_types(self):
        res = super(tracking_attribute, self)._get_field_types()
        #print 'FIELDTYPEz-'*20, res
        tt = []
        ttkeys = []
        # 1 ORDERED
        for kv in ORDEREDFIELDTYPE + res:
            k,v = kv[:2]
            if not k in ttkeys:
                tt.append(tuple([k, v]))
                ttkeys.append(k)

        print 'TTTTz-'*20, tt
        return tt    