{
    'name': 'User Restricted Locations',
    'version': '18.0.0.1',
    'category': 'Inventory',
    'summary': 'Restrict user access to specific locations',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'depends': ['base', 'stock'], # We depend on 'stock' for locations
    'data': [
        'security/stock_location_security.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}