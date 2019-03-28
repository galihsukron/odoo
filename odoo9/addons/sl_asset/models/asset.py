'''
Created on Apr 15, 2015

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


class tracking_item_category(models.Model):
    _name = 'asset.type'
    _description = 'Asset Type'
    _inherit = ['mail.thread']
    
    name = fields.Char('Name', required=True, track_visibility='onchange', translate=True)
    parent_id = fields.Many2one('asset.type', 'Parent Type', select=True)
    child_ids = fields.One2many('asset.type', 'parent_id', 'Child Type')

    
class tracking_item(models.Model):
    _name = 'asset.asset'
    _description = 'Asset'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    

#     _track = {
#         'log_state': {
#             'sl_asset.mt_item_new': lambda self, cr, uid, obj, context=None: obj.state == 'new',
#             'sl_asset.mt_item_complete': lambda self, cr, uid, obj, context=None: obj.state != 'new' and obj.log_state in ['close','transfered'],
#         }
#         'stage_id': {
#             # this is only an heuristics; depending on your particular stage configuration it may not match all 'new' stages
#             'project.mt_task_new': lambda self, cr, uid, obj, ctx=None: obj.stage_id and obj.stage_id.sequence <= 1,
#             'project.mt_task_stage': lambda self, cr, uid, obj, ctx=None: obj.stage_id.sequence > 1,
#         },
#         'user_id': {
#             'project.mt_task_assigned': lambda self, cr, uid, obj, ctx=None: obj.user_id and obj.user_id.id,
#         },
#         'kanban_state': {
#             'project.mt_task_blocked': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'blocked',
#             'project.mt_task_ready': lambda self, cr, uid, obj, ctx=None: obj.kanban_state == 'done',
#         },
#    }

    def _default_company_id(self) :
        return self.env['res.company']._company_default_get('resource.calendar')


    name = fields.Char('Name',  track_visibility='always', required=True, help="Document number or Hardware Serial Number")
    type_id = fields.Many2one('asset.type', 'Asset Type')
    #color = fields.Integer('Color Index')
    #partner_id = fields.Many2one('res.partner', 'Vendor Partner')
    state = fields.Selection([('new', 'New'),  # new = signal for don't show the circular referenced field which is not yet available, such log_id
                                   ('draft','Draft'), # draft can change the flow
                                   ('open','Open'), # meaning In Progress
                                   ('completed', 'Completed'),
                                   ('canceled', 'Canceled'),
                                   ],
                                   'Status', required=True, readonly="1",
                                   copy=False,
                                   track_visibility='onchange',
                                   #help='When new statement is created the status will be \'Draft\'.\n'
                                   #     'And after getting confirmation from the bank it will be in \'Confirmed\' status.'
                                        default='draft')
        
    #name = fields.Char(compute='_item_name_get_fnc',  string='Name', store=True)
    company_id = fields.Many2one('res.company', 'Company', default=_default_company_id)
    #location_id = fields.Many2one('asset.location', 'Location')
    #pic_uid = fields.Many2one('res.users', 'PIC')
    note = fields.Char('Note')
    tag_ids = fields.Many2many('asset.tag', 'asset_tag_rel', 'asset_id','tag_id', 'Tags', copy=False)
        
        #--- MOVEMENT
    asset_move_ids = fields.One2many('asset.move', 'asset_id', 'Progress/Steps')
        
        #inherits-link-like relation, dynamic flow (new mode)
    asset_move_id = fields.Many2one('asset.move', 'Current Step')
                
        #current
    #log_id = fields.Many2one(related='asset_move_id.flow_step_id', relation='tracking.flow.step', domain = "[('flow_id','=',flow_id)]", string="Current Step", track_visibility='always')
    #log_id2 = fields.Many2one(related='asset_move_id.flow_step_id', relation='tracking.flow.step', domain = "[('flow_id','=',flow_id)]", string="Current Step"),#for progress meter
    #log_activity = fields.Char(related='log_id.activity',  readonly=True)
    #log_pic = fields.Many2one(related='asset_move_id.pic_uid', relation='res.users', store=True, string="Current PIC")
    log_pic = fields.Many2one(related='asset_move_id.pic_partner', relation='res.partner', store=True, string="Current PIC")
    #log_state = fields.Selection(related='asset_move_id.state',  selection=_get_tracking_progress_log_state, string="Current Step State", readonly=True, track_visibility='always',)
    log_date = fields.Datetime(related='asset_move_id.date',  string="Date", store=True)
    #log_completed = fields.Char(compute='_get_log_completed',  string='Completed Logs')
    log_location = fields.Many2one(related='asset_move_id.location_id', relation='asset.location', store=True, string="Current Location")
        
    dummies = fields.Boolean('Dummies Attribute')
        
        
    #--- IMAGES
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used as avatar for this asset, limited to 1024x1024px",
        #default=lambda self: self._get_default_image(False, True)
        default=False)
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


    @api.model
    def create(self, vals):
        location_id = vals.pop('log_location',False)
        pic = vals.pop('log_pic',False)
        log_date = vals.pop('log_date',False)
        
        res = super(tracking_item, self ).create(vals)
        
        #create first progress.log
        olog = self.env['asset.move']
        
        log_data = {'asset_id': res.id} #///, 'pic_uid': uid}
        if location_id:
            log_data['location_id'] = location_id
        if pic:
            log_data['pic_partner'] = pic
        if log_date:
            log_data['date'] = log_date
#         flow_id = vals.get('flow_id',0)
#         #if vals.has_key('flow_id'):
#         if flow_id:
#             log_data['flow_id'] = flow_id
#             oflow = self.pool.get('tracking.flow')
#             bflow = oflow.browse(cr,uid, flow_id)
#             istep = 1
#             for step in bflow.step_ids:
#                 if istep==1:
#                     log_data['flow_step_id'] = step.id
#                 elif istep == 2:
#                     log_data['next_step_id'] = step.id
#                 else:
#                     break
#                 istep += 1
        reslog = olog.create(log_data)
        #upd_data = {'state':'draft'}#, 'asset_move_id': ilog}    
        #res.write(upd_data)
        
        #vals['asset_move_id'] = reslog.id # for asset.move
        
        
        #reslog.write({'asset_id': res.id})
                
        return res
    
    @api.model
    def create0(self, vals):
        location_id = vals.pop('log_location',False)
        res = super(tracking_item, self ).create(vals)
        
        #create first progress.log
        olog = self.env['asset.move']
        
        log_data = {'asset_id': res.id} #///, 'pic_uid': uid}
        if location_id:
            log_data['location_id'] = location_id
#         flow_id = vals.get('flow_id',0)
#         #if vals.has_key('flow_id'):
#         if flow_id:
#             log_data['flow_id'] = flow_id
#             oflow = self.pool.get('tracking.flow')
#             bflow = oflow.browse(cr,uid, flow_id)
#             istep = 1
#             for step in bflow.step_ids:
#                 if istep==1:
#                     log_data['flow_step_id'] = step.id
#                 elif istep == 2:
#                     log_data['next_step_id'] = step.id
#                 else:
#                     break
#                 istep += 1
        reslog = olog.create(log_data)
        upd_data = {'state':'draft'}#, 'asset_move_id': ilog}    
        res.write(upd_data)
                
        return res
    
#     def return_action_to_open(self, cr, uid, ids, context=None):
#         """ This opens the xml view specified in xml_id for the current vehicle """
#         if context is None:
#             context = {}
#         if context.get('xml_id'):
#             #flow_id = self.browse(cr, uid, ids[0], context=context).flow_id.id
#             res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'sl_asset', context['xml_id'], context=context)
#             res['context'] = context
#             #res['context'].update({'default_asset_id': ids[0], 'default_flow_id':flow_id})
#             res['context'].update({'default_asset_id': ids[0]})
#             res['domain'] = [('asset_id','=', ids[0])]            
#             return res
#         return False
    @api.multi
    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('sl_asset', xml_id)
            res.update(
                context=dict(self.env.context, default_asset_id=self.id),
                domain=[('asset_id', '=', self.id)]
            )
            return res
        return False
    
class tracking_item_tag(models.Model):
    _name = 'asset.tag'
    
    name = fields.Char('Name', required=True, translate=True)
    color = fields.Integer('Color Index')




    