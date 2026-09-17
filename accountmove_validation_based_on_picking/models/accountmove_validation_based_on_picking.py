from odoo import fields,models,api, _
from datetime import date, timedelta
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        for rec in self:
            picking_datetime = rec.invoice_line_ids.mapped('y_stock_picking_ref').mapped('date_done')
            picking_date = [d.date() for d in picking_datetime]
            if picking_date:
                max_date = max(picking_date)
                if rec.date <max_date:
                    raise UserError(_("Accounting Date should be greater than Transfer Date."))
          
        return super().action_post()



