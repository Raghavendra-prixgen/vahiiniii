from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
from odoo import api, fields, models, _
from num2words import num2words
from calendar import monthrange
from lxml import etree
from odoo import fields, models, tools
from odoo.tools import formatLang
import json
import re
from odoo.exceptions import AccessError, UserError, ValidationError
# from forex_python.converter import CurrencyRates
import requests
import json
import psycopg2
import simplejson
from odoo.tools import float_compare, date_utils, email_split, html_escape, is_html_empty

from markupsafe import Markup




class AccountPayment(models.Model):
    _inherit = "account.payment"

    y_port_discharge_id = fields.Many2one('l10n_in.port.code',string="Port of Discharge",tracking=True)


    @api.onchange('y_purchase_account_down_id','y_purchase_account_payment_id')
    def _onchange_sale_auto_complete(self):
        super()._onchange_sale_auto_complete()
        if self.y_purchase_account_payment_id and self.y_purchase_account_payment_id.y_transaction_type == 'boe':
            self.memo = self.y_purchase_account_payment_id.y_remark
            self.y_port_discharge_id = self.y_purchase_account_payment_id.y_boe_id.y_port_discharge_id.id
            


class RejectResons(models.TransientModel):
    _inherit = "reject.reason"

    def pass_y_reject_reason(self):
        advance_payment_obj = self.env['purchase.account.payment'].browse(self._context.get('active_id'))
        if advance_payment_obj.y_boe_id:


            advance_payment_obj = self.env['purchase.account.payment'].browse(self._context.get('active_id'))

            msg = Markup("<strong>%s</strong>") % \
                    _("Down payment request has been rejected: %s",
                      advance_payment_obj.y_sequence)

            msg += Markup("<li> %s: <br/>") % _("Reject Reason: %s",
                      self.y_reject_reason)

            advance_payment_obj.y_boe_id.message_post(body=msg)
            advance_payment_obj.y_reject_reason = self.y_reject_reason
        return super().pass_y_reject_reason()

class PurchaseAccount(models.Model):
    _inherit = "purchase.account.payment"

    y_boe_id = fields.Many2one('boe.template',string="BOE")

    def action_approve(self):
        if self.y_boe_id:
            if self.env.user in self.y_boe_id.y_advance_request_form_approval_id.mapped('y_approval_user_ids'):
                self.y_approved_by = self.env.user.id
                self.write({'y_approval_status':'approved','y_is_approved':True})
            else:
                raise UserError (_("Oops!!!! You can't approve the request"))

        return super().action_approve()



    
    def action_reject(self):
        if self.y_boe_id:
            if self.env.user in self.y_boe_id.y_advance_request_form_approval_id.mapped('y_approval_user_ids'):
                self.y_approved_by = self.env.user.id
                self.write({'y_approval_status':'rejected'})
                return {'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'res_model': 'reject.reason',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new'
                      }
            else:
                raise UserError (_("Oops!!!! You can't reject the request"))
        return super().action_reject()



class BOEAdvancePaymentWizard(models.TransientModel):
    _name = "boe.advance.payment.wizard"
    _description = " "

    def get_amount_percentage(self):
        if self.y_boe_id.payment_term_id:
            term_line_ids = self.y_boe_id.y_payment_term_id.line_ids.filtered(lambda x:x.y_advance_request_required == True)
            if term_line_ids:
                if term_line_ids.value == 'percent':
                    return 'percentage'
                elif term_line_ids.value == 'fixed':
                    return 'amount'

    y_name = fields.Char('Name')
    y_boe_id = fields.Many2one('boe.template',string="BOE")
    y_payment_amount = fields.Float('Payment Amount')
    y_payment_status = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft', string="Payment Status")
    y_remark = fields.Text('Remark')
    y_amount_or_percentage = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], default='amount', string=" ")
    y_percentage = fields.Float(string="Percentage")

    y_company_id = fields.Many2one('res.company', 'Company',related="y_boe_id.y_company_id",readonly=True)
    y_currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.company.currency_id)
    y_invoice_date_due = fields.Date(string='Request Date')
    y_is_payment_term_value = fields.Boolean(string="Is Payment Term Value")
    y_payment_term_id = fields.Many2one('account.payment.term',string="Payment Terms")
    y_payment_term_line_id = fields.Many2one('account.payment.term.line',string="Payment Term Line")
    y_port_discharge_id = fields.Many2one('l10n_in.port.code',string="Port of Discharge",tracking=True)

    @api.constrains('y_remark')
    def _check_remark_length(self):
        for record in self:
            if record.y_remark:
                if len(record.y_remark) > 250:
                    raise UserError (_("Length of character should be below 250 characters"))
                if len(record.y_remark.split()) > 50:
                    raise ValidationError('The remark cannot exceed 50 words.')

    @api.constrains('y_invoice_date_due')
    def _check_invoice_date_due(self):
        for record in self:
            if record.y_invoice_date_due and self.y_boe_id.y_bill_of_entry_date:                
                if record.y_invoice_date_due < self.y_boe_id.y_bill_of_entry_date:
                    raise ValidationError("Request Date cannot be earlier than the BOE Date.")

    #need to remove
    def _calculate_percent(self, y_percentage, value):
        """Calculate the percentage value."""
        return (y_percentage / 100) * value


    #need to remove
    @api.onchange('y_amount_or_percentage')
    def _onchange_amount_or_percentage(self):
        if self.y_boe_id and self.y_payment_term_line_id:
            if self.y_amount_or_percentage == 'amount':
                self.y_payment_amount = self.y_payment_term_line_id.value_amount
            else:
                self.y_percentage = self.y_payment_term_line_id.value_amount
                self.y_payment_amount = self._calculate_percent(self.y_percentage, self.y_boe_id.y_total_assessable_value)
                if self.y_percentage:
                    self.y_is_payment_term_value = True



    @api.constrains('y_payment_amount')
    def _check_value(self):
        if self.y_payment_amount <= 0.0:
            raise ValidationError(_("Please Enter The Valid Amount!"))

        total_payments = sum(self.y_boe_id.y_purchase_account_payment_ids.filtered(lambda x:x.y_is_approved).mapped('y_amount'))
        final_amount = total_payments + self.y_payment_amount

        if final_amount > self.y_boe_id.y_duty_payable:
            raise ValidationError("Down Payment Amount Exceeded!")


    def create_advance_payment(self):
        if not self.y_boe_id:
            return
            
        payment_dict = {
            'y_partner_id': self.y_boe_id.y_duty_to_pay_vendor_id.id,
            'y_amount': self.y_payment_amount,
            'y_currency_id': self.y_currency_id.id,
            'y_company_id': self.y_company_id.id,
            'y_date': datetime.now(),
            'y_ref': f'Adv : {self.y_boe_id.y_bill_of_entry_code}',
            'y_boe_id': self.y_boe_id.id,
            'y_transaction_type':'boe',


            'y_remark': self.y_remark,
            'y_invoice_date_due': self.y_invoice_date_due,
            'y_sequence': self.y_boe_id.y_advance_request_form_approval_id.y_advance_sequence_id.next_by_id() or 'New',
        }



        if not self.y_boe_id.y_advance_request_form_approval_id.y_is_approval_required:
            payment_dict.update({
                'y_approval_status': False,    
                'y_is_approved':True,           
            })
        self.env['purchase.account.payment'].create(payment_dict)
        self.y_boe_id.write({'y_is_downpayment_generated':True})



    

   
