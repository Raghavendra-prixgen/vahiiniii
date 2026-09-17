# grn_not_billed/__manifest__.py
{
    'name': "GRN Not Billed Report - 18.0.0.2",
    'summary': "Report to show Goods Receipt Notes (GRN) that are Not Billed",
    'description': """
        This module adds a report to list all GRNs (Goods Receipt Notes) 
        that have been received but **NOT yet billed**.
    """,
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',    
    'category': 'Purchases',
    'version': '18.0.0.1', 
    'depends': ['base', 'stock', 'purchase', 'account','picking_to_accounts','account_additional_reports'], # Dependencies
    'data': [
        'security/ir.model.access.csv',  # Access rights
        'security/grn_not_billed_security.xml',
        'views/grin_report_views.xml',   # Views and menus
    ],
    'installable': True,
    'application': True,              # Mark as an application
    'auto_install': False,
}