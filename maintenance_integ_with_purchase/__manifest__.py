# -*- coding: utf-8 -*-
{
    'name': "Maintenance Integration With Purchase",

    'summary': """Maintenance Integration With Purchase """,

    'description': """Maintenance Integration With Purchase.""",

    'version': '18.0.0.3',
    
    'module_type':'official',
    
    'App Origin': 'Project Specific',
    
    'category': 'Maintenance',
    
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    
    'website': "https://www.prixgen.com", 

    'depends': ['purchase','maintenance_base','purchase_base_18','maintenance'],

    'data': [
        'views/purchase.xml',
        'views/maintenance_request.xml'
    ],
    
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
