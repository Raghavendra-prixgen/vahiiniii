{
    'name': "Tds Register Report - 18.0.0.9",
    'origin': 'base',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'description':'tds report',
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'installable': True,
    'application': True,
    'depends': ['base','product','account','l10n_in','account_additional_reports','l10n_in_withholding'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/tds_report_view.xml'
        ], 
}


