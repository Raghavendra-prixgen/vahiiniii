# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
from collections import defaultdict
import logging

from odoo import api, fields, models, _
from odoo.tools.misc import format_date
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'


    def view_followup_report(self):
        self.ensure_one()
        return {
            'name': _("Follow up report for %s", self.display_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [[self.env.ref('account_followup_addon.customer_statements_form_view').id, 'form']],
            'res_model': 'res.partner',
            'res_id': self.id,
        }





    @api.onchange('unreconciled_aml_ids')
    def _onchange_total(self):
        today = fields.Date.context_today(self)
        total_overdue = 0
        total_due = 0
        for aml in self.unreconciled_aml_ids:
            is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
            if self.env.company in aml.company_id.parent_ids and not aml.blocked:
                total_due += aml.amount_residual
                if is_overdue:
                    total_overdue += aml.amount_residual
        self.total_due = total_due
        self.total_overdue = total_overdue

    @api.depends('invoice_ids')
    @api.depends_context('company', 'allowed_company_ids')
    def _compute_total_due(self):
        due_data = defaultdict(float)
        overdue_data = defaultdict(float)
        unreconciled_aml_ids = defaultdict(list)
        for overdue, partner, blocked, amount_residual_sum, aml_ids in self.env['account.move.line']._read_group(
            domain=self._get_unreconciled_aml_domain(),
            groupby=['followup_overdue', 'partner_id', 'blocked'],
            aggregates=['amount_residual:sum', 'id:array_agg'],
        ):
            unreconciled_aml_ids[partner] += aml_ids
            if not blocked:
                due_data[partner] += amount_residual_sum
                if overdue:
                    overdue_data[partner] += amount_residual_sum

        for partner in self:
            partner.total_due = due_data.get(partner, 0.0)
            partner.total_overdue = overdue_data.get(partner, 0.0)
            partner.unreconciled_aml_ids = self.env['account.move.line'].browse(unreconciled_aml_ids.get(partner, []))

    def _set_followup_line_on_unreconciled_amls(self):
        today = fields.Date.context_today(self)
        for partner in self:
            current_followup_line = partner.followup_line_id
            previous_followup_line = self.env['account_followup.followup.line'].search([('delay', '<', current_followup_line.delay), ('company_id', 'parent_of', self.env.company.id)], order='delay desc', limit=1)
            for unreconciled_aml in partner.unreconciled_aml_ids:
                if not unreconciled_aml.blocked:
                    unreconciled_aml.followup_line_id = previous_followup_line
                    # When a specific followup line is manually selected, we consider the followup as processed
                    unreconciled_aml.last_followup_date = today


    def _included_unreconciled_aml_max_followup(self):
        """ Computes the maximum delay in days and the highest level of followup (followup line with highest delay) of all the unreconciled amls included.
        Also returns the delay for the next level (after the highest_followup_line), the most delayed aml and a boolean specifying if any invoice is overdue.
        :return dict with key/values: most_delayed_aml, max_delay, highest_followup_line, next_followup_delay, has_overdue_invoices
        """
        self.ensure_one()
        today = fields.Date.context_today(self)
        highest_followup_line = None
        most_delayed_aml = self.env['account.move.line']
        first_followup_line = self._get_first_followup_level()
        # Minimum value for delay, will always be smaller than any other delay
        max_delay = first_followup_line.delay - 1
        has_overdue_invoices = False
        for aml in self.unreconciled_aml_ids:
            aml_delay = (today - (aml.date_maturity or aml.date)).days

            is_overdue = aml_delay > 0
            if is_overdue:
                has_overdue_invoices = True

            if self.env.company in aml.company_id.parent_ids and not aml.blocked:
                if aml.followup_line_id and aml.followup_line_id.delay >= (highest_followup_line or first_followup_line).delay:
                    highest_followup_line = aml.followup_line_id
                max_delay = max(max_delay, aml_delay)
                if most_delayed_aml.amount_residual < aml.amount_residual:
                    most_delayed_aml = aml
        followup_lines_info = self._get_followup_lines_info()
        next_followup_delay = None
        if followup_lines_info:
            key = highest_followup_line.id if highest_followup_line else None
            current_followup_line_info = followup_lines_info.get(key)
            next_followup_delay = current_followup_line_info.get('next_delay')
        return {
            'most_delayed_aml': most_delayed_aml,
            'max_delay': max_delay,
            'highest_followup_line': highest_followup_line,
            'next_followup_delay': next_followup_delay,
            'has_overdue_invoices': has_overdue_invoices,
        }

    def _get_invoices_to_print(self, options):
        self.ensure_one()
        if not options:
            options = {}
        invoices_to_print = self._get_included_unreconciled_aml_ids().move_id.filtered(lambda l: l.is_invoice(include_receipts=True))
        if options.get('manual_followup'):
            # For manual reminders, only print invoices with the selected attachments
            return invoices_to_print.filtered(lambda inv: inv.message_main_attachment_id.id in options.get('attachment_ids'))
        return invoices_to_print.filtered(lambda inv: inv.message_main_attachment_id)

    def _get_included_unreconciled_aml_ids(self):
        self.ensure_one()
        return self.unreconciled_aml_ids.filtered(lambda aml: not aml.blocked)

    def _update_next_followup_action_date(self, followup_line):
        """Updates the followup_next_action_date of the right account move lines
        """
        self.ensure_one()
        if followup_line:
            next_date = followup_line._get_next_date()
            self.followup_next_action_date = datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT)
            msg = _('Next Reminder Date set to %s', format_date(self.env, self.followup_next_action_date))
            self.message_post(body=msg)

        today = fields.Date.context_today(self)
        previous_levels = self.env['account_followup.followup.line'].search([('delay', '<=', followup_line.delay), ('company_id', '=', self.env.company.id)])
        for aml in self._get_included_unreconciled_aml_ids().filtered('date_maturity'):
            eligible_levels = previous_levels.filtered(lambda level: (today - aml.date_maturity).days >= level.delay)
            if eligible_levels:
                aml.followup_line_id = max(eligible_levels, key=lambda level: level.delay)

    def open_action_followup(self):
        self.ensure_one()
        return {
            'name': _("Overdue Payments for %s", self.display_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [[self.env.ref('account_followup.customer_statements_form_view').id, 'form']],
            'res_model': 'res.partner',
            'res_id': self.id,
        }

    def _get_followup_data_query(self, partner_ids=None):
        self.env['account.move.line'].check_access('read')
        self.env['account.move.line'].flush_model()
        self.env['res.partner'].flush_model()
        self.env['account_followup.followup.line'].flush_model()
        ResPartner = self.env['res.partner'].with_company(self.env.company.root_id.id)
        return f"""
            SELECT partner.id as partner_id,
                   ful.id as followup_line_id,
                   CASE WHEN partner.balance <= 0 THEN 'no_action_needed'
                        WHEN in_need_of_action_aml.id IS NOT NULL AND (followup_next_action_date IS NULL OR followup_next_action_date <= %(current_date)s) THEN 'in_need_of_action'
                        WHEN exceeded_unreconciled_aml.id IS NOT NULL THEN 'with_overdue_invoices'
                        ELSE 'no_action_needed' END as followup_status
            FROM (
          SELECT partner.id,
                 {self.env.cr.mogrify(ResPartner._field_to_sql('partner', 'followup_next_action_date')).decode(self.env.cr.connection.encoding)} AS followup_next_action_date,
                 MAX(COALESCE(next_ful.delay, ful.delay)) as followup_delay,
                 SUM(aml.balance) as balance
            FROM res_partner partner
            JOIN account_move_line aml ON aml.partner_id = partner.id
            JOIN account_account account ON account.id = aml.account_id
       LEFT JOIN account_followup_followup_line ful ON ful.id = aml.followup_line_id
       LEFT JOIN account_followup_followup_line next_ful ON next_ful.id = (
                    SELECT next_ful.id
                      FROM account_followup_followup_line next_ful
                     WHERE next_ful.delay > COALESCE(ful.delay, %(min_delay)s - 1)
                       AND next_ful.company_id = %(root_company_id)s
                  ORDER BY next_ful.delay ASC
                     LIMIT 1
                 )
           WHERE account.deprecated IS NOT TRUE
             AND account.account_type = 'asset_receivable'
             AND aml.parent_state = 'posted'
             AND aml.reconciled IS NOT TRUE
             AND aml.blocked IS FALSE
             AND aml.company_id = ANY(%(company_ids)s)
             {"" if partner_ids is None else "AND aml.partner_id IN %(partner_ids)s"}
        GROUP BY partner.id
            ) partner
            LEFT JOIN account_followup_followup_line ful ON ful.delay = partner.followup_delay AND ful.company_id = %(root_company_id)s
            -- Get the followup status data
            LEFT OUTER JOIN LATERAL (
                SELECT line.id
                  FROM account_move_line line
                  JOIN account_account account ON line.account_id = account.id
             LEFT JOIN account_followup_followup_line ful ON ful.id = line.followup_line_id
                 WHERE line.partner_id = partner.id
                   AND account.account_type = 'asset_receivable'
                   AND account.deprecated IS NOT TRUE
                   AND line.parent_state = 'posted'
                   AND line.reconciled IS NOT TRUE
                   AND line.balance > 0
                   AND line.blocked IS FALSE
                   AND line.company_id = ANY(%(company_ids)s)
                   AND COALESCE(ful.delay, %(min_delay)s - 1) <= partner.followup_delay
                   AND COALESCE(line.date_maturity, line.date) + COALESCE(ful.delay, %(min_delay)s - 1) < %(current_date)s
                 LIMIT 1
            ) in_need_of_action_aml ON true
            LEFT OUTER JOIN LATERAL (
                SELECT line.id
                  FROM account_move_line line
                  JOIN account_account account ON line.account_id = account.id
                 WHERE line.partner_id = partner.id
                   AND account.account_type = 'asset_receivable'
                   AND account.deprecated IS NOT TRUE
                   AND line.parent_state = 'posted'
                   AND line.reconciled IS NOT TRUE
                   AND line.balance > 0
                   AND line.blocked IS FALSE
                   AND line.company_id = ANY(%(company_ids)s)
                   AND COALESCE(line.date_maturity, line.date) < %(current_date)s
                 LIMIT 1
            ) exceeded_unreconciled_aml ON true
        """, {
            'company_ids': self.env.company.search([('id', 'child_of', self.env.company.id)]).ids,
            'root_company_id': self.env.company.root_id.id,
            'partner_ids': tuple(partner_ids or []),
            'current_date': fields.Date.context_today(self),  # Allow mocking the current day for testing purpose.
            'min_delay': self._get_first_followup_level().delay or 0,
        }


