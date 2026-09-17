# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('requisition_id')
    def _onchange_incoterm_id(self):
        if self.requisition_id:
            self.y_purchase_request_number = self.requisition_id.y_purchase_request_id.name
            
class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    y_purchase_request_id = fields.Many2one('purchase.request',string="Purchase Request")

    @api.onchange('y_purchase_request_id')
    def _onchange_purchase_request_id(self):
        if not self.y_purchase_request_id:
            return

        self = self.with_company(self.company_id)
        requisition = self.y_purchase_request_id
        self.write({'company_id': requisition.company_id.id,
                    'currency_id': requisition.currency_id.id,
                    'reference': requisition.name,
                    'user_id': requisition.requested_by.id,})

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context(lang=self.env.user.lang)
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.estimated_cost, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.estimated_cost
                
            # Create PO line
            order_line_values = line._prepare_blanket_order_line(
                name=name, product_uom =line.product_uom_id, product_qty=product_qty, price_unit=price_unit,
                product_id = line.product_id,po = self.id)
            order_lines.append((0, 0, order_line_values))
        self.line_ids = order_lines
