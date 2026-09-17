# -*- coding: utf-8 -*-
{
    'name': "Gate Management - 18.0.1.5",

    'summary': """
        Gate Management with Transfer""",

    'description': """
        The intent of the app is to record the details of the vehicle which has entered/exited the warehouse premises.
        Contains details such as vehicle number, Date, PO/SO/other document details,  etc.
        Without doing the Gate Management process, it will not be possible to either do GRN or Delivery operations.
    """,
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': "https://www.prixgen.com",
    'category': 'Custamization',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'stock', 'purchase', 'sale', 'sale_stock','purchase_stock','fleet','picking_to_accounts'],
    'data': [
        'data/sequence.xml',
        # 'views/assets.xml',
        'security/ir.model.access.csv',
        'security/access_entries.xml',
        'data/group_entry_type_data.xml',
        'data/gate_management_group_access.xml',
        'views/gate_management.xml',
        'views/gate_management_user.xml',
        'views/stock_picking.xml',
        'views/purchase_order.xml',
        'report/header_footer.xml',
        'report/gate_management_report.xml',
        # 'views/res_config_settings.xml',
    ],
    'images': ['images/icon1.png'],

    'installable': True,
    'auto_install': False,
    'application': True,

    # 'css': ['static/src/scss/kanban_dashboard.scss'],
}
