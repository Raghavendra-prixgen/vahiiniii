# -*- coding: utf-8 -*-
{
    'name': "Maintenance Base Odoo 18",

    'summary': """
        Maintenance Base consist of stages equipments also contains the job work stage and sequence for maintenance base """,

    'description': """
        Maintenance Base consist of stages equipments also contains the job work stage and sequence for maintenance base 
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'license': 'LGPL-3',
    'category': 'Maintenance',
    'version': '18.0.0.7',

    'depends': ['base','maintenance','stock','web'],
    'module_type':'official',


    'data': [
        'security/ir.model.access.csv',
        'data/maintenance_seq.xml',
        'views/maintenance.xml',
        'views/sub_categories.xml',
        'views/equipment_request.xml',
        'reports/jobwork_challan.xml',
        'views/equipment_request_delivery.xml',
        'views/equipment_request_receipt.xml',
        'views/equipment_allocation_views.xml',
        'wizard/service_backorder.xml',

    ],
}


