# -*- coding: utf-8 -*-
{
    "name": "Invoice PDF Report-18.0.2.6",
    "summary": "Invoice Order Report",
    "description": "Invoice Order Report",
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "category": "Purchase",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "app_origin": "project specific",
    "depends": [
        "account",
        "web",
        "l10n_in",
        "e_invoice_masters_branch-odoo18",
        "sales_discount",
    ],
    "data": [
        "data/record_creation.xml",
        'security/ir.model.access.csv',
        "reports/irnhf.xml",
        "reports/irn.xml",
    ],
}
