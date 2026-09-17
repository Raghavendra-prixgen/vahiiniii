{
    'name': "Sale Approval 18 --version 18.0.1.2",
    'summary': """ """,
    'description': """
        Included Functionalities - 
        1. Approval Sale Order
        """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'category': 'Sale',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'App origin':"Base",
    'depends': ['sale','sale_base_18','user_approval_code'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sales_reject_views.xml',
        'views/sale_approval_view.xml',
    ],
}
