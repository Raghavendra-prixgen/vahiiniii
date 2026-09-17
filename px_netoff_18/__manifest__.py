# -*- coding: utf-8 -*-
{
    'name': "Netoff Odoo 18.0.0.5",

    'summary': """
        Netoff Odoo 18""",

    'description': """
        Netoff Odoo 18
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",

    'category': 'Accounting',
    'version': '18.0.0.0',

    'depends': ['account','account_accountant'],

    'data': [
        'views/net_off_setting.xml',
        'views/res_partner.xml',
        'views/account_move.xml'
    ],
}
