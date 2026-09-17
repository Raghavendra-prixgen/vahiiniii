{
    'name': "Subcon Register Report - 18.0.0.1",
    'summary': """
            Subcon Register Report
        """,
    'description': """
        Subcon Register Report
        """,
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'module_type':'official',
    'category': 'Purchase',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'App origin':"Base",
    'depends': ['base','purchase','web','stock','purchase_stock','mrp_subcontracting_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/subcon_register_report_views.xml',
    ], 
}
