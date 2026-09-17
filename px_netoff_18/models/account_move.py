# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    net_off_entry_id = fields.Many2one('account.move', copy=False)

    def button_draft(self):
        for rec in self:
            if rec.net_off_entry_id:
                move_ids = rec.net_off_entry_id
                if move_ids:
                    # Create a reverse move directly rather than using the wizard
                    # This is the main change as account.move.reversal is likely deprecated
                    default_values_list = [{
                        'date': fields.Date.today(),
                        'ref': _('Reversal of: %s') % move.name,
                        'journal_id': move.journal_id.id,
                    } for move in move_ids]

                    # Use the new reverse_moves method directly on the move
                    reversed_moves = move_ids._reverse_moves(default_values_list=default_values_list, cancel=True)

                    # Clear the net_off_entry_id field
                    rec.net_off_entry_id = False
        return super(AccountMove, self).button_draft()

    def create_netoffs(self):
        journal_id = int(self.env['ir.config_parameter'].sudo().get_param('net_off_account_journal_id'))
        for rec in self:
            if not rec.net_off_entry_id and rec.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                partner = rec.partner_id.parent_id or rec.partner_id
                net_off_type = partner.net_off_type
                # Get analytic values from the first line
                # In Odoo 18, we should check if there are invoice lines
                if not rec.invoice_line_ids:
                    continue

                # analytic_acc = rec.invoice_line_ids[0].analytic_account_id.id
                # analytic_tags = rec.invoice_line_ids[0].analytic_tag_ids.ids

                if net_off_type:
                    if rec.move_type in ('in_invoice', 'in_refund') and net_off_type == 'rp':
                        pass
                    elif rec.move_type in ('out_invoice', 'out_refund') and net_off_type == 'pr':
                        pass
                    else:
                        # Create the journal entry
                        rec.net_off_entry_id = rec.env['account.move'].create({
                            'move_type': 'entry',
                            'ref': rec.name,
                            'journal_id': journal_id,
                            'line_ids': [
                                (0, 0, {
                                    'account_id': partner.property_account_payable_id.id,
                                    'analytic_distribution': rec.invoice_line_ids[:1].analytic_distribution,
                                    'partner_id': partner.id,
                                    'name': rec.name,
                                    'debit': rec.amount_residual if rec.move_type in (
                                    'in_invoice', 'out_invoice') else 0,
                                    'credit': rec.amount_residual if rec.move_type in (
                                    'in_refund', 'out_refund') else 0,
                                }),
                                (0, 0, {
                                    'account_id': partner.property_account_receivable_id.id,
                                    'analytic_distribution': rec.invoice_line_ids[:1].analytic_distribution,
                                    'partner_id': partner.id,
                                    'name': rec.name,
                                    'credit': rec.amount_residual if rec.move_type in (
                                    'in_invoice', 'out_invoice') else 0,
                                    'debit': rec.amount_residual if rec.move_type in ('in_refund', 'out_refund') else 0,
                                })
                            ]
                        })
                        # Post the entry
                        rec.net_off_entry_id.action_post()

                        invoice_lines = self.line_ids.filtered(
                            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable')
                            and not line.reconciled
                        )
                        payment_lines = rec.net_off_entry_id.line_ids.filtered(
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

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.create_netoffs()
        return res