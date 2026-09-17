from odoo import models, fields, api, _, exceptions

class SaleOrderLines(models.Model):
    _inherit = "sale.order.line"

    y_product_total_weight = fields.Float("Total Weight")

    @api.onchange('product_id','product_uom_qty')
    def update_total_weight(self):
        for each_line in self:
            if each_line.product_id and each_line.product_uom_qty:
                each_line.y_product_total_weight = each_line.product_id.weight *  each_line.product_uom_qty
            else:
                each_line.y_product_total_weight =0.0

    