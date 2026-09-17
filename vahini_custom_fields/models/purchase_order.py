from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    y_delivery_schedule = fields.Date(string="Delivery Schedule")
    
    y_place_of_delivery=fields.Char(string="Place of Delivery")
    y_remark=fields.Text('Remark')
    
   