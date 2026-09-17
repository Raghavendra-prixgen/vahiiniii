{
    "name": "E-Invoicing Masters-18.0.0.8",
    "version": "18.0.0.1",
    "summary": "E-Invoicing Masters",
    "description": """
Invoicing & IRN
====================
E-Invoicing Masters for branch wise

    """,
    'license': 'LGPL-3',
    'module_type':'official',
    "category": "Accounting/Accounting",
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    'App origin':'Project Specific',
    "website": "https://www.prixgen.com",
    "depends": [
        "base",
        "account_accountant",
        "sale",
        "account_irn-odoo18",
        "foc"
    ],
    "data": [
        "views/e_invoice_master_view.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}

#foc is added because of y_is_free_of_charge_visible field