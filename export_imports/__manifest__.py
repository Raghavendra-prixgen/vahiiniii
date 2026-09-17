{
    'name': 'Exports Import',
    'version': '18.0.3.5',
    'summary': '',
    'module_type':'official',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'description':"""""", 
    'App origin':"Base",
    'license': 'LGPL-3',
    'depends':['base',
               'account',
               'web',
               'purchase',
               'sale',
               'contacts',
               'mail',
               'l10n_in',
               'delivery',
               'stock',
               'stock_delivery',
               'picking_to_accounts'
            
               ],
    'data':[
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/import_export_fileds.xml',
        'views/import_export_addon.xml',    
        'views/manual_exchange_rate.xml',    

        ],    
}
#picking_to_accounts is added because of get shipment lines button
#import_duty_autocalculation is added because of autocomplete of po in boe.template

