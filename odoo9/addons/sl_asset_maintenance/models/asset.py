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

class tracking_item(models.Model):
    _inherit = 'asset.asset'
    
    maintenance_state = fields.Many2one('asset.state', 'Maintenance State')
    
    