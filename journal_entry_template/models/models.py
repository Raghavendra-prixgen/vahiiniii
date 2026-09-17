# -*- coding: utf-8 -*-

from odoo import models, fields, api
from contextlib import ExitStack, contextmanager
from odoo import api, fields, models, _, Command, SUPERUSER_ID, modules, tools
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools import (
    create_index,
    date_utils,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    index_exists,
    OrderedSet,
    SQL,
)
class AccountMove(models.Model):
    _inherit = "account.move"

    journal_entry_template_id = fields.Many2one('journal.entry.template')

    @api.onchange('journal_entry_template_id')
    def _onchange_journal_entry_template_id(self):
        if self.journal_entry_template_id:
            if not self._origin:
                raise ValidationError("Please save your changes first")
            else:
                self.line_ids = False
                new_lines = self.env['account.move.line']
                self.date = self.journal_entry_template_id.date
                self.journal_id = self.journal_entry_template_id.journal_id.id
                # self.write({'date':self.journal_entry_template_id.date,
                #             'journal_id':self.journal_entry_template_id.journal_id.id,
                #             })

                line_vals = []
                for line in self.journal_entry_template_id.line_ids:
                    line_vals.append({'account_id':line.account_id.id,
                                           'name':line.name,
                                           'debit':line.debit,
                                           'credit':line.credit,
                                           'balance': line.balance,
                                           'partner_id':line.partner_id.id,
                                           'analytic_distribution':line.analytic_distribution,
                                           })
                for line_val in line_vals:
                    new_line = new_lines.new(line_val)
                    new_lines += new_line
                self.line_ids = new_lines
                

class JournalEntryTemplate(models.Model):
    _name = 'journal.entry.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Journal Entry Template'

    active = fields.Boolean(default=True,tracking=True,copy=False)
    name = fields.Char(string="Name",tracking=True)
    date = fields.Date(
        string='Date',
        copy=False,
        tracking=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        check_company=True,tracking=True
        )

    line_ids = fields.One2many(
        'journal.entry.template.line',
        'move_id',
        string='Journal Items',
        copy=True

    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',tracking=True
    )
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='company_id.currency_id', readonly=True,tracking=True
    )

    y_start_date = fields.Date(string="Start Date",tracking=True)
    y_end_date = fields.Date(string="End Date",tracking=True)

    @api.constrains('y_start_date','y_end_date')
    def _check_dates(self):
        if self.y_end_date and self.y_start_date:
            if self.y_end_date < self.y_start_date:
                raise ValidationError(_("""End Date Date should not be less than Start Date"""))

    @api.constrains('name','company_id','active')
    def check_journal_entry_template_name(self):
        for rec in self:
            docs=rec.env['journal.entry.template'].search([('name','=',rec.name)])
            if len(docs) > 1:
                raise ValidationError(_("""name already exists!"""))

    @api.constrains('name','active','company_id','journal_id')
    def _check_duplicate(self):
        domain = [('journal_id','=',self.journal_id.id),('name','=',self.name),'|',('company_id','=',self.company_id.id),('company_id','=',False)]
        existing_id = self.env['journal.entry.template'].search(domain)
        if len(existing_id) > 1:
            raise UserError (_("Oops, looks like we've got a duplicate record!"))


    # @contextmanager
    # def _check_balanced(self, container):
    #     ''' Assert the move is fully balanced debit = credit.
    #     An error is raised if it's not the case.
    #     '''
    #     unbalanced_moves = self._get_unbalanced_moves(container)
    #     if unbalanced_moves:
    #         error_msg = _("An error has occurred.")
    #         for move_id, sum_debit, sum_credit in unbalanced_moves:
    #             move = self.browse(move_id)
    #             error_msg += _(
    #                 "\n\n"
    #                 "The move (%(move)s) is not balanced.\n"
    #                 "The total of debits equals %(debit_total)s and the total of credits equals %(credit_total)s.\n"
    #                 "You might want to specify a default account on journal \"%(journal)s\" to automatically balance each move.",
    #                 move=move.display_name,
    #                 debit_total=format_amount(self.env, sum_debit, move.company_id.currency_id),
    #                 credit_total=format_amount(self.env, sum_credit, move.company_id.currency_id),
    #                 journal=move.journal_id.name)
    #         raise UserError(error_msg)

    # def _get_unbalanced_moves(self, container):
    #     moves = container['records'].filtered(lambda move: move.line_ids)
    #     if not moves:
    #         return

    #     # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
    #     # are already done. Then, this query MUST NOT depend on computed stored fields.
    #     # It happens as the ORM calls create() with the 'no_recompute' statement.
    #     self.env['account.move.line'].flush_model(['debit', 'credit', 'balance', 'currency_id', 'move_id'])
    #     return self.env.execute_query(SQL('''
    #         SELECT line.move_id,
    #                ROUND(SUM(line.debit), currency.decimal_places) debit,
    #                ROUND(SUM(line.credit), currency.decimal_places) credit
    #           FROM journal_entry_template_line line
    #           JOIN journal_entry_template move ON move.id = line.move_id
    #           JOIN res_company company ON company.id = move.company_id
    #           JOIN res_currency currency ON currency.id = company.currency_id
    #          WHERE line.move_id IN %s
    #       GROUP BY line.move_id, currency.decimal_places
    #         HAVING ROUND(SUM(line.balance), currency.decimal_places) != 0
    #     ''', tuple(moves.ids)))

    # @api.model_create_multi
    # def create(self, vals_list):
    #     container = {'records': self}
    #     self._check_balanced(container)
    #     return super().create(vals_list)

    # def write(self, vals):
    #     container = {'records': self}
    #     self._check_balanced(container)
    #     return super().write(vals)


class JournalEntryTemplateLine(models.Model):
    _name = 'journal.entry.template.line'
    _inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]
    _description = 'Journal Entry Template'

    sequence = fields.Integer(required=True,default=10)
    move_id = fields.Many2one(
        comodel_name='journal.entry.template',
        string='Journal Entry Template',
        )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        tracking=True,
    )
    name = fields.Char(
        string='Label',
        tracking=True,
    )
    company_currency_id = fields.Many2one(
        string='Company Currency',
        related='move_id.company_currency_id', readonly=True, store=True, precompute=True,
    )
    debit = fields.Monetary(
        string='Debit',
        compute='_compute_debit_credit', inverse='_inverse_debit', store=True, precompute=True,
        currency_field='company_currency_id',
    )
    credit = fields.Monetary(
        string='Credit',
        compute='_compute_debit_credit', inverse='_inverse_credit', store=True, precompute=True,
        currency_field='company_currency_id',
    )
    balance = fields.Monetary(
        string='Balance',
        compute='_compute_balance', store=True, readonly=False, precompute=True,
        currency_field='company_currency_id',
        tracking=True,
    )
    

    analytic_distribution = fields.Json()

    display_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('cogs', 'Cost of Goods Sold'),
            ('tax', 'Tax'),
            ('discount', "Discount"),
            ('rounding', "Rounding"),
            ('payment_term', 'Payment Term'),
            ('line_section', 'Section'),
            ('line_note', 'Note'),
            ('epd', 'Early Payment Discount')
        ],
        compute='_compute_display_type', store=True, readonly=False, precompute=True,
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner')

    @api.constrains('credit','debit','move_id')
    def _check_credit_debit(self):
        for line in self:
            if abs(sum(line.move_id.line_ids.mapped('debit'))) != abs(sum(line.move_id.line_ids.mapped('credit'))):
                error_msg = _(
                                "The lines are not balanced.\n"
                                "The total of debits equals %(debit_total)s and the total of credits equals %(credit_total)s.",
                                debit_total=sum(line.move_id.line_ids.mapped('debit')),
                                credit_total=sum(line.move_id.line_ids.mapped('credit'))
                                )
                raise ValidationError(error_msg)

    @api.depends('balance', 'move_id')
    def _compute_debit_credit(self):
        for line in self:
            line.debit = line.balance if line.balance > 0.0 else 0.0
            line.credit = -line.balance if line.balance < 0.0 else 0.0

    @api.onchange('debit')
    def _inverse_debit(self):
        for line in self:
            if line.debit:
                line.credit = 0
            line.balance = line.debit - line.credit

    @api.onchange('credit')
    def _inverse_credit(self):
        for line in self:
            if line.credit:
                line.debit = 0
            line.balance = line.debit - line.credit

    @api.depends('move_id')
    def _compute_balance(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                line.balance = False
            else:
                line.balance = 0

    @api.depends('move_id')
    def _compute_display_type(self):
        for line in self.filtered(lambda l: not l.display_type):
            account_set = self.env.cache.contains(line, line._fields['account_id'])
            line.display_type = ('payment_term' if account_set and line.account_id.account_type in ['asset_receivable', 'liability_payable'] else 'product')








    