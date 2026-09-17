# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM Base 18 - 18.0.0.3',
    'version': '18.0.0.1',
    'summary': 'This apps helps create/generate automatic sequence of lead',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'description':"""
     Automatic Sequance on Lead , Pipeline and Opportunity \n 
     Sequance for Lead ,Opportunity and Pipeline \n
     Auto numbering on lead, Opportunity and Pipeline\n     
     Product Mapping""", 
    'module_type':'official',
    'license': 'LGPL-3',
    'App origin':'Base',
    'depends':['base','sale','crm','sale_crm','sale_management'],
    'data':[
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
        'views/crm_lead2opportunity_view.xml',
        'views/res_partner.xml',
        ],
    'installable': True,
    'auto_install': False,
}

