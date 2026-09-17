{
    'name': 'PO Status Report - 18.0.0.3',
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'version': '18.0.0.1',
    'category': 'Purchase',
    'summary': 'This module is useful to show the purchase order lines with status of GRN and Invoice',
    'description': """This module is useful to show the purchase order lines with status of GRN and Invoice""" ,
    'App origin':'Base',
    'depends': ['purchase','purchase_base_18','purchase_stock'],    
    'data': [
        'views/purchase_order_line.xml',
    ],
    
    'auto_install': False,
    'installable' : True,
    'application': True,
}
