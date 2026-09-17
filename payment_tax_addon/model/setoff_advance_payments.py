from odoo.exceptions import ValidationError
from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)

from markupsafe import Markup

class AdvancePayment(models.Model):
    _name = 'advance.payment.entry.wizard'
    _description = 'Advance Payment Entry Wizard'


    y_partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    y_payment_type = fields.Selection([('outbound','Send'),('inbound','Receive')])
    y_journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    y_date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    y_payments_id = fields.Many2one('account.payment', string='Payments' ,required=True)
    y_account_move_id = fields.Many2one('account.move',string="Bill/Invoice")

    def genarate_advance_payment(self):
        if self.y_payments_id.move_id.line_ids:

            self.prepare_journal_vals()

    def prepare_journal_vals(self):
        if self.y_payments_id.y_adv_payment_done:

            raise ValidationError(_('Advance Payment Already Done'))

        common_values = {
            'date': self.y_date,
            'journal_id': self.y_journal_id.id,
            'move_type': 'entry',
            }

        move_id = self.y_account_move_id
        if self.y_payment_type == 'outbound':
            self.y_payments_id.y_setoff_advance_entry_id = move_id.id
            self._prepare_outbound_payment(common_values, move_id)
            move_id.message_post(
                body=Markup("<b>%s:</b> %s <a href=#id=%s&view_type=form&model=account.payment>%s</a>") % (
                    _("Payment"),
                    _("-->"),
                    self.y_payments_id.id,
                    self.y_payments_id.name))
        
        # if self.y_payment_type == 'inbound':
        #     self._prepare_inbound_payment(common_values, move_id)
        #     move_id.message_post(
        #         body=Markup("<b>%s:</b> %s <a href=#id=%s&view_type=form&model=account.payment>%s</a>") % (
        #             _("Payment"),
        #             _("-->"),
        #             self.y_payments_id.id,
        #             self.y_payments_id.name))

    def reconcile_invoice_and_bill(self, invoice_move, payment_move, payment_amount):
        invoice_lines = invoice_move.line_ids.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable')
            and not line.reconciled
        )
        payment_lines = payment_move.line_ids.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable')
            and not line.reconciled
        )
        
        lines_to_reconcile = invoice_lines + payment_lines
        
        for account in lines_to_reconcile.mapped('account_id'):
            account_lines = lines_to_reconcile.filtered(lambda l: l.account_id == account)
            debit_lines = account_lines.filtered(lambda l: l.debit > 0)
            credit_lines = account_lines.filtered(lambda l: l.credit > 0)
            
            if debit_lines and credit_lines:
                try:
                    (debit_lines + credit_lines).reconcile()
                except Exception:
                    pass
        
        return True

    def _prepare_outbound_payment(self, common_values, bill_move):
        line_ids = []
        total_payment = 0
        total_debit = 0
        total_credit = 0

        # Find the payable account from the bill
        payable_line_id = bill_move.line_ids.filtered(lambda line: line.account_id.account_type == 'liability_payable')
        
        for line in self.y_payments_id.move_id.line_ids.filtered(lambda x:x.account_id != self.y_payments_id.outstanding_account_id):
            if line.balance > 0:
                # Debit line to Credit line
                line_ids.append((0, 0, {
                    'name': line.name,
                    'date_maturity': self.y_date,
                    'currency_id': line.currency_id.id,
                    'debit': 0.0,
                    'credit': abs(line.amount_currency),
                    'amount_currency': -(line.amount_currency),
                    'partner_id': line.partner_id.id,
                    'account_id': line.account_id.id,
                    'tax_tag_ids': line.tax_tag_ids.ids,
                    'y_is_advance_tax_line':line.y_is_advance_tax_line,
                    'y_advance_tax_ids': [(6,0,line.y_advance_tax_ids.ids)],
                }))
                total_credit+= abs(line.amount_currency)
                
            else:
                # Credit line to Debit line
                amount = abs(line.amount_currency)
                line_ids.append((0, 0, {
                    'name': line.name,
                    'date_maturity': self.y_date,
                    'amount_currency': amount,
                    'currency_id': line.currency_id.id,
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': line.partner_id.id,
                    'account_id': line.account_id.id,
                    'tax_tag_ids': line.tax_tag_ids.ids,
                    'y_is_advance_tax_line':line.y_is_advance_tax_line,
                    'y_advance_tax_ids': [(6,0,line.y_advance_tax_ids.ids)],
                }))
                total_debit+= abs(line.balance)
        amount = total_credit - total_debit
        line_ids.append((0, 0, {
                    'name': payable_line_id[0].name,
                    'date_maturity': self.y_date,
                    'amount_currency': amount,
                    'currency_id': self.env.company.currency_id.id,
                    'debit': amount,
                    'credit': 0.0,
                    'account_id': payable_line_id[0].account_id.id,
                    'partner_id': self.y_payments_id.partner_id.id,
                }))
            
        payment_values = common_values.copy()
        payment_values.update({'line_ids': line_ids})
        payment_move = self.env['account.move'].create(payment_values)
        payment_move.action_post()
        self.y_payments_id.y_adv_payment_done = True
        self.reconcile_invoice_and_bill(bill_move, payment_move, total_payment)

        return True
    

        

    # def _prepare_inbound_payment(self, common_values, invoice_move):
    #     line_ids = []
    #     total_payment = 0
    #     total_debit = 0
    #     total_credit = 0

    #     # Find the receivable account from the invoice
    #     receivable_account = invoice_move.line_ids.filtered(lambda line: line.account_id.account_type == 'asset_receivable').account_id

    #     for line in self.y_payments_id.line_ids:
    #         amount = abs(line.amount_currency)
    #         total_payment += amount

    #         if line.account_id == receivable_account:
    #             # Credit the receivable account
    #             line_ids.append((0, 0, {
    #                 'name': line.name,
    #                 'date_maturity': self.y_date,
    #                 'amount_currency': -amount,
    #                 'currency_id': line.currency_id.id,
    #                 'debit': 0.0,
    #                 'credit': amount,
    #                 'partner_id': line.partner_id.id,
    #                 'account_id': receivable_account.id,
    #                 'tax_tag_ids': line.tax_tag_ids.ids
    #             }))
    #             total_credit += amount
    #         else:
    #             # Debit the payment account
    #             line_ids.append((0, 0, {
    #                 'name': line.name,
    #                 'date_maturity': self.y_date,
    #                 'amount_currency': amount,
    #                 'currency_id': line.currency_id.id,
    #                 'debit': amount,
    #                 'credit': 0.0,
    #                 'partner_id': line.partner_id.id,
    #                 'account_id': line.account_id.id,
    #                 'tax_tag_ids': line.tax_tag_ids.ids
    #             }))
    #             total_debit += amount

    #     # Ensure the entry is balanced
    #     if total_debit != total_credit:
    #         if total_debit > total_credit:
    #             line_ids.append((0, 0, {
    #                 'name': 'Payment balance',
    #                 'date_maturity': self.y_date,
    #                 'amount_currency': -(total_debit - total_credit),
    #                 'currency_id': self.env.company.currency_id.id,
    #                 'debit': 0.0,
    #                 'credit': total_debit - total_credit,
    #                 'account_id': receivable_account.id,
    #                 'partner_id': self.y_payments_id.partner_id.id,
    #             }))
    #         else:
    #             line_ids.append((0, 0, {
    #                 'name': 'Payment balance',
    #                 'date_maturity': self.y_date,
    #                 'amount_currency': total_credit - total_debit,
    #                 'currency_id': self.env.company.currency_id.id,
    #                 'debit': total_credit - total_debit,
    #                 'credit': 0.0,
    #                 'account_id': self.y_payments_id.destination_account_id.id,
    #                 'partner_id': self.y_payments_id.partner_id.id,
    #             }))

    #     payment_values = common_values.copy()
    #     payment_values.update({'line_ids': line_ids})

    #     payment_move = self.env['account.move'].create(payment_values)
    #     payment_move.action_post()
    #     self.y_payments_id.y_adv_payment_done = True
    #     self.reconcile_invoice_and_bill(invoice_move, payment_move, total_payment)
    #     move_id.message_post(
    #             body=Markup("<b>%s:</b> %s <a href=#id=%s&view_type=form&model=account.payment>%s</a>") % (
    #                 _("Payment"),
    #                 _("-->"),
    #                 self.y_payments_id.id,
    #                 self.y_payments_id.name))
    #     return True

    
    