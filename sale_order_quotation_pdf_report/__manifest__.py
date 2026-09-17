# -*- coding: utf-8 -*-
{
    "name": "SALE QUOTATION PDF Report - 18.0.1.6",
    "summary": """ SALE QUOTATION PDF Reports""",
    "description": """
        1. SALE QUOTATION PROJECT ORDER PDF Report.
        2. SALE QUOTATION PDF Report.
                    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "module_type": "official",
    "category": "Sales",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "depends": [
        "base",
        "web",
        "sale",
        "sale_management",
        "l10n_in",
        "alternative_uom",
        "vahini_custom_fields",
        "sale_revision",
        "alternative_uom"
        
    ],
    "data": [
        "reports/quotation_project_order.xml",
        "reports/sale_quotation_report.xml",
    ],
}
