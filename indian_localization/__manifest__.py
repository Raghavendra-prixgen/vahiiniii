{
    'name': "Indian Localization - 18.0.0.5",
    'summary': """  
        Indian Localization""",
    'description': """
        Indian Localization
        GST Code Validations
        Instead of GST code, functionality is based on TIN Number which is same as GST Code
        Journal wise Ceiling limit
    """,
    'module_type':'official',
    'license': 'LGPL-3',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Customization',
    'origin': 'Base',
    'version': '18.0.0.1',
    'depends': ['hr','base','l10n_in'],
    'data': [
        'views/localization.xml',
        'views/view.xml',
        # 'views/hsn_san_list.xml',
    ],
}
