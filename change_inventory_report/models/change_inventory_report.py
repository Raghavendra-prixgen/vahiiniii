# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import logging

_logger = logging.getLogger(__name__)


class ChangeInventoryReport(models.Model):
    _name = 'change.inventory.report'
    _description = 'Change Inventory Report'
    _auto = False
    _order = 'y_reference'

    y_reference = fields.Char(string='Reference', readonly=True)
    y_debit = fields.Float(string='Debit', digits=(16, 2), readonly=True)
    y_credit = fields.Float(string='Credit', digits=(16, 2), readonly=True)
    y_difference = fields.Float(string='Difference', digits=(16, 2), readonly=True)
    y_company = fields.Many2one('res.company', string='Company', readonly=True)
    y_reconcile_status = fields.Selection([
        ('reconciled', 'Reconciled'),
        ('partially_reconciled', 'Partially Reconciled'),
        ('unreconciled', 'Unreconciled'),
    ], string='Reconcile Status', readonly=True)
    y_currency_id = fields.Many2one('res.currency',string='Currency',tracking=True,related="y_company.currency_id", readonly=True)
    y_operation_type = fields.Char(string='Operation Type', readonly=True)
    y_date = fields.Date(string='Date', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW change_inventory_report AS
            SELECT
                ROW_NUMBER() OVER()::integer AS id,
                NULL::varchar AS y_reference,
                0.0::numeric AS y_debit,
                0.0::numeric AS y_credit,
                0.0::numeric AS y_difference,
                NULL::integer AS y_company,
                NULL::varchar AS y_reconcile_status,
                NULL::varchar AS y_operation_type,
                NULL::date AS y_date
                
            WHERE FALSE
        """)

    @api.model
    def _get_report_data(self, date_from, date_to, company_id):
        cr = self.env.cr

        child_ids = self.env['res.company'].search([('id', 'child_of', company_id)]).ids
        company_ids = list(set([company_id] + child_ids))

        cr.execute("""
            SELECT DISTINCT
                (property_stock_account_production_cost_id->>%s)::integer
            FROM product_category
            WHERE property_stock_account_production_cost_id ? %s
        """, [str(company_id), str(company_id)])

        account_ids = [row[0] for row in cr.fetchall() if row[0]]

        if not account_ids:
            return []

        query = """
WITH account_moves AS (
    SELECT
        svl.account_move_id,
        MAX(sm.reference) AS reference,
        MAX(
            COALESCE(
                mppt.name->>'en_US',
                spt.name->>'en_US'
            )
        ) AS operation_type
    FROM stock_valuation_layer svl

    LEFT JOIN stock_move sm
        ON sm.id = svl.stock_move_id

    LEFT JOIN mrp_production mp
        ON mp.id = COALESCE(
            sm.production_id,
            sm.raw_material_production_id
        )

    LEFT JOIN stock_picking_type mppt
        ON mppt.id = mp.picking_type_id

    LEFT JOIN stock_picking sp
        ON sp.id = sm.picking_id

    LEFT JOIN stock_picking_type spt
        ON spt.id = sp.picking_type_id

    WHERE svl.account_move_id IS NOT NULL

    GROUP BY svl.account_move_id
)

SELECT
    ROW_NUMBER() OVER(
        ORDER BY COALESCE(amv.reference, am.name)
    )::integer AS id,

    COALESCE(
        amv.reference,
        am.name
    ) AS y_reference,

    MIN(aml.date) AS y_date,
    
    SUM(aml.debit) AS y_debit,
    SUM(aml.credit) AS y_credit,
    SUM(aml.credit) - SUM(aml.debit) AS y_difference,

    aml.company_id AS y_company,
    amv.operation_type AS y_operation_type,
    
    CASE
        WHEN SUM(aml.debit) = 0
             AND SUM(aml.credit) <> 0
        THEN 'unreconciled'

        WHEN SUM(aml.credit) = 0
             AND SUM(aml.debit) <> 0
        THEN 'unreconciled'

        WHEN ABS(SUM(aml.credit) - SUM(aml.debit)) <= 1
        THEN 'reconciled'

        ELSE 'partially_reconciled'
    END AS y_reconcile_status

FROM account_move_line aml

JOIN account_move am
    ON am.id = aml.move_id

LEFT JOIN account_moves amv
    ON amv.account_move_id = aml.move_id

WHERE aml.account_id = ANY(%s)
  AND aml.date BETWEEN %s AND %s
  AND aml.company_id = ANY(%s)
  AND am.state = 'posted'

GROUP BY
    COALESCE(amv.reference, am.name),
    aml.company_id,
    amv.operation_type

ORDER BY
    y_reference
        """
        cr.execute(query, [account_ids, date_from, date_to, company_ids])
        cols = [d[0] for d in cr.description]
        rows = [dict(zip(cols, row)) for row in cr.fetchall()]
        print('rows--------------',rows)
        for r in rows:
            if r.get('y_reference') == 'U1/SBC/00279':
                _logger.info("FOUND U1/SBC/00279 ===== %s", r)
        return rows