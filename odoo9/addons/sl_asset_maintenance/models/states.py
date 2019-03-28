'''
Created on July 20, 2017

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

PERSPECTIVE = (12, 'Maintenance')
    
class AssetState(models.Model):
    _inherit = 'asset.state'
    
    @api.model
    def _setup_fields(self, partial):
        """Hack due since the field 'perspective' selection is dynamic.
        """
        cls = type(self)
        perspective_selection = cls._fields['perspective'].selection
        # print 'perspective_selection '*20, perspective_selection
        if PERSPECTIVE not in perspective_selection:
            tmp = list(perspective_selection)
            tmp.append(PERSPECTIVE)
            cls._fields['perspective'].selection = list(set(tmp))
            
            # perspective_selection = cls._fields['perspective'].selection
            # print 'PERSPECTIVE_now= '*20, perspective_selection
            
        super(AssetState, self)._setup_fields(partial)


    