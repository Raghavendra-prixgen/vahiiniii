{
    'name': "Purchase Approval 18  --version 18.0.1.2",
    'description': """ Purchase approval 18""",
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'App origin': "Base",
    'category': 'Purchase',
    'version': '18.0.0.1',
    'license': 'LGPL-3',

    'depends': ['base','purchase','product','purchase_base_18','user_approval_code'],

    'data': [        
        'security/ir.model.access.csv',
        'wizard/purchase_reject_views.xml',
        'views/purchase_approval_view.xml',
       

    ],
}
