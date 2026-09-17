{
    'name': 'GRN Posting Date Control - 18.0.0.2',
    'version': '18.0.0.1',
    'category': 'Inventory',
    'summary': 'Control the posting date for Goods Receipt Notes (GRN)',
    'depends': ['stock_account','purchase_stock'], # Depends on stock_account for valuation and accounting integration
    'module_type':'official',
    'category': 'Inventory',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'data': [
        'security/grn_security.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}