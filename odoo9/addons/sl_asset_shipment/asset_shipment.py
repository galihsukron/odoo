'''
Created on Apr 14, 2016

@author: Fathony
'''

from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
#import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import copy

class shipment(models.Model):
#class shipment( osv.Model ):
    _name = 'asset.shipment'
    _description = 'Shipment'
    _inherit = ['mail.thread']#, 'ir.needaction_mixin']

#     _track = {
#         'state' : {
#             'sl_asset_shipment.mt_shipment_new': lambda self, cr, uid, obj, context=None: obj.state == 'draft',
#             'sl_asset_shipment.mt_shipment_statechanged': lambda self, cr, uid, obj, context=None: obj.state and obj.state != 'draft' #and obj.log_state in ['close','transfered'],
#         }
#     }
    def _track_subtype(self, cr, uid, ids, init_values, context=None):
        print '*'*50, 'shipment._trackSubtypE,initvals=', init_values
        record = self.browse(cr, uid, ids[0], context=context)
        if 'state' in init_values: #and record.state:
            if not init_values['state']: # init_values.get('state'):
                return False
            if record.state: # init_values.get('state'):
                return 'sl_asset_shipment.mt_shipment_statechanged'
            else:
                return 'sl_asset_shipment.mt_shipment_new'
#         elif 'location' in init_values and record.location:
#             return 'calendar.subtype_invitation'
        return False
        return super(shipment, self)._track_subtype(cr, uid, ids, init_values, context=context)
    

    #date = fields.Date('Date')
    name = fields.Char('Shipment Reg', required=True)
    state =   fields.Selection([('draft','Draft'),('delivering','Delivering'),('done','Done')], 
                               track_visibility='onchange',  
                               string='State', default='draft')
    origin_loc_id = fields.Many2one('asset.location', 'Origin', required=True)
    destination_loc_id = fields.Many2one('asset.location', 'Destination', required=True)
    note = fields.Text("Note")
    
    planned_asset_ids   = fields.One2many('asset.shipment.planned', 'shipment_id', 'Inspection')
    asset_planned       = fields.Integer('Num of Assets',
                            store=True, readonly=True, compute='_compute_asset_summary')
    asset_added         = fields.Integer('Additional Assets',
                            store=True, readonly=True, compute='_compute_asset_summary')
    asset_missing       = fields.Integer('Mising Assets',
                            store=True, readonly=True, compute='_compute_asset_summary')
    asset_equal         = fields.Integer('Delivered Assets Equally',
                            store=True, readonly=True, compute='_compute_asset_summary')
    asset_total         = fields.Integer('Total Delivered Assets',
                            store=True, readonly=True, compute='_compute_asset_summary')
    
    
#     @api.multi
#     @api.depends('planned_asset_ids.asset_id')
#     def _compute_planned_asset(self):
#         """ Determine reserved, available, reserved but unconfirmed and used seats. """
#         # initialize fields to 0
#         for ship in self:
#             ship.asset_planned = 0
#         # aggregate registrations by event and by state
#         if self.ids:
#             state_field = {
#                 'draft': 'seats_unconfirmed',
#                 'open': 'seats_reserved',
#                 'done': 'seats_used',
#             }
#             query = """ SELECT shipment_id, count(shipment_id)
#                         FROM asset_shipment_planned
#                         WHERE shipment_id IN %s 
#                         GROUP BY shipment_id
#                     """
#             self._cr.execute(query, (tuple(self.ids),))
#             for event_id, num in self._cr.fetchall():
#                 event = self.browse(event_id)
#                 event['asset_planned'] = num
        
    date_created        = fields.Date('Created Date', default=fields.Date.today)
    date_x_departure    = fields.Date('Exp. Departure', help="Expected Departure Date")
    date_x_completion   = fields.Date('Exp. Completion', help="Expected Completion Date")
    
    party_ids = fields.One2many('asset.move.party', 'shipment_id', 'Inspection')
    @api.multi
    @api.depends('planned_asset_ids.asset_id','party_ids.state', 'party_ids.asset_total')
    def _compute_asset_summary(self):
        """ Determine reserved, available, reserved but unconfirmed and used seats. """
        # initialize fields to 0
        for ship in self:
            ship.asset_planned = 0
        # aggregate registrations by event and by state
        if self.ids:
            query = """ 
                SELECT 
                    shipment_id, 
                    SUM(plan1) AS planned,
                    SUM(add1) AS added, 
                    SUM(miss1) AS miss,
                    SUM(equal1) AS equal
                FROM(    
                   SELECT 
                    /*p.shipment_id, n.shipment_id AS n_ship_id,
                    p.id as pid,
                    n.id as nid, n.asset_id as nd_assid , 
                    m.id as mo_id, m.asset_id as mo_assid, 
                    
                    CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS id,
                    */
                    CASE WHEN p.shipment_id IS NOT NULL THEN p.shipment_id ELSE n.shipment_id END AS shipment_id,
                    CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS asset_id,
                    --a.name, 
                    /*CASE 
                        WHEN n.id IS NULL AND m.id IS NOT NULL THEN 'added' 
                        WHEN n.id IS NOT NULL AND m.id IS NULL THEN 'miss' 
                        WHEN n.id IS NOT NULL AND m.state = 'unreceived' THEN 'miss' 
                        WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 'equal' 
                        ELSE 'unknown' END
                        AS state,
                    */    
                    CASE WHEN n.id IS NOT NULL THEN 1 ELSE 0 END AS plan1,
                    CASE WHEN n.id IS NULL AND m.id IS NOT NULL THEN 1 ELSE 0 END AS add1,
                    CASE WHEN n.id IS NOT NULL AND p.id IS NOT NULL AND (m.id IS NULL OR m.state = 'unreceived') THEN 1 ELSE 0 END AS miss1,
                    CASE WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 1 ELSE 0 END AS equal1
                        
                    --,m.state as mstate
                    
                
                    -- SELECT *
                FROM
                
                (    -- #get party.id by latest date
                    SELECT DISTINCT ON (shipment_id)
                           id,shipment_id --,date
                    FROM   asset_move_party
                    WHERE shipment_id IN %s --IS NOT NULL --IN (1,2)
                    ORDER  BY shipment_id, "date" DESC
                )p
                
                LEFT JOIN asset_move m ON 
                    m.party_id = p.id 
                    
                FULL OUTER JOIN asset_shipment_planned n ON n.shipment_id = p.shipment_id    
                    AND 
                    m.asset_id = n.asset_id
                
                --LEFT JOIN asset_asset a ON a.id = m.asset_id OR a.id = n.asset_id
                -- WHERE n.shipment_id IS NOT NULL
                --ORDER BY n.shipment_id, n.id, p.id, m.id --, a.id
                ) a
                GROUP BY shipment_id
                    """
            self._cr.execute(query, (tuple(self.ids),))
            for ship_id, planned, added, miss,equal in self._cr.fetchall():
                if not ship_id:
                    continue
                ship = self.browse(ship_id)
                ship.asset_planned  = planned
                ship.asset_added    = added
                ship.asset_missing  = miss
                ship.asset_equal    = equal
                ship.asset_total    = equal + added
    
    #plan vs realisasi
    lastvsplan_ids = fields.One2many('asset.shipment.lastvsplan','shipment_id','Plan vs Last (asset list)')

    #Shipment to Asset list
    #init_party_id =     fields.Many2one('asset.move.party')
    #current_party_id =  fields.Many2one('asset.move.party')
    #move_ids =          fields.One2many('asset.move', related='current_party_id.move_ids', store=False, string="Assets")   
    #from_partner =      fields.Many2one('res.partner', related='current_party_id.from_partner_id',  store=False, string="Sender")   
    #to_partner =        fields.Many2one('res.partner', related='current_party_id.to_partner_id', store=False, string="Receiver")
    #location_id =       fields.Many2one('asset.location', related='current_party_id.location_id')
    #party_state =       fields.Selection(related='current_party_id.state')
    #pic_partner =       fields.Many2one('res.partner', related='current_party_id.pic_partner')   
    
    @api.model
    def create(self, vals):
        print 'SHIPMENT+create CUY=', vals
        return super(shipment, self).create(vals)
    
    @api.multi
    def write(self, vals):
        """"give a unique alias name if given alias name is already assigned"""
        print 'SHIPMENT+WRITE CUY=', vals
        return super(shipment, self).write(vals)
    
#     @api.model
#     def create(self, vals):
#         '''
#         shipment = kakek
#         party = anak
#         move = cucu
#         --- > supaya kake,anak,cucu maka tambahkan anak dulu
#         '''
#         #print 'Create.'*10, self._name 
#         #pprint.pprint(vals)
# #         move_ids = vals.pop('move_ids',False)
# #         if move_ids:
# #             vals['party_ids'] = vals.get('party_ids',[]) or [[0,
# #                  False,
# #                  {#u'courier': u'jne',
# #                   u'date': vals.get('date', False), # u'2016-04-04 06:31:28',
# #                   u'eta': False,
# #                   u'name': False,
# #                   ###u'pic_uid': self.env.user.id
# #                   }]]
# #             vals['party_ids'][0][2].update({'move_ids': move_ids})
#             
#             
#         init_party = {#u'courier': u'jne',
#                   'date': vals.get('date', False), # u'2016-04-04 06:31:28',
#                   'eta': False,
#                   'name': False,
#                   'from_partner_id' : vals.pop('from_partner',False),
#                   'to_partner_id' : vals.pop('to_partner',False),
#                   'location_id' : vals.pop('location_id',False),
#                   'move_ids' : vals.pop('move_ids',False),
#                   ###u'pic_uid': self.env.user.id
#                   }
#         vals['party_ids'] = [[0,False, init_party]]
#         res_id = super(shipment, self).create(vals)
# #        print "ship after create", res_id
# #        print "self after create", self.id
# #         if move_ids:
# #             self._cr.execute('''UPDATE asset_shipment 
# #             SET init_party_id = x.id, current_party_id = x.id
# #             FROM (
# #                 SELECT min(p.id) as id, shipment_id AS sid
# #                 -- SELECT init_party_id
# #                 FROM asset_move_party p 
# #              
# #                 WHERE shipment_id IS NOT NULL
# #                 AND shipment_id = %s
# #                 GROUP BY p.shipment_id
# #             ) x
# #             WHERE x.sid = asset_shipment.id 
# #             AND asset_shipment.id = %s''', (res_id.id,res_id.id))
# 
#         for party in res_id.party_ids:
#             res_id.init_party_id = party.id
#             res_id.current_party_id = party.id
#             break
#         return res_id
    
    
    #shipment to handover
    #handover_ids =     fields.One2many('asset.shipment.handover', 'shipment_id', 'Histories')
    #current_handover = fields.Many2one('asset.shipment.handover')
#     from_partner =     fields.related('current_handover', 'from_partner', type='many2one',relation='res.partner', store=False, string="Sender")   
#     to_partner =       fields.related('current_handover', 'to_partner', type='many2one',relation='res.partner', store=False, string="Receiver")
#     handover_state =   fields.related('current_handover','state', type='selection', selection=[('draft','Draft')('sent','Sent')('received','Received')], string='State')
#    from_partner =     fields.Many2one('res.partner', related='current_handover.from_partner',  store=False, string="Sender")   
#    to_partner =       fields.Many2one('res.partner', related='current_handover.to_partner', store=False, string="Receiver")
    #from_partner =     fields.Many2one('res.partner', related='current_handover.from_party.partner_id',  store=False, string="Sender")   
    #to_partner =       fields.Many2one('res.partner', related='current_handover.to_party.partner_id', store=False, string="Receiver")
    #handover_state =   fields.Selection([('draft','Draft'),('sent','Sent'),('received','Received')],related='current_handover.state', string='State')

    @api.multi
    def action_dummy(self):
        #current_handover.from_party.party_id.name = 'galih'
        pass
    
    @api.multi
    def action_confirm(self):
        #current_handover.from_party.party_id.name = 'galih'
        pass
    
    @api.multi
    def action_delivering(self):
        self.state = 'delivering' 
        print self.planned_asset_ids
        self.planned_asset_ids.write({'flag': 'confirmed' })
            
        
    @api.multi
    def action_done(self):
        self.state = 'done' 
        
    @api.multi
    def action_lock_asset(self):
        self.current_party_id.state = 'confirmed' 
    
    @api.multi
    def action_handover_sent(self):
        self.current_party_id.state = 'done' if self.current_party_id.state == 'received' else  'sent'
        self.current_party_id.pic_partner = self.from_partner.id
        self.move_ids.write({
                        'location_id': self.location_id.id,
                        'pic_partner': self.from_partner.id,
                        'date': fields.Datetime.now() })
         
    @api.multi
    def action_handover_received(self):
        self.current_party_id.state = 'done' if self.current_party_id.state == 'sent' else 'received'
        self.current_party_id.pic_partner = self.to_partner.id
        self.move_ids.write({
                        'location_id': self.location_id.id,
                        'pic_partner': self.to_partner.id,
                        'date': fields.Datetime.now() })

    @api.multi
    def action_new_handover(self):
        "Jangan dipanggil pertama kali, ini hanya utk melanjutkan yg sudah ada"
        new_party_id = self.current_party_id.create(
                        {'shipment_id':self.id,
                         'from_partner_id': self.current_party_id.to_partner_id.id
                         }).id
        for asset_move in self.move_ids:
            asset_move.copy({'party_id': new_party_id})
        self.current_party_id = new_party_id


class asset_planned_asset(models.Model):
    _name='asset.shipment.planned'
    shipment_id = fields.Many2one('asset.shipment', 'Shipment', required=False) #parent
    asset_id    = fields.Many2one('asset.asset', 'Asset', required=True) #parent
    image_small = fields.Binary(related='asset_id.image_small', string="Asset Image")
    asset_type  = fields.Many2one(related='asset_id.type_id', relation="asset.type", string="Asset Type", readonly=True)
    #name        = fields.function(_vehicle_log_name_get_fnc, type="char", string='Name', store=True),
    eta        = fields.Date('ETA', help="Estimated time arrival")
    flag        = fields.Selection([
                    ('draft','Draft'),
                    ('confirmed','Confirmed'),
                    ],'State', track_visibility='onchange',  default="draft", readonly=True)
    
    
class asset_move_party(models.Model):
    _inherit='asset.move.party'
    

#     _track = {
#         'state' : {
#             'sl_asset_shipment.mt_shipment_new': lambda self, cr, uid, obj, context=None: obj.state == 'draft',
#             'sl_asset_shipment.mt_shipment_statechanged': lambda self, cr, uid, obj, context=None: obj.state and obj.state != 'draft' #and obj.log_state in ['close','transfered'],
#         }
#     }    
    #shipment & relates
    shipment_id     = fields.Many2one('asset.shipment', 'Shipment Number') #harus online baru ketemu ID
    origin_loc_id   = fields.Many2one('asset.location', related="shipment_id.origin_loc_id", readonly=True)
    destination_loc_id  = fields.Many2one('asset.location', related="shipment_id.destination_loc_id", readonly=True)
    asset_planned = fields.Integer(related="shipment_id.asset_planned")
    shipment_raw    = fields.Char('Shipment Reg', required=False, help="Usefull when offline-mode") #offline, jadi RAW ini dipakai utk mencari ID

    @api.multi
    def action_sync_asset_list(self):
        'Fill the move_ids with the last available assets {last pictransfer | planned asset}'
        print 'self.ids=',self.ids
        if not self.shipment_id.id:
            #cant resolve
            #self.move_ids.ids = [] #can it be?
            pass
        else:
            for mov in self.move_ids:
                print "self.move.id=",mov.id, 'asset=', mov.asset_id.id, 'move=',mov
            
            asset_ids = []
            #1.a. AMBIL DARI LAST PARTY
            parties = copy.copy( self.shipment_id.party_ids.ids )
            if len(parties):
                last_party_id = parties[-1]
                #try resolves
                if last_party_id == self.id:
                    if len(parties) > 1:
                        last_party_id = parties[-2]
                    else:
                        last_party_id = False #stop, but should never happens?
                        #return
                if last_party_id: #found
                    last_party = parties.index(last_party_id) #we need index, not "id"
                    for mov in self.shipment_id.party_ids[ last_party ].move_ids:
                        asset_ids.append( mov.asset_id.id )
            
            #1.b. AMBIL DARI PLAN        
            if not asset_ids and len( self.shipment_id.planned_asset_ids.ids ):
                for mov in self.shipment_id.planned_asset_ids:
                    asset_ids.append( mov.asset_id.id )
                
            #2 COCOKKAN DGN ASSET SEKARANG
            for mov in self.move_ids:
                i = mov.asset_id.id
                if i in asset_ids: #jika asset sudah 
                    asset_ids.remove(i) #beri tanda
                    
            for i in asset_ids: #ada yg belum diberi tanda?
                #self.move_ids.ids.append( (0,0,{'asset_id':i}) )
                self.move_ids.create({'asset_id':i, 'party_id': self.id} )
                #mv = self.move_ids.new() 
                #mv.asset_id = i
                #mv.party_id = self.id        
    
    name        = fields.Char('Courier Reg', required=False, )
    activity    = fields.Selection([('scan','Scan'),('approval','Approval')],'Activity')
    state       = fields.Selection([
                    ('draft','Draft'),
                    ('confirming','Confirming'),
                    ('signing','Signing'),
                    ('completed','Completed'),
                    #('done','Done')
                    ],'State', track_visibility='onchange',  default="draft", readonly=True)
    from_partner_id = fields.Many2one('res.partner','From')
    to_partner_id   = fields.Many2one('res.partner','To')
    #courier        = fields.Char('Courier')
    
    note            = fields.Text("Note")
    eta             = fields.Date('ETA', help="Estimated time arrive")
    #asset_count     = fields.Integer('Quantity',
    #                        store=True, readonly=True, compute='_compute_asset')
    asset_equal     = fields.Integer('Equal',
                            store=True, readonly=True, compute='_compute_asset')
    asset_missing   = fields.Integer('Missing',
                            store=True, readonly=True, compute='_compute_asset')
    asset_added     = fields.Integer('Added',
                            store=True, readonly=True, compute='_compute_asset')
    
    asset_total     = fields.Integer('Total Receipt',
                            store=True, readonly=True, compute='_compute_asset')
    
    def reformat_gps_value(self, vals):
        if vals.has_key('longitude') and vals.has_key('latitude') and vals['longitude'] != 0 and vals['latitude'] != 0:
            try:
                vals['longitude'] = vals['longitude'].replace(',','.')
                vals['latitude'] = vals['latitude'].replace(',','.') 
            except:
                pass
            
    @api.model
    def create(self, vals):
        print 'SHIPMENT-line+create CUY=', vals
        self.reformat_gps_value(vals)
        return super(asset_move_party, self).create(vals)
    
    @api.multi
    def write(self, vals):
        """"give a unique alias name if given alias name is already assigned"""
        print 'SHIPMENT-line+WRITE CUY=', vals
        return super(asset_move_party, self).write(vals)
        
    @api.multi
    @api.depends('shipment_id','move_ids.asset_id')
    def _compute_asset(self):
        """ Determine reserved, available, reserved but unconfirmed and used seats. """
        # initialize fields to 0
        for party in self:
            party.asset_total = party.asset_missing = party.asset_added = party.asset_equal = 0
        # aggregate registrations by event and by state
        if self.ids:
            query = '''
                SELECT pid, sum(add1) as added, sum(miss1) as missing, sum(receive1) as received
                FROM (
                -- INFO: +fields: asset Total, miss, equal, added
                SELECT     /*n.id as nid, n.asset_id as nd_assid , 
                    m.id as mo_id, m.asset_id as mo_assid, m.state,*/
                    p.id as pid,
                    CASE WHEN n.id IS NULL AND m.id IS NOT NULL THEN 1 ELSE 0 END AS add1,
                    CASE WHEN n.id IS NOT NULL AND m.state = 'unreceived' THEN 1 ELSE 0 END AS miss1,
                    CASE WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 1 ELSE 0 END AS receive1
                    
                
                FROM asset_move_party p
                LEFT JOIN asset_move m ON 
                    m.party_id = p.id 
                LEFT JOIN asset_shipment_planned n ON n.shipment_id = p.shipment_id    
                    AND 
                    m.asset_id = n.asset_id
                
                WHERE p.id in %s --(7,8,9,10) --
                )A
                GROUP BY pid'''            
            self._cr.execute(query, (tuple(self.ids),))
            #for party_id, added, missing, oke  in self._cr.fetchall():
            for party_id, added, missing, received  in self._cr.fetchall():
                party = self.browse(party_id)
                party.asset_equal    = received
                party.asset_missing  = missing
                party.asset_added    = added
                party.asset_total    = received + added

#             query = """ SELECT party_id, count(party_id)
#                         FROM asset_move
#                         WHERE party_id IN %s 
#                         GROUP BY party_id
#                     """
#             self._cr.execute(query, (tuple(self.ids),))
#             for event_id, num in self._cr.fetchall():
#                 event = self.browse(event_id)
#                 event['asset_count'] = num
            
    @api.multi
    def action_dummy(self):
        #current_handover.from_party.party_id.name = 'galih'
        pass
        
    @api.multi
    def action_lock_asset(self):
        self.state = 'confirming' 
    
    @api.multi
    def action_handover_sent(self):
        self.state = 'signing'
        #self.state = 'done' if self.state == 'received' else  'sent'
        self.pic_partner = self.from_partner_id.id
        self.move_ids.write({
                        'location_id': self.location_id.id,
                        'pic_partner': self.from_partner_id.id,
                        'date': fields.Datetime.now() })
         
    @api.multi
    def action_handover_received(self):
        self.state = 'completed' #'done' if self.current_party_id.state == 'sent' else 'received'
        self.pic_partner = self.to_partner_id.id
        self.move_ids.write({
                        'location_id': self.location_id.id,
                        'pic_partner': self.to_partner_id.id,
                        'date': fields.Datetime.now() })

         
class asset_move(models.Model):
    _inherit='asset.move'
    
    state = fields.Selection([('received','Oke'),
                              ('unreceived','Not Found'),
                              ('added','+/Replaced')],'Condition', default='received')
    
    @api.multi
    def action_accept(self):
        self.write({'state': 'accepted'})
    
    @api.multi
    def action_reject(self):
        self.write({'state': 'rejected'})
    
        
from openerp import tools
        
class asset_shipment_lastvsplan(models.Model):
    _name='asset.shipment.lastvsplan'
    _auto = False
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'asset_shipment_lastvsplan')
        cr.execute("""
            CREATE OR REPLACE VIEW asset_shipment_lastvsplan AS (
                SELECT 
                    /*
                    p.shipment_id, n.shipment_id AS n_ship_id,
                    p.id as pid,
                    n.id as nid, n.asset_id as nd_assid , 
                    m.id as mo_id, m.asset_id as mo_assid, 
                    */
                    --CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS id,
                    --coalesce(p.id::varchar,'') || '/' || coalesce(n.id::varchar,'') AS id,
                    (COALESCE(CASE WHEN p.shipment_id IS NOT NULL THEN p.shipment_id ELSE n.shipment_id END::varchar,'') || 
    COALESCE(CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END::varchar,''))::bigint AS id,
                    
                    CASE WHEN p.shipment_id IS NOT NULL THEN p.shipment_id ELSE n.shipment_id END AS shipment_id,
                    CASE WHEN n.asset_id IS NOT NULL THEN n.asset_id ELSE m.asset_id END AS asset_id,
                    --a.name, 
                    CASE 
                        WHEN n.id IS NULL AND m.id IS NOT NULL THEN 'added' 
                        WHEN n.id IS NOT NULL AND m.id IS NULL THEN 'miss' 
                        WHEN n.id IS NOT NULL AND m.state = 'unreceived' THEN 'miss' 
                        WHEN n.id IS NOT NULL AND m.state != 'unreceived' THEN 'equal' 
                        ELSE 'unknown' END
                        AS state
                    --,m.state as mstate
                    
                
                    -- SELECT *
                FROM
                
                (    -- #get party.id by latest date
                    SELECT DISTINCT ON (shipment_id)
                           id,shipment_id --,date
                    FROM   asset_move_party
                    WHERE shipment_id IS NOT NULL
                    ORDER  BY shipment_id, "date" DESC
                )p
                
                INNER JOIN asset_move m ON 
                    m.party_id = p.id 
                    
                FULL OUTER JOIN asset_shipment_planned n ON n.shipment_id = p.shipment_id    
                    AND 
                    m.asset_id = n.asset_id
                
                --LEFT JOIN asset_asset a ON a.id = m.asset_id OR a.id = n.asset_id
                -- WHERE n.shipment_id IS NOT NULL
                --ORDER BY n.shipment_id, n.id, p.id, m.id --, a.id
            )""")
        
    shipment_id = fields.Many2one('asset.shipment', 'Shipment', required=False) #parent
    asset_id    = fields.Many2one('asset.asset', 'Asset', required=True) #parent
    #image_small = fields.Binary(related='asset_id.image_small', string="Asset Image")
    asset_type  = fields.Many2one(related='asset_id.type_id', relation="asset.type", string="Asset Type", readonly=True)
    state       = fields.Selection([
                    ('unknown','Unknown'),
                    ('equal','Equal'),
                    ('miss','Missing'),
                    ('added','Addition'),
                    ],'State', readonly=True)
    