# -*- coding: utf-8 -*-
{
    'name': "Import Duty Auto calculation",
    'summary': """
        Import Duty Auto calculation""",
    'description': """ """,
    'license': 'LGPL-3',
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Customization',
    'version': '18.0.7.4',
    'App origin':'Base',
    'depends': ['base','account','product','purchase','mail','stock','purchase_stock','stock_account','purchase_mrp','stock_landed_costs','purchase_down_payment','export_imports'],

    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'wizard/boe_report_wizard.xml',
        'views/exim_currency_rate.xml',

        # 'views/boe_report.xml',
        'views/import_duty.xml',
        'views/boe_downpayment.xml',

        'views/grn_exchange_rate.xml',
    ],
}

#purchase_down_payment is added because of downpayment
#export_imports is addded because of y_country_orgin_goods_id,y_port_loading_id,y_port_discharge_id


