from odoo import fields,api, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    y_is_set_to_draft = fields.Boolean(string="Is Set to Draft",default=False,copy=False)

    def sale_order_action_draft(self):
        for order in self:
            order.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
            })
            order.y_sale_lvl_amt_approval_line.unlink()
            self.y_to_approve_states = 'to_approve_state1'
            order.picking_ids.filtered(lambda x:x.state != 'cancel').action_cancel()
            order.y_is_set_to_draft = True
            order.locked = False

    def action_sale_order_sequence(self):
        for order in self:
            if order.y_is_set_to_draft == False:
                super().action_sale_order_sequence()
            



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    y_is_set_to_draft = fields.Boolean(string="Is Set to Draft",default=False,copy=False)

    def purchase_order_button_draft(self):
        for order in self:
            order.sudo().button_draft()
            order.y_purchase_lvl_amt_approval_line.unlink()
            self.y_to_approve_states = 'to_approve_state1'
            order.picking_ids.filtered(lambda x:x.state != 'cancel').action_cancel()
            order.y_is_set_to_draft = True


    def action_purchase_order_sequence(self):
        for order in self:
            if order.y_is_set_to_draft == False:
                super().action_purchase_order_sequence()