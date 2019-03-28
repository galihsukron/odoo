'''
Created on Apr 26, 2015

@author: MPD
'''

#----------------------------------------------------------
# additional attributes
#----------------------------------------------------------

# import itertools
# import logging
# from functools import partial
# from itertools import repeat
# 
from lxml import etree
from lxml.builder import E
# 
import openerp
from openerp import SUPERUSER_ID, models
# from openerp import tools
# import openerp.exceptions
# from openerp.osv import fields, osv, expression
# from openerp.tools.translate import _
# from openerp.http import request
import json
from openerp import fields, models, api
import time
import datetime
from openerp import tools
from openerp.osv.orm import except_orm
from openerp.tools.translate import _
#from dateutil.relativedelta import relativedelta
from pprint import pprint

#_logger = logging.getLogger(__name__)
#----------------------------------------------------------
# Vitrual checkbox and selection for res.user form view
#
# Extension of res.groups and res.users for the special groups view in the users
# form.  This extension presents groups with selection and boolean widgets:
# - Groups are shown by application, with boolean and/or selection fields.
#   Selection fields typically defines a role "Name" for the given application.
# - Uncategorized groups are presented as boolean fields and grouped in a
#   section "Others".
#
# The user form view is modified by an inherited view (base.user_groups_view);
# the inherited view replaces the field 'groups_id' by a set of reified group
# fields (boolean or selection fields).  The arch of that view is regenerated
# each time groups are changed.
#
# Naming conventions for reified groups fields:
# - boolean field 'in_group_ID' is True iff
#       ID is in 'groups_id'
# - selection field 'sel_groups_ID1_..._IDk' is ID iff
#       ID is in 'groups_id' and ID is maximal in the set {ID1, ..., IDk}
#----------------------------------------------------------

def name_visibility_attribute(id):
    return 'att_visible_' + str(id)

def name_visibility_id(id):
    return 'avisible_id_' + str(id)

def name_boolean_attribute(id):
    return 'in_group_' + str(id)

def name_selection_attributes(ids):
    return 'sel_groups_' + '_'.join(map(str, ids))

def is_visibility_attribute(name):
    return name.startswith('att_visible_')

def is_visibility_id(name):
    return name.startswith('avisible_id_')

def is_boolean_attribute(name):
    return name.startswith('in_group_')

def is_selection_attributes(name):
    return name.startswith('sel_groups_')

def is_reified_attribute(name):
    return is_visibility_attribute(name) or is_visibility_id(name) #or is_boolean_attribute(name) or is_selection_attributes(name)

def get_visibility_attribute(name):
    return int(name[12:])


def get_boolean_attribute(name):
    return int(name[9:])

def get_selection_attributes(name):
    return map(int, name[11:].split('_'))

def partition(f, xs):
    "return a pair equivalent to (filter(f, xs), filter(lambda x: not f(x), xs))"
    yes, nos = [], []
    for x in xs:
        (yes if f(x) else nos).append(x)
    return yes, nos

def parse_m2m(commands):
    "return a list of ids corresponding to a many2many value"
    ids = []
    for command in commands:
        if isinstance(command, (tuple, list)):
            if command[0] in (1, 4):
                ids.append(command[2])
            elif command[0] == 5:
                ids = []
            elif command[0] == 6:
                ids = list(command[2])
        else:
            ids.append(command)
    return ids


class tracking_attributes(models.Model):
    _inherit = 'asset.attribute'

    #@api.model_cr
    #@api.cr
    #@api.guess
#    def init(self, cr):
    #def init(self, cr):
        #super(tracking_attributes, self).init(cr)
        #models.Model.init(self)
#        self.update_tracking_flow_view()
        
    @api.model
    def create(self, values):
        res = super(tracking_attributes, self).create(values)
        self.update_tracking_flow_view()
        return res

    @api.multi
    def write(self, values):
        res = super(tracking_attributes, self).write(values)
        self.update_tracking_flow_view()
        return res

    @api.multi
    def unlink(self):
        res = super(tracking_attributes, self).unlink()
        self.update_tracking_flow_view()
        return res

    @api.model
    def update_tracking_flow_view(self):
        # the view with id 'base.user_groups_view' inherits the user form view,
        # and introduces the reified group fields
        # we have to try-catch this, because at first init the view does not exist
        # but we are already creating some basic groups
        print 'INSTALLMENTz=-_*** '*10, 'cONTEXTz=', self._context
        if self._context.get('install_mode'):
            # use installation/admin language for translatable names in the view
            
            user_context = self.env['res.users'].context_get()  
            self = self.with_context(**user_context)
        #view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'base.user_groups_view', context=context)
        #view = self.env['ir.model.data'].sudo().xmlid_to_object('sl_asset_attribute.tracking_flow_attributed_view')
        view = self.env.ref('sl_asset_attribute.tracking_flow_attributed_view', raise_if_not_found=False)
        print "viviview:",view 
        
        if view and view.exists() and view._name == 'ir.ui.view':
            xml1, xml2 = [], []
            xml1.append(E.separator(string=_('Attributes'), colspan="2"))
            
            for app, kind, gs in self.get_groups_by_application():
                # hide groups in category 'Hidden' (except to group_no_one)
                attrs = {} # {'groups': 'base.group_no_one'} if app and app.xml_id == 'base.module_category_hidden' else {}
                if kind == 'selection':
                    # application name with a selection field
                    field_name = name_selection_attributes(map(int, gs))
                    xml1.append(E.field(name=field_name, **attrs))
                    xml1.append(E.newline())
                elif kind == 'visibility':
                    #
                    first_row = True 
                    for g in gs:
                        field_name = name_visibility_attribute(g.id)
                        attrs['widget'] = "visibility_grid" 
                        options = {'grid_columns':'step_ids'}
                        if first_row:
                            options['grid_header'] = True
                            first_row = False
                        #attrs['options'] ="{'grid_columns':'step_ids'}"
                        attrs['options'] = str(options)
                        xml2.append(E.field(name=field_name, **attrs))
                else:
                    # application separator with boolean fields
                    #app_name = app and app.name or _('Other')
                    #xml2.append(E.separator(string=app_name, colspan="4", **attrs))
                    for g in gs:
                        field_name = name_boolean_attribute(g.id)
                        xml2.append(E.field(name=field_name, **attrs))

            #xml = E.field(*(xml1 + xml2), name="attributes_id", position="replace")
            xml = E.field(*(xml1 + xml2), name="name", position="after")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
            xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
            view.write({'arch': xml_content})
        self.env['asset.asset'].sudo().update_dummies_view()
        
        return True
    
        
    def get_application_attributes(self, domain=None):
        return self.search( domain or [])

    def get_groups_by_application(self):
        """ return all groups classified by application (module category), as a list of pairs:
                [(app, kind, [group, ...]), ...],
            where app and group are browse records, and kind is either 'boolean' or 'selection'.
            Applications are given in sequence order.  If kind is 'selection', the groups are
            given in reverse implication order.
        """
        def linearized(gs):
            gs = set(gs)
            # determine sequence order: a group should appear after its implied groups
            order = dict.fromkeys(gs, 0)
            for g in gs:
                for h in gs.intersection(g.trans_implied_ids):
                    order[h] -= 1
            # check whether order is total, i.e., sequence orders are distinct
            if len(set(order.itervalues())) == len(gs):
                return sorted(gs, key=lambda g: order[g])
            return None

        # classify all groups by application
        #gids = self.get_application_attributes()
        by_app, others = {}, []
        #for g in self.browse(gids):
        for g in self.get_application_attributes():
#             if g.category_id:
#                 by_app.setdefault(g.category_id, []).append(g)
#             else:
#                 others.append(g)
            others.append(g)
        # build the result
        res = []
        apps = sorted(by_app.iterkeys(), key=lambda a: a.sequence or 0)
        for app in apps:
            gs = linearized(by_app[app])
            if gs:
                res.append((app, 'selection', gs))
            else:
                res.append((app, 'boolean', by_app[app]))
        if others:
            #res.append((False, 'boolean', others))
            res.append((False, 'visibility', others))
        return res
    
class tracking_flow(models.Model):
    _inherit = 'asset.type'
 
    def flow_hasbeen_modified(self):
        #print "flow has been modified"*10, context, "<---------"
        #if context and not context.get('skip_build_attribute_view',False):
        if not self._context.get('skip_build_attribute_view',False):
            self.env['asset.asset'].sudo().update_dummies_view()
            pass

    @api.model
    def create(self, values):
        values = self._remove_reified_attributes(values)
        return super(tracking_flow, self).create(values) 
        self.flow_hasbeen_modified()
 
    @api.multi
    def write(self, values):
        #print 'FOLW-WRITING:',context,
        pprint(values)
        values = self._remove_reified_attributes(values)
        res = super(tracking_flow, self).write(values)
        self.flow_hasbeen_modified()
        return res
    

    @api.multi
    def unlink(self):
        res = super(tracking_flow, self).unlink()
        self.flow_hasbeen_modified()
        return res
 
    def _remove_reified_attributes(self, values):
        """ return `values` without reified group fields """
        add, rem = [], []
        values1 = {}
        visibilities = {}
 
        for key, val in values.iteritems():
            #if is_boolean_attribute(key):
            #    (add if val else rem).append(get_boolean_attribute(key))
#             if is_visibility_id(key):
#                 visibility.setdefault(get_visibility_attribute(key),{})['id'] = val                
            if is_visibility_attribute(key):
                #visibilities.setdefault(get_visibility_attribute(key),{})['visibility'] = val
                visibilities[get_visibility_attribute(key)] = val
                #(add if val else rem).append(get_visibility_attribute(key))
#             elif is_selection_attributes(key):
#                 rem += get_selection_attributes(key)
#                 if val:
#                     add.append(val)
            else:
                values1[key] = val
 
        if 'visibility_ids' not in values and visibilities:
            part_ids = []
            for k,v in visibilities.iteritems():
                code = eval(v or '{}')
                id = code.pop('visibility_id',0)
                v = str(code)
                cmd = id and 1 or 0
                value = {'visibility': v, 'attribute_id': k}
                #cmd = v.has_key('id')  and 4 or 0
                #id = v.get('id',False)
                #value = {'visibility': v.get('visibility','{}'), 'attribute_id': k}
                part_ids.append([cmd,id,value])
            print 'Parx VIs IDs:',
            pprint(part_ids)
            values1['visibility_ids'] = part_ids
#         if 'visibility_ids' not in values and (add or rem):
#             # remove group ids in `rem` and add group ids in `add`
#             values1['visibility_ids'] = zip(repeat(3), rem) + zip(repeat(4), add)
 
        return values1
 
    def default_get0(self, fields):
        attribute_fields, fields = partition(is_reified_attribute, fields)
        fields1 = (fields + ['attributes_id']) if attribute_fields else fields
        values = super(tracking_flow, self).default_get(cr, uid, fields1, context)
        self._add_reified_attributes(attribute_fields, values)
 
        # add "default_groups_ref" inside the context to set default value for group_id with xml values
        if 'groups_id' in fields and isinstance(context.get("default_groups_ref"), list):
            groups = []
            ir_model_data = self.pool.get('ir.model.data')
            for group_xml_id in context["default_groups_ref"]:
                group_split = group_xml_id.split('.')
                if len(group_split) != 2:
                    raise osv.except_osv(_('Invalid context value'), _('Invalid context default_groups_ref value (model.name_id) : "%s"') % group_xml_id)
                try:
                    temp, group_id = ir_model_data.get_object_reference(cr, uid, group_split[0], group_split[1])
                except ValueError:
                    group_id = False
                groups += [group_id]
            values['groups_id'] = groups
        return values
 
    @api.multi
    def read(self, fields=None, load='_classic_read'):
        # determine whether reified groups fields are required, and which ones
        fields1 = fields or self.fields_get().keys()
        attribute_fields, persistent_fields = partition(is_reified_attribute, fields1)
        #print "AALLOHA:",attribute_fields, persistent_fields
        # read regular fields (persistent_fields); add 'groups_id' if necessary
        drop_visibility_ids = False
        if attribute_fields and fields:
            if 'visibility_ids' not in persistent_fields:
                persistent_fields.append('visibility_ids')
                drop_visibility_ids = True
        else:
            persistent_fields = fields
 
        res = super(tracking_flow, self).read(persistent_fields, load) #load for List Mode
 
        # post-process result to add reified group fields
        if attribute_fields:
            for values in (res if isinstance(res, list) else [res]):
                self._add_reified_attributes(attribute_fields, values) # load for Form Mode
                if drop_visibility_ids:
                    values.pop('visibility_ids', None) #per row
        return res
 
    def _add_reified_attributes(self, fields, values):
        """ add the given reified group fields into `values` """
        #gids = set(parse_m2m(values.get('attributes_id') or []))
        vids = values.get('visibility_ids',[]) or []
        print 'VIDS:',vids
        if vids:
            #self.pool['asset.attribute.visibility'].read(cr,uid, vids, ['attribute_id','visibility'])
            visibility = self.env['asset.attribute.visibility'].get_visibility_dict( vids)
            print 'visibilityyyt',
            pprint(visibility)
            for f in fields:
                if is_visibility_attribute(f):
                    #values[f] = visibility.get( get_visibility_attribute(f) , {}).get('visibility','{}')
                    att = visibility.get( get_visibility_attribute(f) , {})
                    if att:
                        vdict = eval(att.get('visibility','{}'))
                        vdict['visibility_id'] = att.get('id',0)
                        values[f] = json.dumps(vdict)
                elif is_visibility_id(f):
                    values[f] = visibility.get( get_visibility_attribute(f) , {}).get('id',0)
#                 elif is_boolean_attribute(f):
#                     values[f] = get_boolean_attribute(f) in gids
#                 elif is_selection_attributes(f):
#                     selected = [gid for gid in get_selection_attributes(f) if gid in gids]
#                     values[f] = selected and selected[-1] or False
 
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(tracking_flow, self).fields_get(allfields, attributes=attributes)
        # add reified groups fields
        # if uid != SUPERUSER_ID and not self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):
        if not self.env.user._is_admin():
            return res
        #for app, kind, gs in self.pool['res.groups'].get_groups_by_application(cr, uid, context):
        for app, kind, gs in self.env['asset.attribute'].get_groups_by_application():
            if kind == 'visibility':
                # selection group field
                #tips = ['%s: %s' % (g.name, g.comment) for g in gs if g.comment]
                for g in gs:                
                    res[name_visibility_attribute(g.id)] = {
                        'type': 'char',
                        'string': g.field_id.field_description,
                        #'selection': [(False, '')] + [(g.id, g.name) for g in gs],
                        #'help': '\n'.join(tips),
                        'exportable': False,
                        'selectable': False,
                    }
                    res[name_visibility_id(g.id)] = {
                        'type': 'integer',
                        'string': g.field_id.field_description,
                        #'selection': [(False, '')] + [(g.id, g.name) for g in gs],
                        #'help': '\n'.join(tips),
                        'exportable': False,
                        'selectable': False,
                    }
            elif kind == 'selection':
                # selection group field
                #tips = ['%s: %s' % (g.name, g.comment) for g in gs if g.comment]
                res[name_selection_attributes(map(int, gs))] = {
                    'type': 'selection',
                    'string': app and app.name or _('Other'),
                    'selection': [(False, '')] + [(g.id, g.name) for g in gs],
                    #'help': '\n'.join(tips),
                    'exportable': False,
                    'selectable': False,
                }
            else:
                # boolean group fields
                for g in gs:
                    res[name_boolean_attribute(g.id)] = {
                        'type': 'boolean',
                        'string': g.field_id.field_description,
                        #'help': g.comment,
                        'exportable': False,
                        'selectable': False,
                    }
        return res
    
#     def copy_data(self, cr, uid, id, default=None, context=None):
#         if default is None:
#             default = {}
#         if context is None:
#             context = {}
#         this = self.browse(cr, uid, id, context=context)
#         tmp_default = dict(default, name=_("%s (Copy)") % this.name)
#         result = super(tracking_flow, self).copy_data(cr, uid, id, default=tmp_default, context=context)
#         print 'FLOW COPYING DATA CUY'
#         pprint.pprint(result)
#         return result

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        tmp_default = dict(default or {}, name=_('%s (copy)') % self.name)
        #return super(Groups, self).copy(default)
        #if context is None:
        #    context = {}
#         context = context.copy()
#         context['skip_build_attribute_view'] = True
#         this = self.browse(cr, uid, id, context=context)
#         tmp_default = dict(default, name=_("%s (Copy)") % this.name)
        user_context = self._context
        user_context['skip_build_attribute_view'] = True
        self = self.with_context(**user_context)
        
        new_id = super(tracking_flow, self).copy(tmp_default)
        self._apply_attributed_fields(id, new_id)
        #del context['skip_build_attribute_view']
        user_context['skip_build_attribute_view'] = False
        self = self.with_context(**user_context) 
        self.flow_hasbeen_modified()
        return new_id
        
        
    def _apply_attributed_fields(self,cr,uid, id, new_id, context):
        o_att = self.env['asset.attribute.visibility']
        #OLD
        oldies = {}
        old = self.browse(cr, uid, id, context=context)
        j = 0
        for i in old.step_ids:
            oldies[i.id] = j 
            j +=1
        print 'oldies',oldies
        
        #NEW 
        newish = []             
        new = self.browse(cr, uid, new_id, context=context)
        j = 0
        for i in new.step_ids:
            #newish[i.id] = j 
            #j +=1
            newish.append(i.id)
        print 'newish:',newish
        for i in new.visibility_ids:
            newvi = {}
            oldvi = eval(i.visibility or '{}') #got {'19': 'readonly', '18': 'readonly', '20': 'readonly'}
            print '   oldvi:',oldvi
            j=0
            for k,v in oldvi.iteritems():   #{'19': 'readonly', '18': 'readonly', '20': 'readonly'}
                k=int(k)
                print "k",`k`,"v:",v
                newj = oldies.get(k)        #index
                if newj < len(newish):
                    newk = newish[newj]
                    newvi[newk] = v
            
            svi = str(newvi)
            o_att.write(cr,uid, i.id, {'visibility': svi}, context=context)
            
            
        
        
        
class tracking_item_view(models.Model):
    _inherit = 'asset.asset'

#     @api.model_cr
#     def init(self):
#         super(tracking_item_view, self).init()
#         self.update_dummies_view()    

#     @api.model
#     def _setup_complete(self):
#         super(tracking_item_view, self)._setup_complete()
#         print '_setup_complete'*100
#         print 'self.conteXt=', self._context
#         self.update_dummies_view()
#     def create(self, cr, uid, values, context=None):
#         res = super(tracking_attributes, self).create(cr, uid, values, context)
#         self.update_tracking_flow_view(cr, uid, context)
#         return res
# 
#     def write(self, cr, uid, ids, values, context=None):
#         res = super(tracking_attributes, self).write(cr, uid, ids, values, context)
#         self.update_tracking_flow_view(cr, uid, context)
#         return res
# 
#     def unlink(self, cr, uid, ids, context=None):
#         res = super(tracking_attributes, self).unlink(cr, uid, ids, context)
#         self.update_tracking_flow_view(cr, uid, context)
#         return res
    @api.model
    def update_dummies_view(self):
        print 'UPDATE-DUMMY-VIEW--'*40
        # the view with id 'base.user_groups_view' inherits the user form view,
        # and introduces the reified group fields
        # we have to try-catch this, because at first init the view does not exist
        # but we are already creating some basic groups
#         if not context or context.get('install_mode'):
#             # use installation/admin language for translatable names in the view
#             context = dict(context or {})
#             context.update(self.pool['res.users'].context_get(cr, uid))
#         #view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'base.user_groups_view', context=context)
#         #view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'sl_asset.asset_asset_form', context=context)
#         view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'sl_asset_attribute.tracking_item_view', context=context)
        if self._context.get('install_mode'):
            # use installation/admin language for translatable names in the view
            
            user_context = self.env['res.users'].context_get()  
            self = self.with_context(**user_context)
        #view = self.pool['ir.model.data'].xmlid_to_object(cr, SUPERUSER_ID, 'base.user_groups_view', context=context)
        #view = self.env['ir.model.data'].sudo().xmlid_to_object('sl_asset_attribute.tracking_flow_attributed_view')
        view = self.env.ref('sl_asset_attribute.tracking_item_view', raise_if_not_found=False)        
        print "vovoview:"*100,view 
        
        if view and view.exists() and view._name == 'ir.ui.view':
            xml1, xml2 = [], []
            #xml1.append(E.separator())#string=_('Attributes'), colspan="2"))
            for att in self.get_attributed_fields(): # all tracking.attribute rows
                attrs = {}
                
                p = att.iplaceholder
                if p:
                    attrs['placeholder'] = p
                
                sattrs = self.get_field_attrs(att.id)
                if sattrs:
                    attrs['attrs'] = sattrs
                print "attaweasers",attrs                
#                 oke_flows = self.get_visible_flow(cr, uid, att.id, context)
#                 print att.field_id.name, oke_flows
#                 if oke_flows:
#                     attrs['invisible'] = "[('flow_id', 'not in', [%s])]" % oke_flows
                xml1.append(E.field(name= att.field_id.name, **attrs))
#             for app, kind, gs in self.get_groups_by_application(cr, uid, context):
#                 # hide groups in category 'Hidden' (except to group_no_one)
#                 attrs = {} # {'groups': 'base.group_no_one'} if app and app.xml_id == 'base.module_category_hidden' else {}
#                 if kind == 'selection':
#                     # application name with a selection field
#                     field_name = name_selection_attributes(map(int, gs))
#                     xml1.append(E.field(name=field_name, **attrs))
#                     xml1.append(E.newline())
#                 else:
#                     # application separator with boolean fields
#                     #app_name = app and app.name or _('Other')
#                     #xml2.append(E.separator(string=app_name, colspan="4", **attrs))
#                     for g in gs:
#                         field_name = name_boolean_attribute(g.id)
#                         xml2.append(E.field(name=field_name, **attrs))
            #
            
            xml = E.field(*(xml1 + xml2), name="dummies", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
            xml_content = etree.tostring(xml, pretty_print=True, xml_declaration=True, encoding="utf-8")
            view.write({'arch': xml_content})
        return True
    
    def parse_visibilities(self, strdict):
        "return: xml.attrs={} input:'{},{}'"
        hascoma = strdict.find('},{') >= 0
        if hascoma:
            visibilities = list(eval(strdict))
        else:
            visibilities = [eval(strdict)]
        visibility = {}
        res = {}
        for d in visibilities:
            visibility.update(d)
        for k,v in visibility.iteritems() :
            res.setdefault(v,[]).append(int(k))
        print 'RRERESESERS',res
        result = ''
        if res:
            attrs={}
            for att in ['required','readonly']:
                if att in res:
                    attrs[att] = [('type_id','in', res[att])]
            invisible = []
            for v in res.itervalues():
                invisible.extend(v)
            attrs['invisible'] = [('type_id','not in', invisible)]
            result = str(attrs)
        return result
#         INX-VISIBLE-ITY: (u"{},{},{'0': 'editable36798'}",)
#         RRERESESERS {'editable36798': [0]}
#         attaweasers {'attrs': "{'invisible': [('type_id', 'not in', [0])]}"}

#         INX-VISIBLE-ITY: (u"{'0': 'editable'},{},{}",)
#         RRERESESERS {'editable': [0]}
#         attaweasers {'attrs': "{'invisible': [('type_id', 'not in', [0])]}"}

#         INX-VISIBLE-ITY: (u"{'0': 'editable'},{}",)
#         RRERESESERS {'editable': [0]}
#         attaweasers {'attrs': "{'invisible': [('type_id', 'not in', [0])]}"}

#         INX-VISIBLE-ITY: (u'{},{}',)
#         RRERESESERS {}
#         attaweasers {}

#         INX-VISIBLE-ITY: (None,)
#         attaweasers {}
            
    def get_field_attrs(self, attribute_id):
        print 'def get_field_attrs(self, attribute_id):=', attribute_id
        #return for xml definition of <field>
        #<field  attrs="{'invisible' : [('type', 'not in', ('integer', 'boolean'))]}"/>
        attrs={}
        #Get Invisible
        #query = '''select string_agg(cast(flow_id as varchar(20)), ',') as flow_id
        #    from tracking_flow_attributes where attribute_id = %s'''
        query = '''select string_agg(visibility, ',') as coder
            from asset_attribute_visibility where attribute_id = %s'''

        self._cr.execute(query, (attribute_id,))
        visibility = self._cr.fetchone()
        print "INX-VISIBLE-ITY:",visibility
        
        if type(visibility) == tuple: #('{1,2}',)
            visibility = visibility[0]
        if visibility:
            return self.parse_visibilities(visibility)
#             hascoma = visibility.find('},{') >= 0
#             if hascoma:
#                 visibilities = list(eval(visibility))
#             else:
#                 visibilities = [eval(visibility)] 
#                 
#             attrs['invisible'] = [('flow_id', 'not in', visibilities)]
        #return attrs and {'attrs':str(attrs)} or {}
        return {}
    
    #@api.model
    def get_attributed_fields(self, domain=None):
        return self.get_application_attributes(domain)
        #gids = self.get_application_attributes(domain)
        #return self.env['asset.attribute'].browse(gids)

    #@api.model
    def get_application_attributes(self, domain=None):
        #return self.search(cr, uid, domain or [])
        return self.env['asset.attribute'].search( domain or [])
    
    def get_groups_by_application(self):
        """ return all groups classified by application (module category), as a list of pairs:
                [(app, kind, [group, ...]), ...],
            where app and group are browse records, and kind is either 'boolean' or 'selection'.
            Applications are given in sequence order.  If kind is 'selection', the groups are
            given in reverse implication order.
        """
        def linearized(gs):
            gs = set(gs)
            # determine sequence order: a group should appear after its implied groups
            order = dict.fromkeys(gs, 0)
            for g in gs:
                for h in gs.intersection(g.trans_implied_ids):
                    order[h] -= 1
            # check whether order is total, i.e., sequence orders are distinct
            if len(set(order.itervalues())) == len(gs):
                return sorted(gs, key=lambda g: order[g])
            return None

        # classify all groups by application
        gids = self.get_application_attributes()
        by_app, others = {}, []
        for g in self.env['asset.attribute'].browse(gids):
#             if g.category_id:
#                 by_app.setdefault(g.category_id, []).append(g)
#             else:
#                 others.append(g)
            others.append(g)
        # build the result
        res = []
        apps = sorted(by_app.iterkeys(), key=lambda a: a.sequence or 0)
        for app in apps:
            gs = linearized(by_app[app])
            if gs:
                res.append((app, 'selection', gs))
            else:
                res.append((app, 'boolean', by_app[app]))
        if others:
            res.append((False, 'boolean', others))
        return res
    