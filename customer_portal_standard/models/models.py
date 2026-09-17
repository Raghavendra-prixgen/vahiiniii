from odoo import models, fields, api, _


    
class ProductProduct(models.Model):
    _inherit = "product.product"

    y_product_portal_boolean = fields.Boolean(string='Product Portal Visibility', help='Enable visibility in the customer portal')
    

    
class ProductTemplate(models.Model):
    _inherit = "product.template"

    y_product_portal_boolean = fields.Boolean(string='Product Portal Visibility', help='Enable visibility in the customer portal')

class ProductCategory(models.Model):
    _inherit = "product.category"

    y_company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.company.id,help='Select the company associated with this product category.')


    
    