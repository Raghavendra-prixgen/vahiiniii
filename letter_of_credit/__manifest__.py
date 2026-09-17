{
    'name': 'Letter of Credit - 18.0.0.5',
    'version': '18.0.0.2',
    'App Origin' : 'Base',
    'description': """This module consists of Cost Field Access""",
    'category': 'product',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'module_type':'official',
    'depends': ['base','product','mail','purchase','sale','account'],
    'data': [
        "security/ir.model.access.csv",
        'data/sequence.xml',
        'views/letter_of_credit.xml',
        'views/expired_date_cron_job.xml',
        
    ],
    
}

