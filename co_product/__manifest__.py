# -*- coding: utf-8 -*-
{
    'name': "CO PRODUCT - 18.0.0.3",

    'summary': """
        This module is used to capture the Co-Product obtained from the production of Finished Goods
    """,

    'description': """
        This module is used to capture the Co-Product obtained from the production of Finished Goods
    """,
    'module_type':'official',

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "http://www.prixgen.com",
    'license': 'LGPL-3',
    'App origin':'Base',

    'category': 'Manufacturing',
    'version': '18.0.0.1',

    'depends': ['base','mrp'],

    'data': [
        'security/ir.model.access.csv',
        'views/mrp.xml'
    ],
}
