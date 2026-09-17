{
    'name': 'Incoming Shipment Tracker -- version-18.0.0.3',
    'version': '18.0.0.1',
    'module_type':'official',

    'license': 'LGPL-3',
    'category': 'Incoming Shipment Tracker',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'depends': ['base','purchase','mail','web','product','contacts','stock','account','contact_base','sale_stock','purchase_base_18'],
    'data': [
        'security/ir.model.access.csv',
        'security/data.xml',
        # 'views/srl_imports_view.xml',
        'views/views.xml'
    ],
    
    'installable': True,
    'application': False,
}

#contact_base is added because of partner category
