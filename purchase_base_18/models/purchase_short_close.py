from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo import SUPERUSER_ID, _, api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order" 

    def short_close_form_wizard(self):
        po_lines=self.order_line.filtered(lambda line: line.y_is_short_close == False and line.product_qty != line.qty_received)            
        if self.state in ['purchase','done'] and po_lines:    
            return {
                'name': ("Purchase Short Close Wizard"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.short.close.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('purchase_base_18.view_purchase_short_close_wizard_form').id, 'form')],
                'target': 'new',                
                'context': dict(self._context,default_y_purchase_id=self.id,default_sc_po_lines_ids = po_lines.ids)
            }
        elif self.state not in ['purchase','done']:
            raise UserError(_('Purchase Short Close can be processed only if the Order is in Purchase Order State!'))

    y_is_po_short_close = fields.Boolean(copy=False,string="Short Close")

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    y_is_short_close = fields.Boolean(string='Short Close',copy=False)
    y_short_close_description = fields.Char(string='Short Close Reason',copy=False)
    y_short_close_reason_id = fields.Many2one('purchase.short.close.reason',string='Short Close Reasons',copy=False)

class StockMove(models.Model):
    _inherit = "stock.move"

    y_is_freeze = fields.Boolean(copy=False)