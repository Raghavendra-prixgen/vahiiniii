# -*- coding: utf-8 -*-
{
    'name': "Inventory Summary - 18.0.0.9",

    'summary': """
        Inventory Summary""",

    'description': """
        Inventory Summary Report
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'license': 'LGPL-3',

    'category': 'Inventory',
    'version': '18.0.0.1',

    'depends': ['base','product','stock','stock_account','stock_landed_costs','inventory_base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
}
