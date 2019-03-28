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
from warnings import catch_warnings
print '*'*200, fields
import utm
import json

class Location(geo_model.GeoModel):
    """Asset Location"""

    _inherit = "asset.location"
    the_point = geo_fields.GeoPoint('Coordinate')
    
    def mix_the_point(self, vals):
        #if not vals.get('the_point',False) and vals.get('latitude',0) and vals.get('longitude',0):
        lat = vals.get('latitude',0)
        lng = vals.get('longitude',0)
        pot = vals.get('the_point',False)
        if not pot: 
            try:
                print vals['latitude'], vals['longitude']
            except:
                vals['latitude'] = 0
                vals['longitude'] = 0
            pt = utm.from_latlon(vals['latitude'], vals['longitude'])
            #vals['the_point'] = str({"type": "Point", "coordinates": list(pt[:2])}) #list(pt[:2]) # 'POINT(%.15f, %.15f)' % pt[:2]
            ptc = {"type": "Point", "coordinates": list(pt[:2])}
            vals['the_point'] = json.dumps(ptc)
        elif pot and not (lat and lng):
            print 'pPOTTT===',pot
   
    @api.multi
    def write(self, vals):
        self.mix_the_point(vals)
        return super(Location, self).write(vals)
    
    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        self.mix_the_point(vals)
        return super(Location, self).create(vals)

