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

class Location(models.Model):
    """Asset Location"""

    _inherit = "asset.location"
    
    latlng = fields.Char(compute='_compute_latlng',store=False)

    #@api.multi
    @api.depends('latitude', 'longitude')
    def _compute_latlng(self):
        for record in self:
            record.latlng = '%s,%s' % (record.latitude, record.longitude)
            
    # onchange handler
    @api.onchange('latlng')
    def _onchange_price(self):
        # set auto-changing field
        (lat,lng) = self.latlng.split(',')[:2]
        #self.price = self.amount * self.unit_price
        self.latitude = lat
        self.longitude = lng