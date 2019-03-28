'''
Created on Nov 25, 2016
Last Modified on: 19 February 2017

@author: x2nie
'''

from openerp import models, fields, api
from warnings import catch_warnings
#print '*'*200, fields
import utm
import json

class Asset(models.Model):
    """Asset Location"""

    _inherit = "asset.asset"
    
    latlng = fields.Char('Location', compute='_compute_latlng',store=False)

    #@api.multi
    #@api.depends('asset_move_id.location_id')
    @api.depends('asset_move_id')
    def _compute_latlng(self):
        for record in self:
            #record.latlng = '%s,%s' % (record.asset_move_id.location_id.latitude, record.asset_move_id.location_id.longitude)
            record.latlng = '%s,%s' % (record.asset_move_id.latitude, record.asset_move_id.longitude)
            