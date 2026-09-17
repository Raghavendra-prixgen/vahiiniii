# -*- coding: utf-8 -*-
{
    "name": "Partner Ledger in portal 18.0.0.3",
    "summary": "Portal users can view partner ledger in portal",
    "description": """ """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "category": "Portal",
    "version": "18.0.0.1",
    "depends": [
        "base",
        "web",
        "website",
        "account",
        "portal",
    ],
    "data": [
        "security/groups.xml",
        "views/partner_ledger_portal_template.xml",
        "reports/partner_ledger_report.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "partner_ledger_portal/static/src/js/partner_ledger.js",
            "partner_ledger_portal/static/src/css/partner_ledger.scss",
        ],
    },
}
