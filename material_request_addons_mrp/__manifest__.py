{
    'name': "Material Requisition Addons Mrp - 18.0.0.4",
    'summary': """Material Requisition Addons Mrp""",
    'description': """
        1. Generate Material request for manufacturing orders 
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'category': 'Customization',
    'origin': 'Base',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base','stock','purchase','mrp','material_request'],
    'data': [
        'views/mrp_material_request.xml',
    ],
}
