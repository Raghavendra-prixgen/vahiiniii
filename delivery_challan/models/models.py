from odoo import api, fields, models,_

class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'  
    
    def fetch_stp_order(self):
        address = self.env['res.partner']
        if self.y_warehouse_address_id:
            address = self.y_warehouse_address_id
        if not address:
            address = self.company_id.partner_id
        return address