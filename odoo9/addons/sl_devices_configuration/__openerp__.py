# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Devices Configuration',
    'version': '3.0',
    'author' : 'SmartLeaders',
    #'website': "http://smart-leaders.net",    
    'sequence': 130,
    'depends': ['base','sl_asset'],
    'summary': 'To control devices configuration',
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
    #'demo': ['data/asset_demo.xml'],
    'data': [
        'views/devices_configuration_view.xml'
        
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
