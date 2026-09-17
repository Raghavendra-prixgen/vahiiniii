{
    'name': "Purchase Base 18 -- version 18.0.2.3",
    'description': """
        Included Functionalities - 

        1. Document type
        2. Sequence for Document Type
        3. Product Souring
        4. Purchase Charges 
        5. Purchase gross amount
        6. Purchase tolerance
        7. Purchase Unit Of Measure
        8. Purchase Order Routing
        9. Purchase Request
        10. Purchase Advance Payment
        11. Purchase Short Close
        12. Purchase Receipt to Bill
        13. Merge Purchase Order
        14. Split Purchase Order
    """,
    'module_type':'official',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'App origin': "Base",
    'category': 'Purchase',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': ['base','purchase','product','purchase_requisition_stock','sale_management','stock_landed_costs','account','stock','mail','purchase_stock','purchase_requisition'],
    'data': [
        "data/purchase_request_sequence.xml",
        "data/purchase_request_data.xml",

        "security/purchase_request.xml",
        "security/ir.model.access.csv",

        'views/purchase_order_view.xml',
        'views/stock_location_route_view.xml',
        'views/purchase_doc_type_views.xml',
        'views/purchase_tolerance_view.xml',
        'views/product_sourcing.xml',
        'views/active_view.xml',
        'views/incoterm.xml',
        "reports/report_purchase_request.xml",
        "wizard/purchase_request_line_make_purchase_order_view.xml",
        "views/purchase_request_view.xml",
        "views/purchase_request_line_view.xml",
        "views/purchase_request_report.xml",
        "views/purchase_order_request_view.xml",
        "views/request_type.xml",

        'wizard/purchase_short_close_wizard.xml',
        'views/purchase_short_close.xml',

        'views/blanket_order.xml',
        'views/purchase_request_short_close.xml',
        'views/product_procurement_group.xml',
        'views/purchase_order_discount.xml',
        'views/res_partner.xml',


    ],
    'installable' : True,
	'auto_install': False,

}
