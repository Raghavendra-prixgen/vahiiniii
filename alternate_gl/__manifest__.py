{
    'name': "Alternate GL -version 18.0.0.5",
    'summary': """Alternate GL  """,
    'description': """Alternate GL""",
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': "https://www.prixgen.com",
    'category': 'Accounting',
    'App origin': "Base",
    'module_type':'official', 
    'version': '18.0.0.1',
    'depends': ['account','account_accountant','account_asset','internal_transfer'],
    'data': [
        'security/ir.model.access.csv',
        'views/alt_gl.xml',
        'views/account_payment.xml'
    ],
}
