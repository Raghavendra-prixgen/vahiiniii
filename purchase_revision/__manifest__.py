# -*- coding: utf-8 -*-
{
    "name": "Purchase Order Revision",
    "version": "18.0.0.1",
    'license': 'LGPL-3',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    "summary": """
       Purchase Order Revision.
    """,
    "description": """
       Purchase Order Revision
    """,
    "origin":"base",
    'module_type':'official',
    "category": "Purchase",
    "depends": [
        'base',
        'purchase'
    ],
    "data": [

        "security/ir.model.access.csv",
        "views/purchase_revision.xml",

    ],
    
}
