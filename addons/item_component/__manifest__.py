# -*- coding: utf-8 -*-
{
    'name': "Master Komponen Item",

    'summary': """
        Master Komponen Item""",

    'description': """
        Master Komponen Item
    """,

    'author': "Galih",
    'website': "http://www.yourcompany.com",
    'category': 'Component',
    'version': '11.0.1',    
    'depends': ['base','base_import'],    
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/item_component.xml',
        
    ],
    'qweb' : ['static/src/xml/custom_import.xml'],    
    'demo': [
        'demo/demo.xml',
    ],
}