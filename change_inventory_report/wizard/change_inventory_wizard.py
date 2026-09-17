# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChangeInventoryWizard(models.TransientModel):
    _name = 'change.inventory.wizard'
    _description = 'Change Inventory Report Wizard'

    y_date_from = fields.Date(string='From Date', required=True, default=lambda self: fields.Date.context_today(self).replace(day=1),)
    y_date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.context_today,
    )
    y_company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,)

    def action_confirm(self):
        self.ensure_one()
        if self.y_date_from > self.y_date_to:
            raise UserError("'From Date' must be earlier than or equal to 'To Date'.")

        Report = self.env['change.inventory.report']
        rows = Report._get_report_data(self.y_date_from, self.y_date_to, self.y_company_id.id)

        if not rows:
            raise UserError(
                "No inventory change records found for the selected period and company.\n\n"
                "Please verify:\n"
                "• Product categories have 'Production Cost Account' configured.\n"
                "• There are posted journal entries on those accounts in the selected date range."
            )

        cr = self.env.cr
        if rows:
            value_rows = []
            for r in rows:
                ref = (r['y_reference'] or '').replace("'", "''")
                operation_type = r.get('y_operation_type') or ''

                if isinstance(operation_type, dict):
                    operation_type = operation_type.get('en_US') or next(iter(operation_type.values()), '')

                operation_type = str(operation_type).replace("'", "''")
                value_rows.append(
                    f"""(
                        {r['id']},
                        '{ref}',
                        {r['y_debit']},
                        {r['y_credit']},
                        {r['y_difference']},
                        {r['y_company']},
                        '{r['y_reconcile_status']}',
                        '{operation_type}',
                        '{r['y_date']}'
                    )"""
                )
            values_sql = ',\n            '.join(value_rows)
            view_sql = f"""
                CREATE OR REPLACE VIEW change_inventory_report AS
                SELECT
                    id::integer,
                    y_reference::varchar,
                    y_debit::numeric,
                    y_credit::numeric,
                    y_difference::numeric,
                    y_company::integer,
                    y_reconcile_status::varchar,
                    y_operation_type::varchar,
                    y_date::date
                FROM (
                    VALUES
                    {values_sql}
                ) AS t(
                    id,
                    y_reference,
                    y_debit,
                    y_credit,
                    y_difference,
                    y_company,
                    y_reconcile_status,
                    y_operation_type,
                    y_date
                )
            """
        else:
            view_sql = """
                CREATE OR REPLACE VIEW change_inventory_report AS
                SELECT
                    ROW_NUMBER() OVER()::integer AS id,
                    NULL::varchar AS y_reference,
                    0::numeric AS y_debit,
                    0::numeric AS y_credit,
                    0::numeric AS y_difference,
                    NULL::integer AS y_company,
                    NULL::varchar AS y_reconcile_status,
                    NULL::varchar AS y_operation_type,
                    NULL::date AS y_date
                WHERE FALSE
            """
        cr.execute(view_sql)

        # refresh cache
        self.env['change.inventory.report'].invalidate_model()

        # debug
        cr.execute("""
            SELECT COUNT(*)
            FROM change_inventory_report
        """)
        _logger.info(
            "REPORT COUNT ===== %s",
            cr.fetchone()[0]
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Inventory Report',
            'res_model': 'change.inventory.report',
            'view_mode': 'list',
            'views': [(False, 'list')],
            'target': 'current',
            'context': {
                'date_from': str(self.y_date_from),
                'date_to': str(self.y_date_to),
                'company_id': self.y_company_id.id,
                'company_name': self.y_company_id.name,
                # 'group_by': 'y_reference',
            },
        }
