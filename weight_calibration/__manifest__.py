# -*- coding: utf-8 -*-
{
    'name': "Weight Calibration 18.0.0.9",

    'summary': """
        Weight Calibration for Base App """,

    'description': """
        This app provides a capability to record the weight of the manufacturing output and compares it with the ideal weight desired
    """,

    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",

    'origin':'Project Specific',
    'category': 'Manufacturing',
    'version': '18.0.0.2',
    'module_type': 'official',

    'depends': ['base','product','stock','mrp','resource'],

    'data': [
        'views/product_template_view.xml',
        'views/mrp_production_view.xml',
        'views/mrp_consumption.xml'
    ],
    
}