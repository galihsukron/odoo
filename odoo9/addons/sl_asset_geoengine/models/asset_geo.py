'''
Created on Maret 31, 2016

@author: Fathony
'''

#from openerp.osv import fields, osv
# import time
# import datetime
# from openerp import tools
# from openerp.osv.orm import except_orm
# from openerp.tools.translate import _
# from dateutil.relativedelta import relativedelta
from openerp.addons.base_geoengine import geo_model
from openerp.addons.base_geoengine import fields as geo_fields
from openerp.addons.base_geoengine import geo_field
from openerp import api
from openerp.osv import fields
#print '*'*200, fields
import utm
import json

class ShipmentLine(geo_model.GeoModel):
    """Asset Shipment Line"""

    _inherit = "asset.move.party"
    
    #latitude = fields.Float('Latitude')
    #longitude = fields.Float('Longitude')
    the_point = geo_fields.GeoPoint('Coordinate')
    
    def mix_the_point(self, vals):
        if vals.get('latitude',0) and vals.get('longitude',0):
            pt = utm.from_latlon(vals['latitude'], vals['longitude'])
            #vals['the_point'] = str({"type": "Point", "coordinates": list(pt[:2])}) #list(pt[:2]) # 'POINT(%.15f, %.15f)' % pt[:2]
            ptc = {"type": "Point", "coordinates": list(pt[:2])}
            vals['the_point'] = json.dumps(ptc)
        
    @api.multi
    def write(self, vals):
        self.mix_the_point(vals)
        return super(ShipmentLine, self).write(vals)
    
#     @api.model
#     @api.returns('self', lambda value: value.id)
#     def create(self, vals):
#         self.mix_the_point(vals)
#         return super(ShipmentLine, self).create(vals)
            
        
# class tracking_progress_log(osv.Model):
#     _inherit='asset.move'
#     _columns = {
#         'the_point': fields.geo_related('party_id', 'the_point', type='geo_point', string='ThePoint'), #parent
#     }
class TrackingProgressLog(geo_model.GeoModel):
    """Asset Shipment Line"""

    _inherit = "asset.move"
    
    #latitude = fields.Float('Latitude')
    #longitude = fields.Float('Longitude')
    the_point = geo_fields.GeoPoint('Coordinate')
    
    def mix_the_point(self, vals):
        if vals.get('latitude',0) and vals.get('longitude',0):
            float_la = float(vals['latitude'])
            float_lo = float(vals['longitude'])
            #pt = utm.from_latlon(vals['latitude'], vals['longitude'])
            pt = utm.from_latlon(float_la, float_lo)
            #vals['the_point'] = str({"type": "Point", "coordinates": list(pt[:2])}) #list(pt[:2]) # 'POINT(%.15f, %.15f)' % pt[:2]
            ptc = {"type": "Point", "coordinates": list(pt[:2])}
            vals['the_point'] = json.dumps(ptc)
        elif vals.get('location_id',0) and not vals.get('the_point',0):
            location = self.env['asset.location']
            vals['the_point'] = location.sudo().browse(vals['location_id']).the_point
        
    @api.multi
    def write(self, vals):
        self.mix_the_point(vals)
        return super(TrackingProgressLog, self).write(vals)
    
    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        self.mix_the_point(vals)
        return super(TrackingProgressLog, self).create(vals)

# class tracking_item(osv.Model):
#     _inherit = 'asset.asset'
#      
#     _columns = {
#         'log_point': fields.geo_related('asset_move_id', 'the_point', type='geo_point', string='ThePoint', stored=True), #parent
#     }
    
class TrackingItem(geo_model.GeoModel):
    _inherit = 'asset.asset'
    
    #log_point = geo_field.GeoRelated('asset_move_id', 'the_point', type='geo_point', string='ThePoint', stored=True) #parent
#     _columns = {
#         'log_point': fields.geo_related('asset_move_id', 'the_point', type='geo_point', string='ThePoint', stored=True), #parent
#     }
    log_point = geo_fields.GeoPoint('ThePoint', related='asset_move_id.the_point') #parent
        
