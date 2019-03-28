'''
Created on July 20, 2017

@author: Fathony
'''

from openerp import fields, models
import time
import datetime
import openerp
from openerp import tools, api
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
#from dateutil.relativedelta import relativedelta


    
class tracking_item_state(models.Model):
    _name = 'asset.state'
    _order = 'perspective,sequence asc,id'
    
    name = fields.Char('Name', required=True)
    perspective = fields.Selection([(0, 'Undefined')],
                                   'Perspective',
                                   required=True,
                                   index=True,
                                   track_visibility='onchange',
                                   help='Each asset may has several states depending on perspective'
                                   )
    sequence = fields.Integer('Sequence', default=10, help="Used to order the note stages")
    description = fields.Char('Description', help="Long description of the state within current perspective.")

    _sql_constraints = [('asset_name_unique','unique(perspective,name)', 'State name already exists')]


    