{
    'name': "Purchase Request Approval 18 - 18.0.0.6",
    'description': """ Purchase Request approval 18""",
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
        'wizard/purchase_request_reject_views.xml',
        'views/purchase_request_approval.xml',
       

    ],
}
