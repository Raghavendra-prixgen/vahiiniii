# -*- coding: utf-8 -*-
{
    'name': "Purchase Analysis Report - 18.0.0.1",

    'summary': """
        """,

    'description': """
        This Module Create new submenu under purchase analysis reporting in the name of Purchase Analysis Report.
        Providing form view and wizard for purchase register.
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",

    'category': 'Purchase',
    'version': '18.0.0.1',

    'depends': ['base','account','purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_report_wizard.xml',
        'views/purchase_report.xml',
        'views/purchase_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
