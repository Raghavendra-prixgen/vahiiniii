# -*- coding: utf-8 -*-
{
    "name": "Retail Invoice PDF Report - 18.0.1.2",
    "summary": """
                Retail Invoice Report
        """,
    "description": """
                Retail Invoice Report  
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "module_type":"official",
    "category": "Invoicing",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "origin": "project Specfic",
    "depends": ['account', 'base','l10n_in','vahini_custom_fields',],
    "data": [
        "reports/retail_invoice.xml",
        "reports/head_foot.xml",
    ],
    'installable': True,
    'auto_install': False,
    
}