# -*- coding: utf-8 -*-
{
    "name": "Purchase Order PDF Report-18.0.1.2",
    "summary": """
                Purchase Order Report
        """,
    "description": """
            Purchase Order Report  
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "module_type": "official",
    "category": "Purchase",
    "module_type": "official",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "origin": "project Specfic",
    "depends": [
        "base",
        "purchase",
        "web",
        "l10n_in",
        "vahini_custom_fields",
    ],
    "data": [
        "reports/purchase_order.xml",
        "views/header_foot.xml",
    ],
    "installable": True,
    "auto_install": False,
}
