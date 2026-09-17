{
    'name': 'Auto Lot Creation--18.0.0.2',
    'version': '18.0.0.1',
    'category': 'Inventory',
    'summary': 'Automatic Lot Number Generation Based on Configuration',
    'description': """
        This module allows automatic generation of lot numbers based on:
        - Product Category
        - PO Number
        - GRN Number
        - Vendor Reference
        With configurable prefix and sequence size.
    """,
    'depends': ['base', 'stock', 'purchase'],
    'App origin': 'Project Specific',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'data': [
        'security/ir.model.access.csv',
        'views/auto_lot_views.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #       'auto_lot_creation_18/static/src/js/generate_serial_dialog.js'
    #     ],
    # },

    'installable': True,
    'application': False,
    'auto_install': False,
}
