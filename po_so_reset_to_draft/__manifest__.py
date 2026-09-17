{
    'name': "PO SO Rest To Draft - 18.0.0.7",
    'summary': """ """,
    'description': """ """,
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'category': 'Uncategorized',
    'App origin': 'base',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['purchase_approval_18','sale_approval_18','purchase_base_18','sale_base_18'],
    'data': [
        'security/groups.xml',
        'views/po_so_reset.xml',
    ],
}


# sale_approval_18 ==> y_sale_lvl_amt_approval_line
# purchase_approval_18 ==> y_purchase_lvl_amt_approval_line
# purchase_base_18 ==> action_purchase_order_sequence
# sale_base_18 ==> action_sale_order_sequence