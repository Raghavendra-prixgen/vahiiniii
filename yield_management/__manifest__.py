{
    'name': 'Manufacturing Report -18.0.0.1 ',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'summary': """
        Yield Management Report""",
    'description': """ This module consists, of the To Consume and Consumed qunatity in Manufacturing Order  """,
    'category': 'Manufacturing',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'depends': ['mrp','web','manufacturing_base_18','base','product','purchase','lot_purchase_cost'],
    'App origin': "Project Specific",
    'module_type':'official',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/mrp_report.xml',
        'wizard/prix_mrp_report_wizard.xml',
        'data/yield_management_email.xml',
        
    ],
   

    'assets': {
        'web.assets_backend': [
            'yield_management/static/src/xml/production_analytics_templates.xml',  # Single XML file
            'yield_management/static/src/js/production_analytics_dashboard.js',   # Single JS file
            'yield_management/static/src/css/production_analysis.scss',   # Single css file
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
}