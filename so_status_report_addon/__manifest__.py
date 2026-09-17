{
    'name': "SO Status Report Addon - 18.0.0.4",
    'summary': """ SO Status Report Addon""",
    'description':"""
        """,
        
    'module_type':'official',
       
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com', 
    
    'category': 'Sales',
    'version': '18.0.0.1',
    'App origin':'Project Specfic',
    
    'depends': ['base','sale','sale_stock','sale_base_18','so_status_report','sales_discount'],
    'data': [
        'views/sale_order_line.xml',
    ],
    
    'license': 'LGPL-3',
    'auto_install': False,
    'installable' : True,
    'application': True,
}
