{
    'name' : 'IRN and E-way bill',
    'version' : '18.0.0.8',
    'summary': 'Invoices & Payments',
    'description': """ IRN &  E-way bill Generation Gov API    
=======================================
    """,
    'license': 'LGPL-3',
    'module_type':'official',
    'category': 'Integration',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    
    'depends' : ['base', 'account','stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/irn_account_move.xml',
        'views/irn_config_settings.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
