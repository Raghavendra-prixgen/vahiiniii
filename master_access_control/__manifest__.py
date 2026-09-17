
{
    'name': "Master Access Control--18.0.0.2",
    'version': '18.0.0.1',
    'module_type':'official',
    'category': 'Master Access Control',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'depends': ['base','web'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/access_models_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'master_access_control/static/src/**/*',
        ],

    },
    

}

