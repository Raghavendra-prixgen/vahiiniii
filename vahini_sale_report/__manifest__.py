# -*- coding: utf-8 -*-
{
    "name": "Sale Order PDF Report-18.0.2.1",
    "summary": """
                Sale Order Report
        """,
    "description": """
            Sale Order Report  
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "module_type": "official",
    "category": "Sale",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "origin": "project Specfic",
    "depends": [
        "base",
        "sale",
        "web",
        "l10n_in",
        "sales_discount",
        "vahini_custom_fields",
        "sale_pdf_quote_builder",
        "inventory_base",
    ],
    "data": [
        "views/hide_std_reports.xml",
        "reports/sale_order_header_footer.xml",
        "reports/sale_order.xml",
    ],
    "installable": True,
    "auto_install": False,
}
