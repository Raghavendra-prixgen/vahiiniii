# -*- coding: utf-8 -*-
{
    'name': "Job Work Challan report Template(maintenance)",
    
    'summary': """
        This module consists, the Job Work Challan Templates""",

    'description': """
        This module consists, the Job Work Challan Templates
    """,

    'module_type':'official',
    'category': 'maintenance',
    'version': '18.0.0.4',
    'App Origin': 'Project Specific',
    
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',

    'depends':['base','purchase','l10n_in','web','maintenance_base','maintenance_integ_with_purchase'],
  
    'data': [
        'report/job_work_challan.xml',
        'views/header_footer.xml',
        'views/maintenance_request_extra.xml'
    ],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}


