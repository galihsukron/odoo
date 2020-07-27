
import datetime
import io
import itertools
import logging
import psycopg2
import operator
import os
import re

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.misc import ustr
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

_logger = logging.getLogger(__name__)


# Funsgsi baru untuk custom import
class custom_import(models.TransientModel):
    _inherit = "base_import.import"
    
    @api.multi
    def custom_import(self, fields, options, dryrun=False):       
        self.ensure_one()
        self._cr.execute('SAVEPOINT import')
        # print "custom_import"
        
#         pengecekan model dan juga field yang di import, jika sesuai maka import = true
        master_component_import = False 
        if str(self.res_model) == "master.item" and  "component_ids/component_name" in fields:
            component_name_index    = fields.index("component_ids/component_name")
            if "component_ids/component_id" not in fields :
                fields[component_name_index] = "component_ids/component_id"
            master_component_import = True

        try:
            data, import_fields = self._convert_import_data(fields, options)            
            data = self._parse_import_data(data, import_fields, options)
        except ValueError as error:
            return [{
                'type': 'error',
                'message': pycompat.text_type(error),
                'record': False,
            }]

#         proses pembuatan master data komponen
        if master_component_import == True:
            estimation_field        = False
            estimation_index        = 0
            
            if "component_ids/component_estimation" in import_fields :
                estimation_index = import_fields.index("component_ids/component_estimation")
                estimation_field = True
                
            for data_imp in data :
                        name = data_imp[component_name_index]
                        if estimation_field == True:
                            estimation = int(data_imp[estimation_index])
                        if not self.env["master.component"].search([("name","=",str(name))]):                            
                            component_data = {
                                    "name" : name,
                                    "estimation" : estimation
                                    }
                            self.env["master.component"].create(component_data)


        
        _logger.info('importing %d rows...', len(data))

        model = self.env[self.res_model].with_context(import_file=True)
        defer_parent_store = self.env.context.get('defer_parent_store_computation', True)
        if defer_parent_store and model._parent_store:
            model = model.with_context(defer_parent_store_computation=True)
        
        import_result = model.load(import_fields, data)
        _logger.info('done')
        try:
            if dryrun:
                self._cr.execute('ROLLBACK TO SAVEPOINT import')
            else:
                self._cr.execute('RELEASE SAVEPOINT import')
        except psycopg2.InternalError:
            pass

        return import_result['messages']

