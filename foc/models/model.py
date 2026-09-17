# -*- coding: utf-8 -*-
import json
from itertools import chain
from lxml import etree
import odoo
from odoo import fields, models, api, _
from odoo.exceptions import  UserError, ValidationError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    y_tax_counterpart_account_id = fields.Many2one('account.account',string="GST Credit Reversal Account")

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    y_is_free_of_charge_visible = fields.Boolean(copy=False,default=False,store=True)
    y_is_free_of_charge = fields.Boolean()

 
class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_line_ids', 'journal_id')
    def onchange_invoice_lines_or_journal(self):
        for move in self:
            if move.journal_id.y_tax_counterpart_account_id:
                for line in move.invoice_line_ids:
                    line.y_is_free_of_charge_visible = True



    
    def button_draft(self):
        for invoice in self:
            if any(invoice.line_ids.filtered(lambda x: x.y_is_free_of_charge == True and x.account_type == 'income' or x.account_id.id == invoice.journal_id.y_tax_counterpart_account_id.id)):
                free_charge_tax_ids = invoice.line_ids.filtered(
                    lambda x: x.y_is_free_of_charge == True and x.account_type == 'income' or x.account_id.id == invoice.journal_id.y_tax_counterpart_account_id.id
                )
                if free_charge_tax_ids:
                    invoice.env.cr.execute("DELETE FROM account_move_line WHERE id IN {}".format(tuple(free_charge_tax_ids.ids) + (0,)))
                    line_ids_vals = []
                    receivable_account_id = invoice.line_ids.filtered(lambda x:x.account_id.account_type == 'asset_receivable' and x.y_is_free_of_charge == True).mapped('account_id')
                    receivable_line_id = invoice.line_ids.filtered(lambda x:x.account_id == receivable_account_id and x.y_is_free_of_charge == True)
                    if receivable_line_id:
                        if invoice.invoice_line_ids:
                            value = sum(line.price_total for line in invoice.invoice_line_ids)
                            line_ids_vals.append((1,receivable_line_id.id,{'account_id':receivable_line_id.account_id.id,'balance':value,'credit':0,'debit':value,'analytic_distribution':receivable_line_id.analytic_distribution,'y_is_free_of_charge':False,'display_type':receivable_line_id.display_type}))
                    if line_ids_vals:
                        invoice.with_context({'skip_readonly_check':True}).write({'line_ids':line_ids_vals})
        return super(AccountMove,self).button_draft()

    def action_post(self):
        for invoice in self:
            if any(invoice.invoice_line_ids.filtered(lambda x:x.y_is_free_of_charge_visible == True)):
                if not invoice.journal_id.y_tax_counterpart_account_id and any(invoice.invoice_line_ids.filtered(lambda x:x.y_is_free_of_charge_visible == True)):
                    raise UserError("Tax Counterpart Account Not Configured...!")
                line_ids_vals = []
                tot_free_of_charge = sum(invoice.invoice_line_ids.mapped('price_unit'))            
                for payable in invoice.line_ids.filtered(lambda x:x.y_is_free_of_charge_visible == True):
                    value = payable.credit
                    line_ids_vals.append((0,0,{'account_id':payable.account_id.id,'balance':value,'debit':value,'credit':0,'analytic_distribution':payable.analytic_distribution,'y_is_free_of_charge':True,'display_type':'tax'}))

                tax_total_value = sum(invoice.line_ids.filtered(lambda x:x.tax_line_id).mapped('credit'))
                if tax_total_value > 0:
                    line_ids_vals.append((0,0,{'account_id':invoice.journal_id.y_tax_counterpart_account_id.id,'balance':tax_total_value,'debit':tax_total_value,'credit':0,'analytic_distribution':payable.analytic_distribution,'y_is_free_of_charge':True,'display_type':'tax'}))

                receivable_account_id = invoice.line_ids.filtered(lambda x:x.account_id.account_type == 'asset_receivable' and x.y_is_free_of_charge == False).mapped('account_id')
                receivable_line_id = invoice.line_ids.filtered(lambda x:x.account_id == receivable_account_id and x.y_is_free_of_charge == False)
                if receivable_line_id:
                    if receivable_line_id.debit != tot_free_of_charge:
                        if invoice.invoice_line_ids:
                            value = receivable_line_id.debit
                            line_ids_vals.append((1,receivable_line_id.id,{'account_id':receivable_line_id.account_id.id,'balance':0,'credit':0,'debit':0,'y_is_free_of_charge':True,'analytic_distribution':receivable_line_id.analytic_distribution,'display_type':receivable_line_id.display_type}))
                if line_ids_vals:
                    invoice.write({'line_ids':line_ids_vals})
        res = super(AccountMove,self).action_post()

        self.line_ids.filtered(lambda x:x.account_id.account_type == 'asset_receivable' and x.y_is_free_of_charge == True).write({
            'amount_residual_currency': 0.0,
            'amount_currency': 0.0,
        })

        return res

        
        
    