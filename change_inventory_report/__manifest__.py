# -*- coding: utf-8 -*-
{
    'name': "Change Inventory Report",
    'summary': "Change Inventory Report - Production Cost Account Move Analysis",
    'description': """
        Change Inventory Report
        =======================
        - Lists journal items linked to property_stock_account_production_cost_id
        - Groups by MRP Production (MO) reference when stock valuation layers exist
        - Falls back to journal item name when no valuation layer
        - Filters by date range and company/branch
        - Parent company includes all child company data
    """,
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'license': 'LGPL-3',
    'category': 'Inventory',
    'version': '18.0.0.2',
    'depends': ['base', 'product', 'stock', 'stock_account', 'mrp','account_additional_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/change_inventory_wizard_views.xml',
        'views/change_inventory_report_views.xml',
        'views/menus.xml',
    ],
}
