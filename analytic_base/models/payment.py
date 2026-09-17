# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_round, float_compare
# import logging
# _logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _name = 'account.payment.register'
    _inherit = ['account.payment.register','analytic.mixin']

    def action_create_payments(self):
        for move in self:
            move._validate_analytic_distribution()
        return super(AccountPaymentRegister, self).action_create_payments()
    
    def _validate_analytic_distribution(self):
        for line in self:
            #enforce analytic validation
            line.with_context(validate_analytic = True)._validate_distribution(**{
                'business_domain': 'payment',
                'company_id': line.company_id.id,
            })
    
    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals['analytic_distribution'] = self.analytic_distribution

        return payment_vals


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment','analytic.mixin']

    # @api.depends('expense_sheet_id')
    # def _compute_analytic_distribution(self):
    #     for pay in self:
    #         distribution = False
            
    #         if pay.expense_sheet_id.expense_line_ids:
    #             distribution = pay.expense_sheet_id.expense_line_ids[0].analytic_distribution
            
    #         pay.analytic_distribution = distribution or pay.analytic_distribution

    def action_post(self):
        for move in self:
            move._validate_analytic_distribution()
        return super(AccountPayment, self).action_post()
    
    def _validate_analytic_distribution(self):
        for line in self:
            #enforce analytic validation
            line.with_context(validate_analytic = True)._validate_distribution(**{
                'business_domain': 'payment',
                'company_id': line.company_id.id,
            })