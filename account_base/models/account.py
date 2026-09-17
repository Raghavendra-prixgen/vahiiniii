# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
import pytz
from datetime import datetime, timedelta,date
from odoo.tools import SQL




class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    y_amount_residual = fields.Float(string='Amount Due in Currency')
    y_amount_residual_signed = fields.Float(string='Amount Due')
    y_weight = fields.Float(string="Weight Per Unit")
    y_total_weight = fields.Float(string="Total Weight")

   
    def _select(self) -> SQL:
        return SQL("""%s,move.amount_residual AS y_amount_residual,
                         move.amount_residual_signed AS y_amount_residual_signed, 
                         template.weight AS y_weight,
                         line.quantity / NULLIF(COALESCE(uom_line.factor, 1) / COALESCE(uom_template.factor, 1), 0.0) * (CASE WHEN move.move_type IN ('in_invoice','out_refund','in_receipt') THEN -1 ELSE 1 END) * template.weight AS y_total_weight""",
                   super()._select())

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    y_name_sequence_id = fields.Many2one('ir.sequence',string="Custom Sequence")
    y_refund_sequence_id = fields.Many2one('ir.sequence',string="Custom Refund Sequence")
    y_out_sequence_id = fields.Many2one('ir.sequence',string="Outward Sequence")
    y_in_sequence_id = fields.Many2one('ir.sequence',string="Inward Sequence")
    y_recon_sequence_id = fields.Many2one('ir.sequence',string="Reconciliation Sequence")
    y_make_seq_mandetory = fields.Boolean(compute="_get_seq_mand",string="Make Sequence Mandatory")

    inbound_payment_method_line_ids = fields.One2many(compute=False)
    outbound_payment_method_line_ids = fields.One2many(compute=False)
    y_is_salary_journal = fields.Boolean(string="Is Salary Journal",copy=False)

    @api.depends('type')
    def _get_seq_mand(self):
        for rec in self:
            rec.y_make_seq_mandetory = False
            if rec.type in ('cash','bank'):
                rec.y_make_seq_mandetory = bool(self.env['ir.config_parameter'].sudo().get_param('account_base.y_enable_custom_sequence')) or False

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_invoice_user_id = fields.Many2one(string='Salesperson',comodel_name='res.users',related="move_id.invoice_user_id",store=True)
    y_partner_name = fields.Char(related="partner_id.commercial_partner_id.name",store=True)

    # def _create_exchange_difference_moves(self, exchange_diff_values_list):

    #     moves = super()._create_exchange_difference_moves(exchange_diff_values_list)
    #     for move in moves:
    #         if move.line_ids and move.line_ids[0].move_id:
    #             move.ref = move.line_ids[0].move_id.name
    #     return moves


    def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None, **kwargs):
        result = super()._prepare_exchange_difference_move_vals(amounts_list,company=company,exchange_date=exchange_date,**kwargs)
        if result and result.get('move_values') and self:
            reference = self[0].move_id.name
            result['move_values']['ref'] = reference
        return result


    

class AccountMove(models.Model):
    _inherit = 'account.move'

    y_journal_type = fields.Selection(related='journal_id.type', readonly=False, string='Journal Type')
    y_is_salary_journal = fields.Boolean(string="Is Salary Journal",copy=False,related="journal_id.y_is_salary_journal")


    y_payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', compute="get_payment_type",inverse='_inverse_get_payment_type',store=True)

    @api.depends('origin_payment_id.payment_type')
    def get_payment_type(self):
        for move in self:
            move.y_payment_type = move.origin_payment_id.payment_type or False


    def _inverse_get_payment_type(self):
        for each in self:
            if each.y_payment_type:
                each.y_payment_type=each.y_payment_type
            else:
                each.y_payment_type = False

    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        pass

    def _post(self, soft=True):
        for rec in self:
            if not rec.posted_before or (rec.origin_payment_id and rec.name == '/'):
                name = 'SEQUENCE NOT MAPPED'
                if rec.move_type in ('in_invoice','in_refund','in_receipt'):
                    if not rec.invoice_date:
                        raise UserError(_('The Bill/Refund date is required to validate this document.'))

                    if rec.date < rec.invoice_date:
                        raise UserError(_('Accounting Date should not less than Bill date !'))
                if rec.y_journal_type in ('cash','bank'):
                    if rec.y_payment_type == 'inbound' and rec.journal_id.sudo().y_in_sequence_id:
                        name = rec.journal_id.sudo().y_in_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()
                    elif rec.y_payment_type == 'outbound' and rec.journal_id.sudo().y_out_sequence_id:
                        name = rec.journal_id.sudo().y_out_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()
                    elif rec.journal_id.sudo().y_recon_sequence_id:
                        name = rec.journal_id.sudo().y_recon_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()
                
                elif rec.move_type in ('in_refund','out_refund') and rec.journal_id.sudo().y_refund_sequence_id:
                    name = rec.journal_id.sudo().y_refund_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()
                elif rec.move_type in ('in_invoice','out_invoice') and rec.journal_id.sudo().y_name_sequence_id:
                    name = rec.journal_id.sudo().y_name_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()
                elif rec.move_type == 'entry':
                    if rec.journal_id.sudo().y_name_sequence_id:
                        name = rec.journal_id.sudo().y_name_sequence_id.with_context(ir_sequence_date=rec.date).next_by_id()

                if name == "SEQUENCE NOT MAPPED":
                    raise ValidationError(_(""" Sequence Not Mapped for {} {} Journal {}""".format(rec.journal_id.name,rec.journal_id.id,rec.company_id.name)))
                rec.name = name
                if rec.origin_payment_id:
                    rec.env.cr.execute("""UPDATE account_payment SET name = '{}' WHERE id = {}""".format(name,rec.origin_payment_id.id))
                    
        return super(AccountMove, self)._post(soft)

    def action_post(self):
        for rec in self:
            tz_name = rec._context.get('tz') or rec.env.user.tz
            timezone = pytz.timezone(tz_name)
            now = datetime.now(tz = timezone)
            current_date = now.date()
            if rec.date:            
                if rec.date > current_date:
                    raise UserError('Accounting date should not be grater than current date!')
        return super(AccountMove,self).action_post() 

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        if move.y_payment_type == 'outbound':
            res['y_payment_type'] = 'inbound'
        if move.y_payment_type == 'inbound':
            res['y_payment_type'] = 'outbound'
        return res

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def button_post(self):
        for line in self.line_ids:
            if line.amount < 0:
                line.move_id.y_payment_type = 'outbound'
            else:
                line.move_id.y_payment_type = 'inbound'
        return super(AccountBankStatement, self).button_post()
    
    

class CashRoundoff(models.Model):
    _inherit = "account.cash.rounding"

    y_is_default_round_off = fields.Boolean(string="Default Round-off")

class AccountMoveCashRounding(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for move in self:
            if move.move_type in ['in_invoice','in_refund'] and  not move.ref:
                raise ValidationError(_("Bill Reference is mandatory to post this document"))
        return super().action_post()


    def write(self,vals):
        res = super().write(vals)
        if vals.get('company_id') or vals.get('currency_id'):
            self.onchange_currency_for_roundoff()
        return res

    @api.onchange('company_id','currency_id')
    def onchange_currency_for_roundoff(self):
        for rec in self:
            if rec.currency_id:
                if rec.currency_id == rec.company_id.currency_id:
                    cash_rouding_method = self.env['account.cash.rounding'].search([('y_is_default_round_off','=',True)],limit=1)
                    if cash_rouding_method:
                        rec.write({'invoice_cash_rounding_id':cash_rouding_method.id})
                else:
                    rec.write({'invoice_cash_rounding_id':False})


       

  
  