'''
Created on Sep 18, 2014

@author: MPD
'''
from datetime import datetime, timedelta, date
from osv import fields, osv

class fast_summary(osv.osv):
    "Temporary table MS2 planning"
    _name = "fast.summary"
    _description = "Summary of Fast Download"
    
    def _icon_get(self, cr, uid, ids, field_name, arg=None, context=None):
        result = {}.fromkeys(ids, 'STOCK_NEW')
        if not isinstance(ids, list):
            ids = [ids]
        for e in ids:
            result[e] = 'STOCK_NEW'
        for r in self.read(cr, uid, ids, ['name','downloaded','found','inserted','failed']):
            if r['downloaded'] and (r['found'] + r['inserted'] +  r['failed'] == 0) :
                result[r['id']] = 'STOCK_INDEX'
                
            elif r['downloaded'] and r['downloaded'] ==r['found'] :
                result[r['id']] = 'STOCK_APPLY'

            elif not r['downloaded']  :
                if r['name'] == 'Parsing':
                    result[r['id']] = 'STOCK_EXECUTE'
                else:
                    result[r['id']] = 'STOCK_STOP'
                
#             if not r['found'] and r['failed'] :
#                 result[r['id']] = 'STOCK_STOP'
                 
            elif r['failed'] :
                result[r['id']] = 'STOCK_DIALOG_WARNING'
                 
            elif r['found'] :
                result[r['id']] = 'STOCK_ADD'
                 
            else:
                result[r['id']] = 'STOCK_APPLY'
        return result
    
    _columns = {        
        'name' : fields.char('Name', size=96, required=True),
        
        
        #'res_company_id' : fields.integer_big('DEPOT'),
        'company_id': fields.many2one( 'res.company', 'Company' ),
        
        'parent_id' : fields.many2one('fast.summary', 'Parent account', select=2),
        'child_ids' : fields.one2many('fast.summary', 'parent_id', 'Child Accounts'),
         
        'downloaded': fields.integer('Downloaded Amount'),    
        'found'     : fields.integer('Found'),
        'inserted'  : fields.integer('New'),
        'failed'    : fields.integer('Unsuccessful'),
        
        
        'started'   : fields.datetime( 'Start'),
        'finished'  : fields.datetime( 'Finish'),
        #'duration'  : fields.float('Duration'),
        'duration'  : fields.char('Duration', size=20), #displayed:  '00:02:59'
        
        'note' : fields.char('Note', size=255),
        
        #COSMETICS
        'icon': fields.function(_icon_get, method=True, string='Icon', type='char', size=32),        
        'chrono': fields.integer_big('Chrono'), # last wizard on top descending, children ascending
    }
    
    _order = 'chrono DESC, id'
    #_order = 'parent_id DESC, id'
    
    _defaults = {
        'downloaded' : lambda *a : 0,
        'found' : lambda *a : 0,
        'failed' : lambda *a : 0,
        'inserted' : lambda *a : 0,
    }
    def create( self, cr, uid, vals, context = {} ):
        has_parent = vals.has_key('parent_id') and vals['parent_id']
        result = super( osv.osv, self ).create( cr, uid, vals, context )
        
        if not has_parent:
            self.write(cr, uid, result, {'chrono':result})
        return result
    
    def write(self, cr, uid, ids, vals, context={}):
        if vals and vals.has_key('finished'):
            # we have both, keep them synchronized:
            res = self.read(cr, uid, ids, ['started'])
            if isinstance(res, list):
                res = res[0]
            started = res['started']
            if isinstance(started, str) or isinstance(started, unicode):
                started = started[:19]
                started = datetime.strptime(started, "%Y-%m-%d %H:%M:%S")
            
            finished = vals['finished']
            if isinstance(finished, str) or isinstance(finished, unicode):
                finished = finished[:19]
                finished = datetime.strptime(finished, "%Y-%m-%d %H:%M:%S")
            #
            diff = finished - started
            #duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)            
            #vals['duration'] = duration
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            vals['duration'] ='%02d:%02d:%02d' % (hours, minutes, seconds)
        result = super(osv.osv, self).write(cr, uid, ids, vals)

        return result    
   
                
fast_summary()