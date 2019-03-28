# -*- coding: utf-8 -*-
# copied from addons/asset/

from openerp.osv import fields, osv
from openerp.tools.translate import _

class asset_configuration(osv.osv_memory):
    _inherit = 'asset.config.settings'

    _columns = {
        'pdsi_import_source': fields.selection([
            (0, "Internal sqlite sample database"),
            (1, 'Actual PDSI/SMART SQL-Server')
            ], "PDSI Import Sorce",
            help='From where the import wizard will gather data.'),
        'pdsi_import_dbserver': fields.char('DB Server', size=128,
            help='Valid SQL-Server Address :\n' \
                 'TONY-PC\MSSQL2008R2 \n' \
                 '(local)\SQLEXPRESS \n' \
                 '10.200.3.4'),
        'pdsi_import_dbname': fields.char('DB Name', size=128),
        'pdsi_import_dbuser': fields.char('DB User', size=128),
        'pdsi_import_dbpassword': fields.char('DB Password', size=128),
    }

#     def onchange_time_estimation_asset_timesheet(self, cr, uid, ids, group_time_work_estimation_tasks):
#         if group_time_work_estimation_tasks:
#             return {'value': {'group_tasks_work_on_tasks': True}}
#         return {}

    def set_pdsi_import(self, cr, uid, ids, context=None):
        ir_values = self.pool['ir.values']
        config = self.browse(cr, uid, ids[0], context)
        for key in ['source', 'dbserver','dbname','dbuser','dbpassword']:
            field = 'pdsi_import_'+key
            value = config[field]
            ir_values.set_default(cr, uid, self._name, field, value)

# 
# 
#     def set_default_pdsi_import_source(self, cr, uid, ids, context=None):
#         config_value = self.browse(cr, uid, ids, context=context).pdsi_import_source
#         self.pool.get('ir.values').set_default(cr, uid, 'asset.config.settings', 'pdsi_import_source', config_value)
# 
#     def set_default_pdsi_import_dbserver(self, cr, uid, ids, context=None):
#         config_value = self.browse(cr, uid, ids, context=context).pdsi_import_dbserver
#         self.pool.get('ir.values').set_default(cr, uid, 'asset.config.settings', 'pdsi_import_dbserver', config_value)

