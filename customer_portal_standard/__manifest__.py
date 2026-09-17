# -*- coding: utf-8 -*-
{
    "name": "Customer order placement standard - Portal - 18.0.0.4",
    "summary": "Portal users can create quotation from quotation portal.",
    "description": """
        1. Portal users can create quotation from quotation.
        2. User can add quantity, packaging quantities, packaging types and price details for the products.
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "category": "Portal",
    "origin":"base",
    'module_type':'official',
    "version": "18.0.0.1",
    "depends": [
        "base",
        "product",
        "web",
        "website",
        "sale_management",
        "portal",
    ],
    "data": [
        "security/portal_user_groups.xml",
        "views/quotation_template.xml",
        "views/product_template.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "customer_portal_standard/static/src/js/portal_quote.js",
            "customer_portal_standard/static/src/js/portal_package.js",
            "customer_portal_standard/static/src/js/resize_table.js",
            "customer_portal_standard/static/src/scss/portal_quotation.scss",
            "customer_portal_standard/static/src/scss/portal_catalogue.scss",
            "customer_portal_standard/static/src/scss/portal_package.scss",
        ],
    },
}
