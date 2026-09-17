{
    'name': 'Analytic Customization - 18.0.1.1',
    'version': '18.0.0.1',
    'summary': 'Analytic Customization',
    'description': """
    Analytic Accounts auto flows covered-
        - SO            ->  DC
        - SO            ->  INV
        - PO            ->  GRN
        - PO            ->  BILL
        - PAY           ->  ACC
        - SO            ->  MO
        - PO            ->  MO
        - MO            ->  PO
        - MO            ->  CHILD MO
        - MO            ->  RAW-PROC
        - TNF(SO/PO/MO) ->  VAL
        - INV-ADJ       ->  VAL
        - EXP           ->  JV
        - EXP           ->  PAY
        - AA-DIST       ->  SO
        - AA-DIST       ->  PO
        - AA-DIST       ->  MO
        - AA-DIST       ->  TNF
    """,
    'depends': ['base',
                'web',
                'sale',
                'stock',
                'account',
                'sale_mrp',
                'analytic',
                'purchase',
                'sale_stock',
                'stock_account',
                'purchase_stock'
                ],
    'category': 'Customization',
    
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "https://www.prixgen.com",
    
    'module_type':'official',
    # 'assets': {
    #     'web.assets_backend': [
    #         'analytic_customization/static/src/components/**/*',
    #     ],
    
    # },


    'data': [
        'views/analytic.xml',
        'views/stock.xml',
        'views/payment.xml',
        'views/mrp.xml',
        ],

    'license': 'LGPL-3',
    

}
