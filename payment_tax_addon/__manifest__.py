{
    'name': 'Payment Tax Addons - 18.0.0.3',
    'version': '18.0.0.1',
    'category': 'Products',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'module_type':'official',
    'App origin': "Base",
    'summary':'Allows to map taxes to payments',
    'depends': ['base','account','alternate_gl','purchase_base_18'],
    'data': [
            'security/ir.model.access.csv',
            'views/payment_tax.xml',
             ],
    'auto_install': False,
    'application': True,
    }
