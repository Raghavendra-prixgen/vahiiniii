{
    'name': "Branch To Branch Transfer Order - 18.0.3.1",
    'summary': """
        This module is used for transferring materials between one branch to another branch.
        """,
    'description': """
        This module is used for transferring materials between one branch to another branch.
    """,
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'category': 'Uncategorized',
    'App Origin': 'Base',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base','stock','account','stock_account','stock_landed_costs','picking_to_accounts'],
    'data': [
        'data/btb_sequence.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/branch_to_branch_config.xml',
        'views/branch_to_branch.xml',
        'views/stock.xml',
        'views/stock_location.xml',
    ],
    'post_init_hook': 'post_init_hook',
}

# BTB LOT Domain:
# ===============
# ['|', ('location_id', '=', False), ('company_id', 'in', company_ids + [False])]