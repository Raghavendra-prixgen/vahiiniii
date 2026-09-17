# -*- coding: utf-8 -*-
{
    'name': "Purchase Down Payment - 18.0.0.5",

    'summary': " ",

    'description': """  """,

    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',

    'category': 'Purchase',
    'version': '18.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        "data/down_payment_request_sequence.xml",
        "security/purchase_request.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        'views/advance_request_form.xml',
        'views/purchase_form_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [  ],
}

