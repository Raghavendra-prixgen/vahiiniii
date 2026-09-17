# -*- coding: utf-8 -*-
{
    "name": "Sale Order Revision",
    "version": "18.0.0.1",
    'license': 'LGPL-3',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    "summary": """
       Sale Order Revision.
    """,
    "description": """
       Sale Order Revision
    """,
    "origin":"base",
    'module_type':'official',
    "category": "Sale",
    "depends": [
        'base',
        'sale_management'
    ],
    "data": [

        "security/ir.model.access.csv",
        "views/sale_revision.xml",

    ],
    "installable": True,
    "auto_install": False,
}
