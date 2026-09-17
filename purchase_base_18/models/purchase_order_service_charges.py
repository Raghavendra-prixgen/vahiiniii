from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import  UserError, ValidationError, AccessError

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_date')
    def _onchange_invoice_date(self):
         for move in self:
            for line in move.invoice_line_ids:
                orders = line.purchase_order_id
                for order in orders:
                    if order and move.invoice_date and order.date_approve and move.invoice_date < order.date_approve.date():
                        raise ValidationError(_('Bill Date Should Not Be Lesser Than Purchase Order Date'))
