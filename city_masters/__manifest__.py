# -*- coding: utf-8 -*-
{
    'name': "Taluk Masters For Vahini",
    
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Taluk For Vahini
    """,

    'module_type':'official',
    'category': 'Address',
    'version': '18.0.0.1',
    'App Origin': 'Project Specific',
    
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',

    'depends': ['base','contacts','sale_management','crm','stock'],

  
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}


