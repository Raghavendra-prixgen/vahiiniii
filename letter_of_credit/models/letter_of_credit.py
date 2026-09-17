from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from datetime import date

class ResBank(models.Model):
    _inherit= "res.bank"

    y_house_bank = fields.Boolean(string="House Bank")


class AccountMove(models.Model):
    _inherit = "account.move"

    y_letter_of_credit_id = fields.Many2one('letter.of.credit',string="Letter Of Credit",copy=False)

class LetterCreditMaster(models.Model):
    _name = "lettercredit.master"
    _description = "Letter Credit Master"
    _rec_name = "y_name"

    y_name = fields.Char(string="Sequence",default='New')
    y_bank_id = fields.Many2one('res.bank',string="Bank")
    y_utilised_value = fields.Float(string="Value Utilised")
    y_remaining_value = fields.Float(string='Remaining Value',compute="calculate_remaining_value")
    y_lc_boe_value_lcy = fields.Float(string="LC/BOE value LCY")

    # @api.model
    # def create(self, vals):
    #     if vals.get('y_name', 'New') == 'New':
    #         vals['y_name'] = self.env['ir.sequence'].next_by_code('lettercredit.master') or 'New'
    #     return super(LetterCreditMaster, self).create(vals)

    @api.depends('y_lc_boe_value_lcy','y_utilised_value')
    def calculate_remaining_value(self):
        for rec in self:
            rec.y_remaining_value = rec.y_lc_boe_value_lcy - rec.y_utilised_value

class LetterOfCredit(models.Model):
    _name = "letter.of.credit"
    _description = "Letter Of Credit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "y_boe_id"

    active = fields.Boolean(string="Active",copy=False,default=True,tracking=True)
    y_name = fields.Char(string="Name",default='New',copy=False)
    y_boe_id = fields.Char(string="LC.No")
    y_description = fields.Char(string="Description")
    y_transaction_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
    ], string='Transaction Type',tracking=True,copy=False)
    y_partner_id = fields.Many2one('res.partner',string="Partner")
    y_issuing_bank_id = fields.Many2one('res.bank',string="Issuing Bank")
    y_receiving_bank_id = fields.Many2one('res.bank',string="Receiving Bank")
    y_lc_state = fields.Selection([
        ('released', 'Released'),
        ('closed', 'Closed'),
    ], string='LC Status',tracking=True,copy=False)

    y_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='State',default='draft',tracking=True,copy=False)
    y_date_of_issue = fields.Date(string="Date of issue")
    y_expiry_date = fields.Date(string="Expiry Date")
    
    y_lc_type = fields.Selection([
        ('inland', 'InLand'),
        ('foreign', 'Foreign'),
    ], string='LC Type',tracking=True,copy=False)
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id,tracking=True)    
    y_company_currency_id = fields.Many2one(related='y_company_id.currency_id')
    y_currency_id = fields.Many2one('res.currency',string="Currency",copy=False)
    y_exchange_rate = fields.Float(string="Exchange Rate")
    y_lc_boe_value = fields.Monetary(string="LC/Boe FCY Value",currency_field='y_currency_id')
    y_lcy_value = fields.Monetary(string="LC LCY Value",compute="calculate_local_currency",currency_field='y_company_currency_id')
    y_utilised_value = fields.Monetary(string="Utilised FCY Value",compute="calculate_utilised_value",currency_field='y_currency_id')
    y_utilised_value_lcy = fields.Monetary(string="Utilised LCY Value",compute="calculate_utilised_value",currency_field='y_company_currency_id')

    y_remaining_fcy_value = fields.Monetary(string="Remaining FCY Value",compute="calculate_remaining_fcy_value",currency_field='y_currency_id')
    y_remaining_lcy_value = fields.Monetary(string="Remaining LCY Value",compute="calculate_remaining_lcy_value",currency_field='y_company_currency_id')

    y_bill_ids = fields.One2many('account.move','y_letter_of_credit_id')
    y_is_bill_value_empty = fields.Boolean(string="Is Empty Bill Value",compute=False,store=True,default=False)

    @api.model
    def create(self, vals):
        if vals.get('y_name', _('New')) == _('New'):
            vals.update({'y_name': self.env['ir.sequence'].next_by_code('lettercredit.master')})
        return super(LetterOfCredit, self).create(vals)

    @api.depends('y_lc_boe_value','y_utilised_value')
    def calculate_remaining_fcy_value(self):
        for rec in self:
            if rec.y_lc_boe_value or rec.y_utilised_value:
                rec.y_remaining_fcy_value = rec.y_lc_boe_value - rec.y_utilised_value
            else:
                rec.y_remaining_fcy_value = 0

    @api.depends('y_lcy_value','y_utilised_value_lcy')
    def calculate_remaining_lcy_value(self):
        for rec in self:
            if rec.y_lcy_value or rec.y_utilised_value_lcy:
                rec.y_remaining_lcy_value = rec.y_lcy_value - rec.y_utilised_value_lcy
            else:
                rec.y_remaining_lcy_value = 0

    @api.depends('y_bill_ids')
    def calculate_utilised_value(self):
        for rec in self:
            if rec.y_bill_ids:
                rec.y_utilised_value = abs(sum(rec.y_bill_ids.mapped('amount_total_in_currency_signed')))
                rec.y_utilised_value_lcy = rec.y_utilised_value * rec.y_exchange_rate
            else:
                rec.y_utilised_value = 0
                rec.y_utilised_value_lcy = 0

    @api.onchange('y_expiry_date')
    def _onchange_active(self):
        today = date.today()
        for record in self:
            if record.y_expiry_date:
                record.active = record.y_expiry_date >= today if record.y_expiry_date else False

    @api.model
    def _cron_update_active_status(self):
        self.search([])._onchange_active()

    @api.constrains('y_date_of_issue', 'y_expiry_date')
    def _check_date_of_issue_expiry(self):
        for rec in self:
            if rec.y_date_of_issue and rec.y_expiry_date and rec.y_date_of_issue > rec.y_expiry_date:
                raise ValidationError(_("The date of issue cannot be later than the expiry date."))    

    def action_confirm(self):
        for rec in self:
            rec.write({'y_state':'confirmed'})

    @api.depends('y_exchange_rate','y_lc_boe_value')
    def calculate_local_currency(self):
        for rec in self:
            if rec.y_exchange_rate:
                rec.y_lcy_value = rec.y_exchange_rate * rec.y_lc_boe_value
            else:
                rec.y_lcy_value = rec.y_lc_boe_value

    @api.depends('y_utilised_value','y_lcy_value','y_bill_ids')
    def calculate_bill_total_value_with_utilised_value(self):
        for rec in self:
            if rec.y_utilised_value == rec.y_lcy_value or rec.y_utilised_value >rec.y_lcy_value:
                rec.y_is_bill_value_empty = True
            else:
                rec.y_is_bill_value_empty = False

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    y_letter_of_credit_id = fields.Many2one('letter.of.credit', string="Letter Of Credit",
        domain="[('y_transaction_type', '=', 'purchase'), ('y_partner_id', '=', partner_id), ('active', '=', True)]")

    @api.onchange('partner_id')
    def _onchange_partner_letter_of_credit(self):
        self.y_letter_of_credit_id = False
        return {'domain': {'y_letter_of_credit_id': [
            ('y_transaction_type', '=', 'purchase'),
            ('active', '=', True),
            ('y_partner_id', '=', self.partner_id.id)
        ]}}

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals['y_letter_of_credit_id'] = self.y_letter_of_credit_id.id
        return invoice_vals

    def button_confirm(self):
        for rec in self:
            if rec.y_letter_of_credit_id:
                if rec.y_letter_of_credit_id.y_utilised_value == rec.y_letter_of_credit_id.y_lc_boe_value or rec.y_letter_of_credit_id.y_utilised_value >rec.y_letter_of_credit_id.y_lc_boe_value:
                    raise UserError(_("LC Value is completely utilised"))
        return super().button_confirm()

class SaleOrder(models.Model):
    _inherit = "sale.order"

    y_letter_of_credit_id = fields.Many2one('letter.of.credit',string="Letter Of Credit",
    domain="[('y_transaction_type', '=', 'sale'), ('y_partner_id', '=', partner_id), ('active', '=', True)]")

    @api.onchange('partner_id')
    def _onchange_partner_letter_of_credit(self):
        self.y_letter_of_credit_id = False
        return {'domain': {'y_letter_of_credit_id': [
            ('y_transaction_type', '=', 'sale'),
            ('active', '=', True),
            ('y_partner_id', '=', self.partner_id.id)
        ]}}

    def _prepare_invoice(self):        
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['y_letter_of_credit_id'] = self.y_letter_of_credit_id.id
        return invoice_vals