# -*- coding: utf-8 -*-
{
    'name': "Entry Type Filter - 18.0.0.2",
    'summary': "",
    'description': """ """,
    'version': "18.0.0.1",
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'category': 'Accounting',

    # any module necessary for this one to work correctly
    'depends': ['base','account','product','stock_account','inventory_base','picking_to_accounts'],

    # always loaded
    'data': [
        'views/document_status.xml',
        ],
    # only loaded in demonstration mode
    'demo': [ ],
}

