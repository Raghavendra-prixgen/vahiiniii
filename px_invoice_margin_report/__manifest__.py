# -*- coding: utf-8 -*-
{
    'name': "Invoice Margin Report   - 18.0.0.6",

    'summary': "The Invoice Margin Report provides a detailed analysis of product margins per invoice",

    'description': """  The invoice Margin Report provides a detailed analysis of product margins per invoices for  within a specified date range.
                        It calculates the profitability of each product, helping businesses make informed decisions about product performance, 
                        stock usage, and margin efficiency.
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",

    'category': 'Account',
    'version': '18.0.0.0',

    'depends': ['base','account','picking_to_accounts','fleet_module_18','account_additional_reports','vahini_custom_fields'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_margin_report_wizard_view.xml',
        'views/invoice_margin_report_views.xml',
    ],
}

