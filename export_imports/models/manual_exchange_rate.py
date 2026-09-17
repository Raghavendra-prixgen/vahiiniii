
from odoo import models, fields, api, _
from datetime import date,datetime
import time
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang

from contextlib import ExitStack, contextmanager

# class StockMove(models.Model):
#     _inherit = "stock.move"

#     def get_receipt_lines(self):
#         res = super().get_receipt_lines()
#         account_val = self.env['account.move'].browse(self._context.get('ref_move_id'))
#         stock_move_exchange_rate = self.mapped('picking_id').mapped('y_valuation_exchange_rate')
#         if len(stock_move_exchange_rate) ==1:
#             account_val.write({'y_manual_rate':stock_move_exchange_rate[0]})

#         return res

class AccountMoveNew(models.Model):
    _inherit = "account.move"

    y_manual_rate = fields.Float(
        string='Exchange Rate',
        required=False,digits=(16,8),copy=False)

    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('currency_id','company_id')
    def check_same_currency(self):
        for rec in self:
            rec.y_is_same_currency = bool(rec.currency_id and rec.currency_id != rec.company_id.currency_id)

    @api.depends('currency_id', 'company_currency_id', 'company_id', 'invoice_date','y_manual_rate')
    def _compute_invoice_currency_rate(self):
        res = super()._compute_invoice_currency_rate
        for move in self:
            if move.is_invoice(include_receipts=True):
                if move.currency_id and move.y_manual_rate:
                    move.invoice_currency_rate = 1.0 / move.y_manual_rate
                else:
                    move.invoice_currency_rate = 1
    
    @api.onchange('currency_id')
    def change_currency(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id

                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=rec.invoice_date
                )
                rec.y_manual_rate = rate if rate else 1.0


    @api.model
    def create(self,vals):

        res = super().create(vals)
        if not self._context.get('import_file'):
            if res.currency_id and res.invoice_date:
                company = res.company_id
                # Use Odoo native conversion rate API → correct
                rate = res.currency_id._get_conversion_rate(
                    from_currency=res.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=res.invoice_date
                )
                # Manual rate should always be inverse of actual rate
                res.y_manual_rate = rate if rate else 1.0
                # res.y_manual_rate = res.currency_id.inverse_rate
        return res

    def update_exchange_rate(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id
                # rec.y_manual_rate = rec.currency_id.inverse_rate

                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=rec.invoice_date
                )
                rec.y_manual_rate = rate if rate else 1.0

   
class AccountPaymentNew(models.Model):
    _inherit = "account.payment"

    y_manual_rate = fields.Float(
        string='Exchange Rate',
        required=False,digits=(16,8),)

    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.onchange('currency_id','date')
    def change_currency(self):
        for rec in self:
            if rec.currency_id and not self._context.get('dont_redirect_to_payments') and rec.date:
                company = rec.company_id
                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=rec.date
                )
                # Manual rate should always be inverse of actual rate
                rec.y_manual_rate = rate if rate else 1.0


    @api.model
    def create(self, vals):
        res = super().create(vals)
        # Skip for register payment wizard → correct
        if not self._context.get('dont_redirect_to_payments'):
            # Ensure both fields exist before processing
            if res.currency_id and res.date and not res.y_manual_rate:
                company = res.company_id
                # Use Odoo native conversion rate API → correct
                rate = res.currency_id._get_conversion_rate(
                    from_currency=res.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=res.date
                )
                # Manual rate should always be inverse of actual rate
                res.y_manual_rate = rate if rate else 1.0
        return res

    @api.depends('currency_id','company_id')
    def check_same_currency(self):
        for rec in self:
            rec.y_is_same_currency = bool(rec.currency_id and rec.currency_id != rec.company_id.currency_id)

  
    @api.model
    def _get_trigger_fields_to_synchronize(self):
        res = super()._get_trigger_fields_to_synchronize()
        return res + ('y_manual_rate',)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        self.ensure_one()
        lines = super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals, force_balance=force_balance)

        if not self.y_manual_rate or self.y_manual_rate <= 0:
            return lines

        company_currency = self.company_id.currency_id
        if self.currency_id == company_currency:
            return lines

        company_round = company_currency.round
        total_balance = 0.0

        for line in lines:
            amount_currency = line.get("amount_currency", 0.0)
            if not amount_currency:
                continue

            # FIX: Round the balance calculation immediately
            new_balance = company_round(amount_currency * self.y_manual_rate)
            line["balance"] = new_balance
            total_balance += new_balance

        # FIX: Check balance based on the new ROUNDED values
        diff = company_round(sum(line.get("balance", 0.0) for line in lines))

        if diff:
            for line in reversed(lines):
                # Apply the 0.01 fix to the counterpart line
                if line.get("account_id") == self.destination_account_id.id:
                    line["balance"] = company_round(line["balance"] - diff)
                    break

        return lines


    # def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
    #     result = super()._prepare_move_line_default_vals(write_off_line_vals, force_balance)
    #     print(result, "RESULT BEFORE CUSTOM")

    #     # Odoo rounding method (very important!)
    #     rounding = self.company_id.currency_id.round

    #     if self.y_manual_rate > 0:
    #         print(self.y_manual_rate, "MANUAL RATE ACTIVE")

    #         for index, res in enumerate(result):

    #             amount_currency = res.get("amount_currency", 0.0)
    #             debit = res.get("debit")
    #             credit = res.get("credit")

    #             ####################################################################################
    #             #  CASE 1: COMPANY CURRENCY == PAYMENT CURRENCY
    #             ####################################################################################
    #             if self.company_id.currency_id.id == self.currency_id.id:

    #                 print("CASE 1: SAME CURRENCY")

    #                 if debit and debit > 0:
    #                     new_base = rounding(abs(amount_currency) * self.y_manual_rate)
    #                     res["amount_currency"] = rounding(amount_currency * self.y_manual_rate)
    #                     res["debit"] = new_base
    #                     res["balance"] = new_base

    #                 elif credit and credit > 0:
    #                     new_base = rounding(abs(amount_currency) * self.y_manual_rate)
    #                     res["amount_currency"] = rounding(amount_currency * self.y_manual_rate)
    #                     res["credit"] = new_base
    #                     res["balance"] = -new_base

    #                 else:
    #                     # Write-off for same currency
    #                     new_base = rounding(abs(amount_currency) * self.y_manual_rate)
    #                     res["amount_currency"] = rounding(amount_currency * self.y_manual_rate)

    #                     if amount_currency >= 0:
    #                         res["debit"] = new_base
    #                         res["balance"] = new_base
    #                     else:
    #                         res["credit"] = new_base
    #                         res["balance"] = -new_base

    #             ####################################################################################
    #             #  CASE 2: COMPANY CURRENCY != PAYMENT CURRENCY
    #             ####################################################################################
    #             else:
    #                 print("CASE 2: FOREIGN CURRENCY")

    #                 if debit and debit > 0:
    #                     print("FOREIGN DEBIT")
    #                     base = rounding(abs(amount_currency) * self.y_manual_rate)
    #                     res["debit"] = base
    #                     res["balance"] = base

    #                 elif credit and credit > 0:
    #                     print("FOREIGN CREDIT")
    #                     base = rounding(abs(amount_currency) * self.y_manual_rate)
    #                     res["credit"] = base
    #                     res["balance"] = -base

    #                 ###################################################################
    #                 #  WRITE-OFF (foreign currency)
    #                 ###################################################################
    #                 else:
    #                     print("WRITE-OFF CORRECTION")

    #                     # Debit/Credit totals with rounding
    #                     other_lines = [l for i, l in enumerate(result) if i != index]
    #                     print(other_lines,"other linesssssssssssssssssssssssssssss")
    #                     total_debit = sum(rounding(l.get("debit", 0)) for l in other_lines)
    #                     total_credit = sum(rounding(l.get("credit", 0)) for l in other_lines)

    #                     diff = rounding(total_debit - total_credit)
    #                     print("DEBIT TOTAL:", total_debit)
    #                     print("CREDIT TOTAL:", total_credit)
    #                     print("DIFFERENCE TO FIX:", diff)

    #                     # Base amount for writeoff
    #                     if diff > 0:
    #                         writeoff_base = diff
    #                         res["credit"] = writeoff_base
    #                         res["balance"] = -writeoff_base
    #                     else:
    #                         writeoff_base = abs(diff)
    #                         res["debit"] = writeoff_base
    #                         res["balance"] = writeoff_base

    #                     # Foreign amount_currency using manual rate (also rounded)
    #                     writeoff_amt_currency = rounding(writeoff_base)
    #                     res["amount_currency"] = writeoff_amt_currency

    #                     print("WRITE-OFF amount_currency FIXED TO:", writeoff_amt_currency)

    #     print(result, "RESULT AFTER FIX")
    #     return result

    # def _prepare_move_lines_per_type(self, write_off_line_vals=None, force_balance=None):
    #     self.ensure_one()

    #     result = super()._prepare_move_lines_per_type(
    #         write_off_line_vals=write_off_line_vals,
    #         force_balance=force_balance,
    #     )

    #     # 🚫 No manual rate
    #     if not self.y_manual_rate or self.y_manual_rate <= 0:
    #         return result


    #     # Same currency → no conversion needed
    #     if self.currency_id == self.company_id.currency_id:
    #         return result

    #     rounding = self.company_id.currency_id.round

    #     def apply_manual_rate(lines):
    #         for line in lines:
    #             amount_currency = line.get("amount_currency", 0.0)
    #             if not amount_currency:
    #                 continue

    #             new_balance = rounding(amount_currency * self.y_manual_rate)
    #             line["balance"] = new_balance

    #         return lines

    #     result["liquidity_lines"] = apply_manual_rate(result.get("liquidity_lines", []))
    #     result["counterpart_lines"] = apply_manual_rate(result.get("counterpart_lines", []))
    #     result["write_off_lines"] = apply_manual_rate(result.get("write_off_lines", []))
    #     result["withholding_lines"] = apply_manual_rate(result.get("withholding_lines", []))

    #     return result


    # def _prepare_move_line_default_vals(self, write_off_line_vals=None,force_balance=None):
    #     result = super()._prepare_move_line_default_vals(write_off_line_vals,force_balance)       
    #     if self.y_manual_rate > 0 :
    #         for res in result:
    #             if self.company_id.currency_id.id == self.currency_id.id:
    #                 amount_currency = res['amount_currency']

    #                 if res.get('debit'):
    #                     res['amount_currency'] = amount_currency / self.y_manual_rate
    #                     res['debit'] = abs(amount_currency) / self.y_manual_rate
    #                 if res.get('credit'):
    #                     res['amount_currency'] = amount_currency / self.y_manual_rate
    #                     res['credit'] =  abs(amount_currency) / self.y_manual_rate
    #             else:
    #                 amount_currency = res['amount_currency']
    #                 debit_value = res.get('debit')

    #                 if debit_value is not None and debit_value > 0:
    #                     res['amount_currency'] = amount_currency 
    #                     res['debit'] = abs(amount_currency) * self.y_manual_rate
    #                     res['balance'] = abs(amount_currency) * self.y_manual_rate
    #                 credit_value = res.get('credit')
                    
    #                 if credit_value is not None and credit_value > 0:
    #                     res['amount_currency'] = amount_currency 
    #                     res['credit'] = abs(amount_currency) * self.y_manual_rate
    #                     res['balance'] = -(abs(amount_currency) * self.y_manual_rate)
    #     print(result,333333333333333333333333333333333333333)

        
    #     return result






class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    y_manual_rate = fields.Float(
        string='Exchange Rate',
        required=False,digits=(16,8))

    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('currency_id','company_currency_id')
    def check_same_currency(self):
        for rec in self:
            rec.y_is_same_currency = bool(rec.currency_id and rec.currency_id != rec.company_currency_id)


    def action_register_payment(self):
        res = super(AccountPaymentRegister, self).action_register_payment()
        res.update({
            'context':{'is_register_account_payment': True}
        })
        return res


    # to flow manual rate from register payment to payment screen
    def _init_payments(self, to_process, edit_mode=False):
        res = super()._init_payments(to_process,edit_mode)
        if self.y_manual_rate:
            res.y_manual_rate = self.y_manual_rate
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        if self.y_manual_rate:
            payment_vals['y_manual_rate'] = self.y_manual_rate
        return payment_vals


    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.y_manual_rate:
            payment_vals['y_manual_rate'] = self.y_manual_rate      
        return payment_vals


class SaleOrder(models.Model):
    _inherit = "sale.order"

    y_manual_rate = fields.Float(
        string='Exchange Rate',
        required=False,digits=(16,8))

    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('currency_id','company_id')
    def check_same_currency(self):
        for rec in self:
            rec.y_is_same_currency = bool(rec.currency_id and rec.currency_id != rec.company_id.currency_id)

    @api.onchange('currency_id','date_order')
    def change_currency(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id
                date_order = rec.date_order.date()
                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                rec.y_manual_rate = rate if rate else 1.0


    @api.model
    def create(self,vals):
        res = super().create(vals)
        if not self._context.get('import_file'):
            if res.currency_id and res.date_order:
                company = res.company_id
                date_order = res.date_order.date()
                rate = res.currency_id._get_conversion_rate(
                    from_currency=res.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                res.y_manual_rate = rate if rate else 1.0
        return res

    def update_exchange_rate(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id
                # rec.y_manual_rate = rec.currency_id.inverse_rate
                date_order = rec.date_order.date()
                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                rec.y_manual_rate = rate if rate else 1.0


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    y_manual_rate = fields.Float(
        string='Exchange Rate',
        required=False,digits=(16,8))

    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('currency_id','company_id')
    def check_same_currency(self):
        for rec in self:
            rec.y_is_same_currency = bool(rec.currency_id and rec.currency_id != rec.company_id.currency_id)

    @api.onchange('currency_id','date_order')
    def change_currency(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id
                date_order = rec.date_order.date()
                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                rec.y_manual_rate = rate if rate else 1.0


    @api.model
    def create(self,vals):
        res = super().create(vals)
        if not self._context.get('import_file'):
            if res.currency_id and res.date_order:
                company = res.company_id
                date_order = res.date_order.date()
                rate = res.currency_id._get_conversion_rate(
                    from_currency=res.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                res.y_manual_rate = rate if rate else 1.0
        return res

    def update_exchange_rate(self):
        for rec in self:
            if rec.currency_id:
                company = rec.company_id
                # rec.y_manual_rate = rec.currency_id.inverse_rate
                date_order = rec.date_order.date()
                rate = rec.currency_id._get_conversion_rate(
                    from_currency=rec.currency_id,
                    to_currency=company.currency_id,
                    company=company,
                    date=date_order
                )
                rec.y_manual_rate = rate if rate else 1.0
