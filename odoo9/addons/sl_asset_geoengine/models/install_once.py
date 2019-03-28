# -*- coding: utf-8 -*-

we_want_to_remove = '''
/* Mobile view */
@media (max-width: 768px) {
  img:not(.cke_iframe), .media_iframe_video, span.fa, i.fa {
    -webkit-transform: none !important;
    -moz-transform: none !important;
    -ms-transform: none !important;
    -o-transform: none !important;
    transform: none !important;
  }
}
'''

import os
from openerp.osv import osv
from openerp.modules import module

FIRST_LINE_WRONG_CSS = "/* Mobile view */"

def _sc_fixup_web_editor_img_css():
    "This function run in source code level, so any db will applied globally"
    css_path = module.get_resource_path('web_editor','static','src','css', 'web_editor.css')
    if os.path.isfile(css_path):
        with open(css_path,"r+") as fp:
            lines= fp.readlines() #SAFER WAY TO READ
            
        fixup_needed = False
        final = []
        closing_bracket = 0
        for line in lines:
            #print `line`
            if line.strip('\n') == FIRST_LINE_WRONG_CSS:
                fixup_needed = True
                closing_bracket = 2
            elif closing_bracket:
                if line.strip() == '}':
                    closing_bracket -= 1
            else:
                final.append(line)
            
        if fixup_needed:
            print 'FINAL: FIXUP IS NEEDED! >>'#, final
            with open(css_path,"w") as fp:
                for line in final:
                    fp.write(line)
        #        lines= fp.readlines() #SAFER WAY TO WRITE
        
class Module(osv.osv):
    _inherit = "ir.module.module"
    
    #@api.multi
    #def _install_web_icon_fa_menus(self):        
    def _fixup_web_editor_img_css(self, cr, uid, ids=None, context=None):
        ''' 
            This function will be called when THIS MODULE was installed. 
            Purpose: allowing images in map-tiles to do CSS transformation,
            which may been prevented by web_editor by forcing image transformation to none. 
        '''
        
        installed_web_editor = self.search(cr, uid, [('name', '=', 'web_editor'), ('state', 'in', ['installed','to upgrade','to install'] )])
        
        if installed_web_editor :
            _sc_fixup_web_editor_img_css()
                
            

        
    