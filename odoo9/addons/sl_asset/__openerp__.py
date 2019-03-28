# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Asset',
    'version': '3.0',
    'author' : 'SmartLeaders',
    #'website': "http://smart-leaders.net",    
    'sequence': 130,
    'depends': ['base', 'decimal_precision', 'mail', 'base_action_rule', 'web_calendar'],
    'summary': 'SmartLeaders Asset Management',
    'description': """
This is a full-featured calendar system.
========================================

It supports:
------------
    - Calendar of events
    - Recurring events

If you need to manage your meetings, you should install the CRM module.
    """,
    'category': 'Smart Leaders',
    #'website': 'https://www.odoo.com/page/crm',
#    'demo': ['data/asset_demo.xml'],
    'data': [
        'security/asset_security.xml',
        'security/ir.model.access.csv',
        'data/precision.xml',
        'views/asset_root_menu.xml',        
        
        'views/asset_view.xml',
        'views/state_view.xml',
        'views/location_view.xml',
        'views/movement_view.xml',
        'views/move_party_view.xml',
        'views/type_view.xml',
        'report/asset_distribution_report_view.xml',
        'views/asset_data.xml',
        'views/res_config_view.xml'
        
    ],
    'qweb': ['static/src/xml/*.xml'],
    'test': [
        #'test/calendar_test.yml',
        #'test/test_calendar_recurrent_event_case2.yml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
