# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class journal_entry_domain_patch(models.Model):
    _inherit = 'account.move'

    y_is_direct_expense_income_voucher = fields.Boolean()

    @api.model
    def create(self,vals):
        if self._context.get('new_jv'):
            vals['y_is_direct_expense_income_voucher'] = True
        return super().create(vals)

    #standard code
    def _search_default_journal(self):
        journal = super()._search_default_journal()
        if self._context.get('new_jv'):
            journal = journal.filtered(lambda x:x.type in ('bank', 'cash'))
        return journal

   
    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            if m._context.get('new_jv'):
                alt_journals =  ('cash','bank')
                company = m.company_id or self.env.company
                m.suitable_journal_ids = self.env['account.journal'].search([
                    *self.env['account.journal']._check_company_domain(company),
                    ('type', '=', alt_journals),
                ])
            else:
                super()._compute_suitable_journal_ids()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    #overriding standard
    def _compute_account_id(self):
        if not self._context.get('new_jv'):
            super()._compute_account_id()
        #this is custom code
        else:
            line.account_id = False
            for line in self:
                if line.payment_id.payment_type == 'outbound':
                    if line.move_id.journal_id.outbound_payment_method_line_ids:
                        if line.move_id.journal_id.outbound_payment_method_line_ids[0].payment_account_id:
                            line.account_id = line.move_id.journal_id.outbound_payment_method_line_ids[0].payment_account_id.id
                        else:
                            account_obj = line.env.company.account_journal_payment_credit_account_id

                            line.account_id  = account_obj.id
                    else:
                        account_obj = line.env.company.account_journal_payment_credit_account_id

                        line.account_id  = account_obj.id
                else:
                    if line.move_id.journal_id.inbound_payment_method_line_ids:
                        if line.move_id.journal_id.inbound_payment_method_line_ids[0].payment_account_id:
                            line.account_id = line.move_id.journal_id.inbound_payment_method_line_ids[0].payment_account_id.id
                        else:
                            account_obj = line.env.company.account_journal_payment_debit_account_id
                            line.account_id  = account_obj.id
                    else:
                        account_obj = line.env.company.account_journal_payment_debit_account_id
                        line.account_id  = account_obj.id

        #######################################
