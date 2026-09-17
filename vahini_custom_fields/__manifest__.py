{
    'name': 'Vahini Custom Fields - 18.0.2.1',
    'version': '18.0.0.1',
    'author': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': 'https://www.prixgen.com',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'category': 'Tools',
    'origin' : 'Project Specific',
    'summary': "Module for customized fields. ",
    'depends': ['base','sale','purchase','hr','crm','account','hr','material_request','stock','product','purchase_base_18','web_map','fleet_module_18','picking_to_accounts','crm_base_18','contact_base','account_followup_addon'],
    
    'data': [
             'data/ir_sequence_data.xml',
             'security/ir.model.access.csv',
             'views/account_move_view.xml',
             'views/crm_lead.xml',
           
             'views/mrp_production.xml',
             'views/inventory_config_views.xml',
             'views/material_request.xml',
            
             'views/product_template_view.xml',
             'views/purchase_order_view.xml',
             'views/res_partner_view.xml',
            
             'views/sale_order.xml',
             'views/purchase_request.xml',
             'views/base_inherit.xml',
             'views/custom_fields.xml',
             "views/res_company.xml",
             
             ],
    'auto_install': False,
    'application': True,
}
