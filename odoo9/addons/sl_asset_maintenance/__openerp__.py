# -*- coding: utf-8 -*-

{
    'name': 'Asset Maintenance',
    'version': '1.0',
    'author' : 'SmartLeaders',
    'sequence': 132,
    'depends': ['base', 'sl_asset'],
    'summary': 'SmartLeaders Asset Management',
    'description': """
This is a basic assset maintenance.
========================================

It supports:
------------
    - Asset Condition


It should be independent module such some assets aren't repairable.
    """,
    'category': 'Smart Leaders',
    #'website': 'https://www.odoo.com/page/crm',
    'demo': ['data/asset_demo.xml'],
    'data': [        
        'data/maintenance_states.xml',  # bekal: working, under maintenance, broken
        'views/asset_view.xml',
                
    ],
    #'qweb': ['static/src/xml/*.xml'],
    'test': [
        #'test/calendar_test.yml',
        #'test/test_calendar_recurrent_event_case2.yml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
