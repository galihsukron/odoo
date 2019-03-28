'''
Created on Apr 15, 2015

@author: Fathony
'''

from openerp import fields, models
import time
import datetime
from openerp import tools, api
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
#from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp

class tracking_progress_party(models.Model):
    _name='asset.move.party'
    #_description='Bulk/header of asset movement'
    _order='date desc'
    _description = 'PIC Transfer'
    _inherit = ['mail.thread']#, 'ir.needaction_mixin']
    
        
    #asset_id = fields.Many2one('asset.asset', 'Asset', required=True), #parent
    #asset_id = fields.Many2one('asset.asset', 'Asset', required=True), #parent
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    #pic_uid = fields.Many2one('res.users', 'Person in Charge', help="Person in charge")
    pic_partner = fields.Many2one('res.partner', 'Person in Charge', help="Person in charge")
    #date_finish = fields.Datetime('Finish Date')
    location_id = fields.Many2one('asset.location', string='Location')
    longitude = fields.Float('Longitude', digits=dp.get_precision('Asset Geo Location')) #)
    latitude = fields.Float('Latitude', digits=dp.get_precision('Asset Geo Location')) #)
    asset_found = fields.Integer('Total Asset')
    move_ids = fields.One2many('asset.move', 'party_id', 'Inspection') #used by shipment
    
    #value = fields.Float('Odometer Value', group_operator="max")
    #flow_id = fields.Many2one(related='item_id.flow_id', relation='tracking.flow', string="Flow", readonly=True)
    #flow_step_id = fields.Many2one('tracking.flow.step', 'For Step', domain = "[('flow_id','=',flow_id)]", required=True)

    #next_step_id = fields.Many2one('tracking.flow.step', 'Next Step', domain = "[('flow_id','=',flow_id)]")
    #next_step_note = fields.Char('Note', size=254)

    #prior_log_id = fields.Many2one('tracking.progress.log', 'Previous Log', domain = "[('item_id','=',item_id)]")
    
    
    
class tracking_progress_log(models.Model):
    _name='asset.move'
    _description='Step log for a tracked item'
    _order='date desc'

#     def _vehicle_log_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
#         res = {}
#         for record in self.browse(cr, uid, ids, context=context):
#             name = record.asset_id.name
#             if not name:
#                 name = record.date
#             elif record.date:
#                 name += ' / '+ record.date
#             res[record.id] = name
#         return res
    @api.depends('asset_id', 'date')
    def _vehicle_log_name_get_fnc(self):
        for record in self:
            name = record.asset_id.name
            if not name:
                name = record.date
            elif record.date:
                name += ' / '+ record.date
            record.asset_id.name = name

#     def on_change_item(self, cr, uid, ids, tracking_item_id, context=None):
#         
#         if not tracking_item_id:
#             return {}
#         #odometer_unit = self.pool.get('tracking.item').browse(cr, uid, tracking_item_id, context=context).odometer_unit
#         #flow_id = self.pool.get('tracking.item').browse(cr, uid, tracking_item_id, context=context).flow_id.id
#         return {
#             'value': {
#                 #'unit': odometer_unit,
# #                'flow_id' : flow_id,
#             }
#         }
    
    
    party_id = fields.Many2one('asset.move.party', 'Asset', required=False) #parent
    asset_id = fields.Many2one('asset.asset', 'Asset', ondelete='cascade', required=True) #parent
    image_small = fields.Binary(related='asset_id.image_small',  string="Asset Image")
    asset_type = fields.Many2one(related='asset_id.type_id',  relation="asset.type", string="Asset Type", readonly=True)
    name = fields.Char(compute='_vehicle_log_name_get_fnc',  string='Name', store=True)
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now())
    #date_finish = fields.Datetime('Finish Date')
    longitude = fields.Float('Longitude', copy=False, digits=dp.get_precision('Asset Geo Location')) #)
    latitude = fields.Float('Latitude', copy=False, digits=dp.get_precision('Asset Geo Location')) #)
    location_id = fields.Many2one('asset.location', 'Location', copy=False)
    #pic_uid = fields.Many2one('res.users', 'PIC', help="Person in charge")
    pic_partner = fields.Many2one('res.partner', 'PIC', help="Person in charge", copy=False)
    
    
    #value = fields.Float('Odometer Value', group_operator="max")
    #flow_id = fields.Many2one(related='item_id.flow_id', relation='tracking.flow', string="Flow", readonly=True)
    #flow_step_id = fields.Many2one('tracking.flow.step', 'For Step', domain = "[('flow_id','=',flow_id)]", required=True)
    
    #next_step_id = fields.Many2one('tracking.flow.step', 'Next Step', domain = "[('flow_id','=',flow_id)]")
    #next_step_note = fields.Char('Note', size=254)
    
    #prior_log_id = fields.Many2one('tracking.progress.log', 'Previous Log', domain = "[('item_id','=',item_id)]")

        
    @api.model
    def create(self, vals):
        res = super(tracking_progress_log, self ).create(vals)
        #print "WOY!"*100, res
        #update as last history
        assetid = vals.get('asset_id',0)
        if assetid:
            #print "assetid.~*"*100, assetid
            oaset = self.env['asset.asset']
            #print "oeasset=", oaset                    
            oaset.browse([int(assetid )]).write({'asset_move_id': res.id} )
            #print "data written#!"*100
        return res

    @api.multi
    def write(self, vals):
        result = super(tracking_progress_log, self).write(vals)        
        if vals.get('pic_partner',False):
            for move in self:
                move.asset_id.asset_move_id = move.id #update related fields
        return result


    