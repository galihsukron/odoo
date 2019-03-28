# -*- coding: utf-8 -*-

{
    'name': 'Asset Geography Map',
    'version': '1.0',
    'author' : 'SmartLeaders',
    'sequence': 132,
    'depends': ['sl_asset','sl_web_geo'],
    'summary': 'SmartLeaders Asset Management',
    'description': """
This is a full-featured calendar system.
========================================

It supports:
------------
    - asset
    - Geograph location

It should be independent module such some asset management doesn't need RFID Management.
    """,
    'category': 'Smart Leaders',
    #'website': 'https://www.odoo.com/page/crm',
    #'demo': ['calendar_demo.xml'],
    'data': [        
        #'geo_view.xml',
        #'asset_geo_view.xml',
        'views/asset_view.xml',
        'views/location_view.xml',
                
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
