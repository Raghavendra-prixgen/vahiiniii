from odoo import models, fields, api
import json

from odoo import models, fields, api
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    y_payment_date = fields.Date(string="Payment Date", compute="_compute_payment_date", store=True)
    y_payment_reconcilation_date = fields.Date(string="Payment Reconciliation Date", compute="_compute_payment_reconcilaiation_date", store=True)

    @api.depends('line_ids.matched_debit_ids.debit_move_id.move_id.date', 
                 'line_ids.matched_credit_ids.credit_move_id.move_id.date', 
                 'payment_state')
    def _compute_payment_date(self):
        for move in self:
            payment_dates = []
            for line in move.line_ids:
                for matched in line.matched_debit_ids:
                    payment = matched.debit_move_id.move_id.origin_payment_id
                    if payment and payment.date:
                        payment_dates.append(payment.date)

                for matched in line.matched_credit_ids:
                    payment = matched.credit_move_id.move_id.origin_payment_id
                    if payment and payment.date:
                        payment_dates.append(payment.date)

            move.y_payment_date = max(payment_dates) if payment_dates else False

    @api.depends('line_ids.matched_debit_ids.max_date', 
                 'line_ids.matched_credit_ids.max_date', 
                 'payment_state')
    def _compute_payment_reconcilaiation_date(self):
        for move in self:
            reconciliation_dates = []
            for line in move.line_ids:
                for matched in line.matched_debit_ids.filtered(lambda x: x.debit_move_id.move_id.origin_payment_id):
                    reconciliation_dates.append(matched.max_date)

                for matched in line.matched_credit_ids.filtered(lambda x: x.credit_move_id.move_id.origin_payment_id):
                    reconciliation_dates.append(matched.max_date)

            move.y_payment_reconcilation_date = max(reconciliation_dates) if reconciliation_dates else False
