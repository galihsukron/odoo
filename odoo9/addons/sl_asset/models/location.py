'''
Created on Apr 16, 2015

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
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp

class tracking_department(models.Model):
    _name = "asset.location"
    _inherit = ['mail.thread']
    _description = 'Asset Location'
    

    @api.depends('name','parent_id')
    def _dept_name_get_fnc(self):
        #return self.name_get()
        for loc in self:
            loc.complete_name = (loc.parent_id and loc.parent_id.name + '/' or '') + loc.name  
        

    #>> 
    def _default_company_id(self): 
        return self.env['res.company']._company_default_get('asset.location')

    
    name = fields.Char('Location Name', required=True)
    complete_name = fields.Char(compute='_dept_name_get_fnc',  string='Name')
    latitude = fields.Float('Latitude', digits=dp.get_precision('Asset Geo Location')) #digits=(4, 16))
    longitude = fields.Float('Longitude', digits=dp.get_precision('Asset Geo Location')) #digits=(4, 16))
    
    company_id = fields.Many2one('res.company', 'Company', select=True, required=False, default=_default_company_id)
    parent_id = fields.Many2one('asset.location', 'Parent Location', select=True)
    child_ids = fields.One2many('asset.location', 'parent_id', 'Child Location')
    #manager_id = fields.Many2one('tracking.employee', 'Manager')
    #member_ids = fields.One2many('tracking.employee', 'department_id', 'Members', readonly=True)
    #jobs_ids = fields.One2many('tracking.job', 'department_id', 'Jobs')
    note = fields.Text('Note')

    #<<<

    #--- IMAGES
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this asset, limited to 1024x1024px",
        #default=lambda self: self._get_default_image(False, True)
        )
    image_medium = fields.Binary("Medium-sized image",
        compute='_compute_images', inverse='_inverse_image_medium', store=True, attachment=True,
        help="Medium-sized image of this asset. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image",
        compute='_compute_images', inverse='_inverse_image_small', store=True, attachment=True,
        help="Small-sized image of this asset. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")

    @api.depends('image')
    def _compute_images(self):
        for rec in self:
            rec.image_medium = tools.image_resize_image_medium(rec.image)
            rec.image_small = tools.image_resize_image_small(rec.image)

    def _inverse_image_medium(self):
        for rec in self:
            rec.image = tools.image_resize_image_big(rec.image_medium)

    def _inverse_image_small(self):
        for rec in self:
            rec.image = tools.image_resize_image_big(rec.image_small)


#     def _check_recursion(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         level = 100
#         while len(ids):
#             cr.execute('select distinct parent_id from asset_location where id IN %s',(tuple(ids),))
#             ids = filter(None, map(lambda x:x[0], cr.fetchall()))
#             if not level:
#                 return False
#             level -= 1
#         return True
# 
#     _constraints = [
#         (_check_recursion, 'Error! You cannot create recursive location.', ['parent_id'])
#     ]

    def foo(self,bar,ber,bor):
        pass
    
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive location.'))


    @api.multi
    def name_get(self):
#         if context is None:
#             context = {}
#         if not ids:
#             return []
        reads = self.read(['name','parent_id'])
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

