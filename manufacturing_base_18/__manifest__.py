# -*- coding: utf-8 -*-
{
    'name': "Manufacturing Base Odoo 18 - 18.0.0.5",
    'summary': """Manufacturing Base Odoo 18""",
    'description': """
        Included Functionalities -
        1. Manufacturing product related stock move report
        2. Validation on excess of unbuild MO Qty (mrp.unbuild) 
        3. Reference of sale order & customer to workorder 
        4. Reference of sale order to purchase order & pickings 
        5. Workorder output Qty updatation & Validation on output Qty 
        6. Validation on operations(operation not started)
        7.Work order restriction based on stock availablity 
        8.Logs for MO;unbuild;Scrap;BOM
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'App origin':'Base',
    'category': 'Manufacturing',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['mrp','base','sale','mrp_account_enterprise','mrp_subcontracting','purchase','product','purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/mo_user_validation.xml',
        'views/workcenter_category.xml',
        'views/saleorder_number.xml',
        'views/master_delete_button.xml',
        'views/bom_report.xml',
        'views/purchase_order_view.xml'
    ],
}
