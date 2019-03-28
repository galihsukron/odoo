'''
Created on Apr 15, 2015

@author: Fathony
'''

from openerp import fields, models, api
import time
import datetime
from openerp import SUPERUSER_ID #, models
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
#from dateutil.relativedelta import relativedelta

import  pprint


class tracking_attribute(models.Model):    
    _name = 'asset.attribute'
    
    _description = 'Additional Attributes'
    _order = 'sequence asc'
    _inherits = {
        'ir.model.fields': 'field_id',
    }
    
    
    field_id = fields.Many2one('ir.model.fields', 'Field', required=True, ondelete='restrict', auto_join=True)
    #department_id = fields.Many2one('tracking.department', 'Department', required=True)
    #name = fields.Char(related='department_id.name',  string="Step", readonly=True)
    #name = fields.Char(compute='_get_sequenced_name',  string='Name')
    #duration = fields.Integer('Duration', required=True, group_operator="sum")
    sequence = fields.Integer('Sequence', help="Used to order the visual visibility")
    default_val = fields.Char('Default value')#, compute='_compute_reference', store=False)
    istate = fields.Integer('internal state', default=0)
    iplaceholder = fields.Char('Placeholder')
    
    
    

    def _default_model_id(self):
        res = self.env['ir.model'].sudo().search([('model','=','asset.asset')])
        return res.ids[0]

    #model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade',
    #                           help="The model this field belongs to")
    #model_id = fields.Many2one('ir.model', default=_default_model_id)

    

    @api.model
    def default_get(self, fields_list):
        res = super(tracking_attribute, self).default_get(fields_list)
        res.update({'model_id': self._default_model_id()})
        #print 'DEFAULT-'*20, res
        return res
        
    @api.model
    def create(self, vals):
        if 'field_description' in vals:
            suffix = 'x_' #self._defaults['name'] # x_
            caption = vals['field_description'].lower()
            if not caption.isalnum():
                caption =  ''.join(ch for ch in caption if ch.isalnum())
            vals['name'] = suffix + caption
            
        self._validatevals(vals)
        res = super(tracking_attribute,self).create(vals)
        return res    

    @api.multi
    def write(self, vals):
        self._validatevals(vals, writing=True)
        return super(tracking_attribute, self).write(vals)
    
    def _validatevals(self, vals, writing=False):
        vals['istate'] = vals.get('istate',0) + 1;
        ir_val = self.env['ir.values']
        model = 'asset.asset'
        field_name = vals.has_key('name') and vals['name'] or self.name
        if vals.has_key('default_val'):
            default_val_resolved = False
            value = vals.get('default_val', False)
            if writing: #check if default value changed
                if not vals['default_val']: #user removing default val
                    #irdefault = ir_val.get_default(model, field_name)
                    #if irdefault: #
                    search_criteria = [
                            ('key', '=', 'default'),
                            #('key2', '=', condition and condition[:200]),
                            ('model', '=', model),
                            ('name', '=', field_name),
                            ('user_id', '=', False),
                            ('company_id', '=', False)
                        ]
                    dbdefaults = ir_val.search(search_criteria)
                    if dbdefaults:
                        dbdefaults.sudo().unlink()
                    default_val_resolved = True
                    
            if not default_val_resolved and value:
                ir_val.sudo().set_default( model, field_name, value)
            
        #return pickle.loads(defaults.value.encode('utf-8')) if defaults else None

class tracking_attributes_visibility(models.Model):
    "Att Visibility. Each asset type as its own attribute visibilities"
    _name = 'asset.attribute.visibility'
    
    type_id = fields.Many2one('asset.type', 'Flow', select=True)
    attribute_id = fields.Many2one('asset.attribute', 'Attributes', required=True)
    visibility = fields.Char('Visibility', default="{'0': 'editable'}")
    #name = fields.Char(related='department_id.name',  string="Step", readonly=True)
    #name = fields.Char(compute='_get_sequenced_name',  string='Name')
    #duration = fields.Integer('Duration', required=True, group_operator="sum")
    #sequence = fields.Integer('Sequence', help="Used to order the flow steps")

    def get_visibility_dict(self):
        res = {}
        for row in self.read(['attribute_id','visibility']):
            att_id = row['attribute_id'][0] 
            res[att_id] = row
        return res
    
class tracking_flow(models.Model):
    _inherit = 'asset.type'
    #_description = 'Tracking Flow'
    
    #name = fields.Char('Name', required=True, translate=True)
    #step_ids = fields.One2many('asset.type.step', 'flow_id', 'Steps',copy=True)
    #step_ids = fields.One2many('asset.type.step', 'flow_id', 'Steps',copy=True)
    visibility_ids = fields.One2many('asset.attribute.visibility', 'type_id', 'Steps',copy=True)
    #step_count = fields.Integer(compute='_count_all',  string='Step Count', multi=True)
    #departement_ids = fields.Many2many('tracking.department', 'tracking_flow_step', 'flow_id','department_id', 'Steps')
    #attribute_ids = fields.One2many('asset.type.attributes', 'flow_id', 'Attributes')
    #res.groups.groups_id = fields.Many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', 'Groups')
    attributes_id = fields.Many2many('asset.attribute', 'tracking_flow_attributes', 'type_id', 'attribute_id', 'Attributes')
    #art_id = fields.Many2one('fa.clipart', 'Art', required=False, ondelete='restrict'),#, auto_join=True)
    #steps = fields.Char('Step')
    
    
        