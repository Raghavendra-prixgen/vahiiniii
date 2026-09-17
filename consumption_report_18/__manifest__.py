# -*- coding: utf-8 -*-
{
    'name': 'Consumption Report 18 - 18.0.0.2',
    'version': '18.0.0.1',
    'category': 'Manufacturing',
    'summary': 'Consumption Report 18',
    'App origin':'Base',
    'description': """	""",
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',    

    'depends': ['base','mrp','stock','product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/consumption_report_wizard.xml',
        'views/consumption_report.xml',
    ],
    'installable': True,
    'auto_install': False
}
