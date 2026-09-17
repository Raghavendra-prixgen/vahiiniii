# -*- coding: utf-8 -*-
{
    'name': "Approval Based Partner Credit Limit",

    'summary': """Approval Based Partner Credit Limit """,

    'description': """ """,
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',

    'category': 'Uncategorized',
    'App origin': 'base',
    'version': '18.0.1.3',
    'license': 'LGPL-3',
   
    'depends': ['account','sale','base','sale_base_18','user_approval_code','sale_approval_18'],

    'data': [
         'security/groups.xml',
         'security/ir.model.access.csv',
         'wizard/sales_reject_views.xml',
         'views/sale_partner_credit_limit.xml',
    ],
}


