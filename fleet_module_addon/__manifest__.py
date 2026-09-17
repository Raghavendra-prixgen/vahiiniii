# -*- coding: utf-8 -*-
{
    'name': "Fleet Module Addon - 18.0.0.7",
    'summary': """ 
        Fleet Module Addon""",
    'description': """
        Fleet Module Addon
    """,
    'module_type':'official',
    'license': 'LGPL-3',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Base',
    'version': '18.0.0.1',
    'depends': ['purchase',
                'fleet_module_18',
                'vahini_custom_fields'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_module.xml',
    ],
}
