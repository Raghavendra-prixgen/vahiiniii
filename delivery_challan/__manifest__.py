# -*- coding: utf-8 -*-
{
    "name": "Delivery Challan Report - 18.0.0.9",
    "summary": """
                Delivery Challan Report
        """,
    "description": """
             Delivery Challan Report  
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "category": "Delivery Challan",
    "version": "18.0.0.1",
    "module_type":"official",
    "license": "LGPL-3",
    "App origin": "project Specfic",
    "depends": ["base", "purchase","web","l10n_in"],
    "data": [
        "reports/delivery_challan.xml",
        "views/header_footer.xml",
    ],
    'installable': True,
    'auto_install': False,
   
}
