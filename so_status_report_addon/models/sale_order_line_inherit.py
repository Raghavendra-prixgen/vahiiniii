from odoo import fields,models,api, _
from odoo.exceptions import ValidationError

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    
    y_pending_value_after_discount = fields.Float(string='Pending Value')
    y_unit_price_after_discount = fields.Float(compute='compute_discount_unit_price_cal',string="Unit Price",store=True)

    
    @api.depends('qty_delivered','price_subtotal','product_uom_qty')
    def compute_discount_unit_price_cal(self):
        for res in self:
            if res.y_discount_amount and res.y_discount_amount > 0  and res.product_uom_qty > 0 and res.y_remaining_qty > 0:
                res.y_unit_price_after_discount = res.price_subtotal / res.product_uom_qty
                res.y_pending_value_after_discount = (res.price_subtotal/res.product_uom_qty)*res.y_remaining_qty
                # res.y_pending_value_after_discount = (res.price_unit * res.y_remaining_qty) - res.y_discount_amount
                
            else:
                res.y_unit_price_after_discount = res.price_unit
                res.y_pending_value_after_discount = (res.price_unit * res.y_remaining_qty) 
    
