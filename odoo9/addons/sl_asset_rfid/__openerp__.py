# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Asset RFID',
    'version': '1.0',
    'author' : 'SmartLeaders',
    'sequence': 132,
    'depends': ['base', 'sl_asset'],
    'summary': 'SmartLeaders Asset Management',
    'description': """
This is a full-featured calendar system.
========================================

It supports:
------------
    - RFID asset
    - RFID location

It should be independent module such some asset management doesn't need RFID Management.
    """,
    'category': 'Smart Leaders',
    #'website': 'https://www.odoo.com/page/crm',
    #'demo': ['calendar_demo.xml'],
    'data': [        
        'rfid_view.xml',
                
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
