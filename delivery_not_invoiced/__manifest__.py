# grn_not_billed/__manifest__.py
{
    'name': "COGS Interim Register(New) - 18.0.0.3",
    'summary': "Report to show Goods Delivered that are Not Invoiced",
    'description': """ """,
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',    
    'category': 'Sales',
    'version': '18.0.0.1', 
    'depends': ['base', 'stock', 'sale', 'account','picking_to_accounts','account_additional_reports'], # Dependencies
    'data': [
        'security/ir.model.access.csv',  # Access rights
        'security/delivery_not_invoiced_security.xml',
        'views/cogs_report.xml',   # Views and menus
    ],
    'installable': True,
    'application': True,              # Mark as an application
    'auto_install': False,
}