# -*- coding: utf-8 -*-
{
    'name': "Maintenance Integration With Asset ",

    'summary': """
        Maintenance Integration With  Asset""",

    'description': """
        Maintenance Integration With  Aasset.
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'license': 'LGPL-3',
    'category': 'Maintenance',
    'version': '18.0.0.1',

    'depends': ['account_asset','maintenance','maintenance_base'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_assets.xml',
        'views/maintenance_equipment.xml',
        'wizards/genrate_equipment_wiz.xml',
    ],
    # 'qweb': [
    #     "static/src/xml/extended_kanabn_button.xml",
    #     ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'maintenance_integ_with_asset/static/src/js/generate_equipemets.js',
    #         'maintenance_integ_with_asset/static/src/xml/extended_kanabn_button.xml',
    #     ],
    #     'web.assets_qweb': [
    #         'maintenance_integ_with_asset/static/src/xml/extended_kanabn_button.xml',
    #         'maintenance_integ_with_asset/static/src/xml/**/*',
    #     ],
    # },
}
