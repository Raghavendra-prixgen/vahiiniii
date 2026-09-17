# -*- coding: utf-8 -*-
{
    'name': "Manufacturing tolerance--18.0.0.6",
    'summary':"""Manufacturing tolerance on products""",
    'description': """Manufacturing tolerance on products""",
    'category': 'Manufacturing',
    'origin':'Project Specification',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'depends': ['base','account','product','stock','mrp','user_approval_code','weight_calibration'],
    'data': [ 
            'security/ir.model.access.csv',
            'views/manufacturing_tolerance_view.xml',
            'wizard/mo_tolerance_views.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
