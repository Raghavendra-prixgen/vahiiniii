{
    'name': 'Sales Discount - 18.0.2.5',
    'version': '18.0.0.1',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'category': 'Sales',
    'summary': 'Discount in sales',
    'App origin':"Project Specific",
    'description': """ """,
    'depends': ['sale_management','sale','inventory_base','stock','account','picking_to_accounts','alternative_uom','sale_base_18'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_discount_structure.xml',
        # 'views/sale_discount.xml',
        'views/sale_order.xml',
        'views/irn_config_settings.xml',
        'views/account_invoice.xml',
        
    ],
    'installable': True,
    'auto_install': False,
}

#picking_to_accounts(y_stock_move_id) is added because of validation wheather get picking is done or not