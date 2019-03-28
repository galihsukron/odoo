# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from ..models import etl_pdsi

class goal_manual_wizard(osv.TransientModel):
    """Wizard to update a manual goal"""
    _name = 'wizard.asset.importfromsmart'
    _columns = {
        #'goal_id': fields.many2one("res.users", string='Goal', required=False),
        'current': fields.float('Current'),
        #'asset' : fields.boolean('Master Asset'),
        'asset' : fields.selection([('requiring','Only Updated'),('none',"Do not import"), ('all','Entire Asset')], 'Asset'),
        'assettype' : fields.selection([('requiring','Only Required'),('all','Entire Type')], 'Type'),
        'assetlocation' : fields.selection([('requiring','Only Required'),('all','Entire Location')], 'Location'),
    }
    _defaults = {
        'asset': 'requiring',
        'assettype': 'requiring',
        'assetlocation': 'requiring',
    }
    

    def load_config(self, cr, uid):
        ir_values = self.pool.get('ir.values')
        def config(var):
            section = 'asset.config.settings'
            return ir_values.get_default(cr, uid, section, var) or ''
        res  ={}
        pdsi_import_source = config('pdsi_import_source') or 0
        res['source'] = pdsi_import_source
        if pdsi_import_source:
            res['server'] = config('pdsi_import_dbserver')
            res['name'] = config('pdsi_import_dbname')
            res['user'] = config('pdsi_import_dbuser')
            res['password'] = config('pdsi_import_dbpassword')
        return  res
        
    def action_update_current(self, cr, uid, ids, context=None):
        """Wizard action for updating the current value"""
        
        #cr['pdsi_import'] = self.load_config(cr, uid)
        #if not etl_pdsi.CONFIG:
        etl_pdsi.CONFIG = self.load_config(cr, uid) #ALWAYS RELOAD CONFIG
        print 'etl_pdsi.CONFIG~=', etl_pdsi.CONFIG
        
        for wiz in self.browse(cr, uid, ids, context=context):
            print '='*20
            print 'Asset:', wiz.asset, 'type:', wiz.assettype, 'loc:', wiz.assetlocation 
            loadAsset   = wiz.asset
            loadType    = wiz.assettype
            loadLocation= wiz.assetlocation 
            break
        
        tbl_asset_type = self.pool.get('atemp.pdsi.asset.type')
        tbl_asset    = self.pool.get('atemp.pdsi.tbl_trs_aset')
        tbl_location = self.pool.get('atemp.pdsi.asset.location')
        
        #0. Clean up
        tbl_asset.clear_atemp(cr)
        
        #1. Load asset
        if loadAsset and loadAsset != 'none':
            tbl_asset.load_asset_from_pdsi(cr,uid, loadAsset)
            print "udah di load"
            
        #2. Extract unavailable asset type
        if loadType == 'all':
            tbl_asset_type.clear_atemp(cr)
            tbl_asset_type.load_all_type(cr,uid)
            
        else:
            tbl_asset_type.prepare_type_from_asset(cr,uid)
            print "udah di extract"
        #PSUDEO TYPE CRATION:
        tbl_asset_type.make_type_assumption(cr,uid)
            

        if loadLocation == 'all':
            tbl_location.load_all_location_from_pdsi(cr,uid,'all')
        else:
            tbl_location.prepare_location_from_asset(cr,uid)
        
            
        #3. Real store to asset
        tbl_asset.inject_atemp_to_AssetAsset(cr, uid)
        print "udah di inject"
#         SQLquery = 'select top 10 kd_aset, cast(deskripsi as varchar(500)) as deskripsi, cast(kd_subsection03 as varchar(500)) as kd_subsection03 from [tbl_trs_aset]'
#         err,rows = etl_pdsi.load_asset(SQLquery)
#         tbl_asset = self.pool.get('atemp.pdsi.tbl_trs_aset')
#         keys = ['kd_asset', 'deskripsi', 'kd_subsection03']
#         for row in rows:
#             vals = dict(zip(keys, row))
#             tbl_asset.create(cr,uid, vals)

#         goal_obj = self.pool.get('importfromsmart')
# 
#         for wiz in self.browse(cr, uid, ids, context=context):
#             towrite = {
#                 'current': wiz.current,
#                 'goal_id': wiz.goal_id.id,
#                 'to_update': False,
#             }
#             goal_obj.write(cr, uid, [wiz.goal_id.id], towrite, context=context)
#             goal_obj.update(cr, uid, [wiz.goal_id.id], context=context)
        return {}
