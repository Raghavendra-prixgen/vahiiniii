# -*- coding: utf-8 -*-
{
    'name': "Fleet Module 18 -- version-18.0.3.6",
    'summary': """  
        Fleet Module 18""",
    'description': """
        Fleet Module 18
    """,
    'module_type':'official',
    'license': 'LGPL-3',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Base',
    'version': '18.0.0.4',
    'depends': ['base',
                'web',
                'fleet',
                'stock',
                'mail',
                'web_map',
                'inventory_base',
                'account',
                'product',
                'sale',
                'sale_stock',
                'stock_fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/transportation_order.xml',
        'views/vehicle_intent.xml',
        'views/fleet_module.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fleet_module_18/static/src/components/vehicle_intent_state_selection/vehicle_intent_state_selection.js',
            'fleet_module_18/static/src/components/vehicle_intent_state_selection/vehicle_intent_state_selection.xml',
            'fleet_module_18/static/src/components/vehicle_intent_state_selection/vehicle_intent_state_selection.scss'
        ],
       
    },
}

#inventory_base is added because of y_release field added in xml for domain purpose
#landed_cost_automated is added because of landed cost creation
