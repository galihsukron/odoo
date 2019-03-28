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
from shapely.coords import required
#from dateutil.relativedelta import relativedelta


class devices_configuration(models.Model):
    _name = 'device.configurations'
    _description = 'Device Configurations'
    
    
    device_serial_number = fields.Char('Serial Number', required=True, track_visibility='onchange', translate=True)
    def_location = fields.Many2one('asset.location', 'Location')
    device_last_update = fields.Datetime(string='Device Last Update',readonly=True)
    location_def_active = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="N", required=True)
    
    ###koneksi ke AS
    server_ip = fields.Char('Server IP', required=True, track_visibility='onchange', translate=True)
    server_port = fields.Char('Server Port', required=True, track_visibility='onchange', translate=True)
    server_db_name = fields.Char('Server DB', required=True, track_visibility='onchange', translate=True)
    server_user = fields.Char('Server Username', required=True, track_visibility='onchange', translate=True)
    server_password = fields.Char('Server Password', required=True, track_visibility='onchange', translate=True)
    
    
    
    
    #gps   
    gps_plugin = fields.Selection([('SL.GPS_Chainway','SL.GPS_Chainway'),
        ], track_visibility='onchange',  default="SL.GPS_Chainway", required=True)
    gps_service = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="N", required=True)
    gps_required = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="N", required=True)
    
    
    
    
    
    #rfid
    rfid_assembly = fields.Selection([('SL.RFID.MC75A6','SL.RFID.MC75A6'),('SL.RFID_UHF.Chainway','SL.RFID_UHF.Chainway'),
        ], track_visibility='onchange',  default="SL.RFID_UHF.Chainway", required=True)
    rfid_threaded = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="Y", required=True)
    rfid_power = fields.Selection([
        ('10','10'),('11','11'),('12','12'),('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),
        ('18','18'),('19','19'),('20','20'),('21','21'),('22','22'),('23','23'),('24','24'),
        ], track_visibility='onchange',  default="10", required=True)
    
    
    
    
    #sinkronisasi
    sync_service_timespan = fields.Integer(string='Sync Service Timespan')
    sync_active = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="N", required=True)
    sync_batch_treshold = fields.Integer(string='Sync Batch Treshold')
    
    
    
    
    #fingerprint
    fingergrabber = fields.Selection([('Chainway','Chainway'),
        ], track_visibility='onchange',  default="Chainway", required=True)
    fingerprint_bmpParser = fields.Selection([('SACISOCSE','SACISOCSE'),
        ], track_visibility='onchange',  default="SACISOCSE", required=True)
    fingergrab_threaded = fields.Selection([('Y','YES'),('N','NO'),
        ], track_visibility='onchange',  default="Y", required=True)
    
    #wifi
    wifi_plugin      = fields.Selection([('SL.Wifi_Chainway','SL.Wifi_Chainway'),
        ], track_visibility='onchange',  default="SL.Wifi_Chainway", required=True)
    
    
    #other
    user_id_setting = fields.Many2one('res.users', 'User Setting')
    setup_firsttime = fields.Selection([('YES','YES'),('NO','NO'),
        ], track_visibility='onchange',  default="NO", required=True)  # ga dipake
    del_prev_scan = fields.Integer(string='Delete Prev Scan in Hour')
    instalation_date = fields.Datetime(string="Instalation Date", store=True)
    
    _sql_constraints = [('serial_number_uniq', 'unique(device_serial_number)', 'Serial Number already exists !')]



    def function_test(self, cr, uid):
        print "ALOOOHHHAAAAAA FUNCTION TEST NIH CUY!"
        return 1
    
    def update_configuration_date(self, cr, uid, context=None, *args):
        print args
        print context
        return 1

#    @api.multi
#    def write(self, vals):
    @api.multi
    def write(self, vals):
        """"give a unique alias name if given alias name is already assigned"""
        print 'DEVICE CONFIGURATIONS+WRITE CUY=', vals
        self.env['log.device.configuration'].sudo().create({'changed_value': str(vals),'device_id':self.id})
        return super(devices_configuration, self).write(vals)



class log_device_configurations(models.Model):
    _name = 'log.device.configuration'
    _description = 'Log Device conf'
    
    changed_value = fields.Text('Changed Value')
    device_id = fields.Many2one('device.configurations', 'Device ID', help="This is a serial number")
    


