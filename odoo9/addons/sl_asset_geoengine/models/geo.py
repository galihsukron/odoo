'''
Created on Maret 31, 2016

@author: Fathony
'''

# from openerp.osv import fields, osv
# import time
# import datetime
# from openerp import tools
# from openerp.osv.orm import except_orm
# from openerp.tools.translate import _
# from dateutil.relativedelta import relativedelta
from openerp import fields
from openerp.addons.base_geoengine import geo_model
from openerp.addons.base_geoengine import fields as geo_fields

class RetailMachine(geo_model.GeoModel):
    """GEO OSV SAMPLE"""

    _name = "asset.geo"

    name = fields.Char('Name', size=64, required=True)
    state = fields.Selection([('hs', 'HS'),
                              ('ok', 'OK')],
                             'State',
                             index=True)    

    latitude = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    the_point = geo_fields.GeoPoint('Coordinate')
        