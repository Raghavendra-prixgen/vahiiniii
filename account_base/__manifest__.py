{
    'name': "Account Base",
    'summary': """""",
    'description': """
        Included Functionalities -
            1) Sequence field in Journal masters picked by Sale Invoices for custom sequence
            2) Override Sequence Mixin to avoid date validation error
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",    
    'category': 'Account',
    'App Origin': 'Base',
    'version': '18.0.3.0',
    'license': 'LGPL-3',
    'depends': ['base','account','account_reports'],
    'data': [
        'views/account_journal.xml',
        'views/res_config_settings.xml',
        'views/gl_code_type.xml',
    ],

    'auto_install': False,
    'installable': True,
}

