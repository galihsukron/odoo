'''
Created on Mar 9, 2016

@author: Fathony
'''

from openerp.osv import fields, osv
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

    
'''
Created on Oct 29, 2014

@author: MPD
'''
#from osv import fields, osv

#--- TABEL USER
class res_users( osv.Model ):
    #_name = 'res.users'
    _inherit = 'res.users'

    _columns = {

        'fpimage1': fields.binary('Fingerprint Image'),
        'fpimage2': fields.binary('Fingerprint Image'),
        
        'fptemplate1': fields.binary('Fingerprint Minutea'),
        'fptemplate2': fields.binary('Fingerprint Minutea'),

        'fpimg_file1': fields.char('File name', size=128),
        'fpimg_file2': fields.char('File name', size=128),

        'fpformat': fields.char('Fingerprint Format', size=20),
    
    }
    _defaults = {      

     }
     
#res_users()    