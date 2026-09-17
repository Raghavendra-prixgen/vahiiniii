from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, tools, _


class AlternativeGl(models.Model):
    _inherit = 'alternative.gl'

    y_is_tax_required = fields.Boolean(string="Is Tax Required",tracking=True)

class AcoountJournal(models.Model):
    _inherit = 'account.journal'

    y_is_setoff_journal = fields.Boolean(string='Set Off Advance Entry',store=True)

class AccounMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_is_advance_tax_line = fields.Boolean(string="Is Advance Tax Line")
    y_advance_tax_ids = fields.Many2many('account.tax','advance_tax_account_move_rel',string="Advance Taxes")

class AccounMove(models.Model):
    _inherit = 'account.move'

    y_is_pending_setoff_advace_payment = fields.Boolean(compute="_compute_pending_setoff_advace_payment")

    @api.depends('partner_id')
    def _compute_pending_setoff_advace_payment(self):
        for move in self:
            move.y_is_pending_setoff_advace_payment = False
            if move.move_type in ('in_invoice','out_invoice') and move.partner_id:
                domain = [('partner_id','=',move.partner_id.id),('y_purchase_account_payment_id','!=',False),('y_adv_payment_done','=',False),('state','in',('in_process','paid'))]
                if move.move_type == 'in_invoice':
                    domain+=[('payment_type','=','outbound')]
                if move.move_type == 'out_invoice':
                    domain_=[('payment_type','=','inbound')]
                payments = self.env['account.payment'].search(domain)
                if payments:
                    move.y_is_pending_setoff_advace_payment = True

    def set_off_payment_wizard(self):
        self.ensure_one()
        if self.move_type in ('out_invoice','in_invoice'):
            if self.state == 'posted':
                view_ref = self.env.ref('payment_tax_addon.set_off_advance_payment_view_form').id
                if self.move_type == 'out_invoice':                    
                    payment_type = 'inbound'
                if self.move_type == 'in_invoice':
                    payment_type = 'outbound'
                return {
                        'name': _('Set off Advance Payment'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'advance.payment.entry.wizard',
                        'view_mode': 'form',
                        'view_id': view_ref,
                        'context': {'default_y_account_move_id':self.id,'default_y_payment_type': payment_type,'default_y_partner_id':self.partner_id.id},
                        'target': 'new',
                        }
            else:
                raise ValidationError("Advance payments for set-off should only be made in the posted state.")
        else:
            raise ValidationError("Please ensure that advance payments are only made against a bill or invoice.")
            
class PaymentTaxes(models.Model):
    _inherit = 'account.payment'

    y_tax_ids = fields.Many2many('account.tax',domain="[('type_tax_use', '=', 'purchase' if payment_type == 'outbound' else 'sale')]")
    y_adv_payment_done = fields.Boolean(default=False,copy=False)
    y_setoff_advance_entry_id = fields.Many2one('account.move',string="Set Off Advance Payment")
    y_is_tax_required = fields.Boolean(string="Is Tax Required",related="y_alternative_gl.y_is_tax_required",store=True)

    @api.onchange('y_purchase_account_payment_id')
    def _onchange_purchase_account_payment(self):
        for pay in self:
            if pay.y_purchase_account_payment_id:
                tax_ids = pay.y_purchase_account_payment_id.y_purchase_id.order_line.taxes_id.filtered(lambda x:x.tax_group_id.name == 'TDS')
                if tax_ids:
                    pay.y_tax_ids = [(6,0,tax_ids.ids)]

    def view_set_off_payment_entry(self):
        return {
                'name': _('Set-Off Entry'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'new',
                'res_id': self.y_setoff_advance_entry_id.id,
                'target':'current'
            }

    @api.onchange('is_internal_transfer')
    def _onchange_is_internal_transfer(self):
        if self.y_alternative_gl and  self.y_tax_ids:
            self.y_alternative_gl = None
            self.y_tax_ids = None
          
    @api.onchange('payment_type')
    def _onchange_payment_type_alternate_gl(self):
        if self.y_alternative_gl and self.y_tax_ids:
            raise ValidationError("You cannot change the payment type")

    def _get_trigger_fields_to_synchronize(self):
        return super()._get_trigger_fields_to_synchronize() + ('y_tax_ids',)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super()._prepare_move_line_default_vals(write_off_line_vals, force_balance)

        if not self.y_tax_ids:
            return res

        currency_id = self.currency_id.id
        company_currency = self.company_id.currency_id
        is_same_currency = self.currency_id == company_currency
        currency_rate = self.currency_id._get_conversion_rate(self.currency_id, company_currency, self.company_id, self.date)
        
        sign = -1 if self.payment_type == 'inbound' else 1
        amount_currency = sign * self.amount
        balance = company_currency.round(amount_currency * currency_rate)

        tax_line_vals = []
        total_tax_amount_currency = 0
        total_tax_balance = 0
        base_tax_grid = []
        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())

        for tax in self.y_tax_ids:
            taxes = tax.children_tax_ids if tax.amount_type == 'group' else [tax]
            for t in taxes:
                repartition_line = t.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax' and x.tag_ids)
                base_line = t.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'base' and x.tag_ids)
                if base_line:
                    base_tax_grid.append(base_line.tag_ids.id)
                
                if not repartition_line.account_id:
                    raise ValidationError("Please update Distribution For Invoices In Taxes")
                
                tax_amount_currency = sign * round(self.amount * t.amount) / 100
                tax_balance = company_currency.round(tax_amount_currency * currency_rate)
                
                total_tax_amount_currency += tax_amount_currency
                total_tax_balance += tax_balance
                
                tax_line_vals.append({
                    'name': t.name,
                    'date_maturity': self.date,
                    'amount_currency': tax_amount_currency,
                    'currency_id': currency_id,
                    'debit': tax_balance if tax_balance > 0 else 0,
                    'credit': -tax_balance if tax_balance < 0 else 0,
                    'partner_id': self.partner_id.id,
                    'account_id': repartition_line.account_id.id,
                    'tax_tag_ids': [repartition_line.tag_ids.id],
                    'y_is_advance_tax_line':True,
                    'y_advance_tax_ids': [(6,0,t.ids)],
                })


        liquidity_amount_currency = -amount_currency - total_tax_amount_currency
        liquidity_balance = -balance - total_tax_balance
        counterpart_amount_currency = amount_currency 
        counterpart_balance = balance 

        # Adjust for rounding differences
        rounding_difference = company_currency.round(liquidity_balance + counterpart_balance + total_tax_balance)
        if rounding_difference:
            if self.payment_type == 'inbound':
                counterpart_balance += rounding_difference
            else:
                liquidity_balance -= rounding_difference

        line_vals_list = [
            {
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0 else 0,
                'credit': -liquidity_balance if liquidity_balance < 0 else 0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
                'tax_tag_ids': base_tax_grid if self.payment_type == 'outbound' else [],
            },
            {
                'name': counterpart_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0 else 0,
                'credit': -counterpart_balance if counterpart_balance < 0 else 0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            }
        ]
        
        return line_vals_list + tax_line_vals
        



    # def _synchronize_from_moves(self, changed_fields):
    #     ''' Update the account.payment regarding its related account.move.
    #     Also, check both models are still consistent.
    #     :param changed_fields: A set containing all modified fields on account.move.
    #     '''
    #     if self._context.get('skip_account_move_synchronization'):
    #         return

    #     for pay in self.with_context(skip_account_move_synchronization=True):

    #         # After the migration to 14.0, the journal entry could be shared between the account.payment and the
    #         # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
    #         if pay.move_id.statement_line_id:
    #             continue

    #         move = pay.move_id
    #         move_vals_to_write = {}
    #         payment_vals_to_write = {}

    #         if 'journal_id' in changed_fields:
    #             if pay.journal_id.type not in ('bank', 'cash'):
    #                 raise UserError(_("A payment must always belongs to a bank or cash journal."))

    #         if 'line_ids' in changed_fields:
    #             all_lines = move.line_ids
    #             liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

    #             if len(liquidity_lines) != 1:
    #                 raise UserError(_(
    #                     "Journal Entry %s is not valid. In order to proceed, the journal items must "
    #                     "include one and only one outstanding payments/receipts account.",
    #                     move.display_name,
    #                 ))

    #             if len(counterpart_lines) != 1 and not self.y_alternative_gl:
    #                 raise UserError(_(
    #                     "Journal Entry %s is not valid. In order to proceed, the journal items must "
    #                     "include one and only one receivable/payable account (with an exception of "
    #                     "internal transfers).",
    #                     move.display_name,
    #                 ))

    #             if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
    #                 raise UserError(_(
    #                     "Journal Entry %s is not valid. In order to proceed, the journal items must "
    #                     "share the same currency.",
    #                     move.display_name,
    #                 ))

    #             if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
    #                 raise UserError(_(
    #                     "Journal Entry %s is not valid. In order to proceed, the journal items must "
    #                     "share the same partner.",
    #                     move.display_name,
    #                 ))

    #             if counterpart_lines.account_id.account_type == 'asset_receivable':
    #                 partner_type = 'customer'
    #             else:
    #                 partner_type = 'supplier'

    #             liquidity_amount = liquidity_lines.amount_currency

    #             move_vals_to_write.update({
    #                 'currency_id': liquidity_lines.currency_id.id,
    #                 'partner_id': liquidity_lines.partner_id.id,
    #             })
    #             payment_vals_to_write.update({
    #                 'amount': abs(liquidity_amount) if not pay.y_tax_ids else pay.amount,
    #                 'partner_type': partner_type,
    #                 'currency_id': liquidity_lines.currency_id.id,
    #                 'destination_account_id': counterpart_lines.account_id.id,
    #                 'partner_id': liquidity_lines.partner_id.id,
    #             })
    #             if liquidity_amount > 0.0:
    #                 payment_vals_to_write.update({'payment_type': 'inbound'})
    #             elif liquidity_amount < 0.0:
    #                 payment_vals_to_write.update({'payment_type': 'outbound'})

    #         move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
    #         pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))
