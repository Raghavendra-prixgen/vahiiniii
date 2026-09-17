{
    'name': "SO Status Report - 18.0.0.2",
    'summary': """ SO Status Report """,
    'description':"""
        This module is useful to show the sale order lines with status of Delivery and Invoice""",
    'module_type':'official',   
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com', 
    'category': 'Sales',
    'version': '18.0.0.1',
    'App origin':'Base',
    'license': 'LGPL-3',
    'depends': ['sale','sale_stock','sale_base_18'],
    'data': [
        'views/sale_order_line.xml',
    ],
    'auto_install': False,
    'installable' : True,
    'application': True,
}
