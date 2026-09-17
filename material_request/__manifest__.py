{
    'name': "Material Requisition - 18.0.0.5",
    'summary': """
        Material Requisition""",
    'description': """
        1. Creating a transfer for product from destination location to source location
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Customization',
    'origin': 'Base',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base','stock','purchase','purchase_base_18'],
    'data': [
        'security/ir.model.access.csv',
        'security/new_groups.xml',
        'views/material_request.xml',
    ],
}
