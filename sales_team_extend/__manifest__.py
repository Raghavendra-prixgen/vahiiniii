# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales Team Extend',
    'version': '18.0.0.3',
    'category': '',
    'summary': 'For all',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'description': """
    This module is display the portal user .
    """,
    'depends': ['base','sale','sales_team','crm','mail','account','purchase'],
    'data': [
        # 'security/groups.xml',
        'views/sales_team_extend.xml'
       
    ],
   
   
}
