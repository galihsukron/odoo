# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Asset Shipment',
    'version': '1.0',
    'author' : 'SmartLeaders',
    'sequence': 931,
    'depends': ['sl_asset',
                 #image on tree
                ],
    'summary': 'SmartLeaders Synchronization',
    'description': """
This is a full-featured calendar system.
========================================

It supports:
------------
    - Calendar of events
    - Recurring events

If you need to manage your abc features, you should install the XYZ module.
    """,
    'category': 'Smart Leaders',
    'license': 'Other proprietary',
    #'website': 'https://www.odoo.com/page/crm',
    #'demo': ['calendar_demo.xml'],
    'data': [
        #'security/asset_security.xml',
        #'security/ir.model.access.csv',
        #'asset_root_menu.xml',        
        #'asset_view.xml',
        'shipment_view.xml',
        'pic_transfer_view.xml',
        'mail.thread.xml',
        #'asset_data.xml',
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
