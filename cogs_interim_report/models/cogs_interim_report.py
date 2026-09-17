# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CogsInterimReport(models.Model):
    _name = "cogs.interim.report"
    _description = "COGS Interim Report"
    _rec_name = "y_sale_id"

    y_sale_id = fields.Many2one("sale.order", string="Sale Order Number", readonly=True)
    y_customer_id = fields.Many2one("res.partner", string="Customer", readonly=True)
    y_delivery_no = fields.Many2one("stock.picking", string="Delivery No", readonly=True)
    y_date_stock_move = fields.Datetime(string="Date of Stock Move", readonly=True)
    y_invoice_ref = fields.Char(string="Invoice / Journal Entry Reference", readonly=True)
    y_credit = fields.Float(string="Credit", readonly=True, digits=(16, 2))
    y_debit = fields.Float(string="Debit", readonly=True, digits=(16, 2))
    y_difference = fields.Float(string="Difference", readonly=True, digits=(16, 2))
    y_status = fields.Selection([
        ("reconciled", "Reconciled"),
        ("partially", "Partially Reconciled"),
        ("unreconciled", "Unreconciled"),
    ], string="Status", readonly=True)
    y_matching = fields.Char(string="Matching", readonly=True)
    y_company_id = fields.Many2one("res.company", string="Company", readonly=True)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, index=True)
    y_currency_id = fields.Many2one('res.currency', string='Currency', tracking=True,
        related="y_company_id.currency_id", readonly=True)

    def _get_report_data(self):
        allowed_companies = (self._context.get("allowed_company_ids") or self.env.user.company_ids.ids)
        cogs_accounts = self.env["account.account"].search([
            ("y_gl_code_type", "=", "asso"),
            ("company_ids", "in", allowed_companies),
        ])

        if not cogs_accounts:
            raise ValidationError("No ASSO account (y_gl_code_type = 'asso') found for the selected companies.")

        account_ids = tuple(cogs_accounts.ids)
        company_ids = tuple(allowed_companies)
        user_id = self.env.user.id

        self._cr.execute("DELETE FROM cogs_interim_report WHERE user_id = %s", (user_id,))

        query = """
                    WITH

                    all_aml AS (
                        SELECT
                            aml.id          AS aml_id,
                            aml.debit       AS debit,
                            aml.credit      AS credit,
                            am.name         AS move_name,
                            aml.company_id  AS company_id
                        FROM account_move_line aml
                        JOIN account_move am
                            ON am.id = aml.move_id
                           AND am.state = 'posted'
                        WHERE aml.account_id IN %(account_ids)s
                          AND aml.company_id IN %(company_ids)s
                          AND (aml.debit > 0 OR aml.credit > 0)
                    ),

                    link_direct AS (
                        SELECT aml.id AS aml_id, sm.picking_id, sol.order_id AS sale_id, 1 AS priority
                        FROM account_move_line aml
                        JOIN account_move am       ON am.id = aml.move_id AND am.state = 'posted'
                        JOIN stock_valuation_layer svl ON svl.account_move_id = am.id
                        JOIN stock_move sm          ON sm.id = svl.stock_move_id AND sm.picking_id IS NOT NULL
                        JOIN sale_order_line sol    ON sol.id = sm.sale_line_id
                        WHERE aml.account_id IN %(account_ids)s AND aml.company_id IN %(company_ids)s
                    ),

                    link_child AS (
                        SELECT aml.id AS aml_id, sm.picking_id, sol.order_id AS sale_id, 2 AS priority
                        FROM account_move_line aml
                        JOIN account_move am            ON am.id = aml.move_id AND am.state = 'posted'
                        JOIN stock_valuation_layer svl_c ON svl_c.account_move_id = am.id
                        JOIN stock_valuation_layer svl_p ON svl_p.id = svl_c.stock_valuation_layer_id
                        JOIN stock_move sm               ON sm.id = svl_p.stock_move_id AND sm.picking_id IS NOT NULL
                        JOIN sale_order_line sol         ON sol.id = sm.sale_line_id
                        WHERE aml.account_id IN %(account_ids)s AND aml.company_id IN %(company_ids)s
                    ),

                    link_cogs_origin AS (
                        SELECT DISTINCT ON (aml.id)
                            aml.id AS aml_id, sm.picking_id, sol.order_id AS sale_id, 3 AS priority
                        FROM account_move_line aml
                        JOIN account_move am        ON am.id = aml.move_id AND am.state = 'posted'
                        JOIN account_move_line rev  ON rev.id = aml.cogs_origin_id
                        JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = rev.id
                        JOIN sale_order_line sol    ON sol.id = rel.order_line_id
                        LEFT JOIN stock_move sm     ON sm.sale_line_id = sol.id
                                                   AND sm.picking_id IS NOT NULL
                                                   AND sm.state = 'done'
                        WHERE aml.account_id IN %(account_ids)s AND aml.company_id IN %(company_ids)s
                        ORDER BY aml.id, sm.id
                    ),

                    link_y_stock_move AS (
                        SELECT aml.id AS aml_id, sm.picking_id, sol.order_id AS sale_id, 4 AS priority
                        FROM account_move_line aml
                        JOIN stock_move sm  ON sm.id = aml.y_stock_move_id AND sm.picking_id IS NOT NULL
                        JOIN sale_order_line sol ON sol.id = sm.sale_line_id
                        WHERE aml.account_id IN %(account_ids)s AND aml.company_id IN %(company_ids)s
                    ),

                    best_link AS (
                        SELECT DISTINCT ON (aml_id) aml_id, picking_id, sale_id
                        FROM (
                            SELECT * FROM link_direct
                            UNION ALL SELECT * FROM link_child
                            UNION ALL SELECT * FROM link_cogs_origin
                            UNION ALL SELECT * FROM link_y_stock_move
                        ) all_links
                        ORDER BY aml_id, priority, picking_id
                    ),

                    aml_linked AS (
                        SELECT a.aml_id, a.debit, a.credit, a.move_name, a.company_id,
                               bl.picking_id, bl.sale_id
                        FROM all_aml a
                        LEFT JOIN best_link bl ON bl.aml_id = a.aml_id
                    ),

                    agg_linked AS (
                        SELECT
                            sale_id, picking_id, company_id,
                            NULL::integer AS orphan_aml_id,
                            SUM(debit)   AS total_debit,
                            SUM(credit)  AS total_credit,
                            string_agg(DISTINCT move_name, ', ' ORDER BY move_name) AS refs
                        FROM aml_linked
                        WHERE sale_id IS NOT NULL OR picking_id IS NOT NULL
                        GROUP BY sale_id, picking_id, company_id
                    ),

                    agg_orphan AS (
                        SELECT
                            NULL::integer AS sale_id, NULL::integer AS picking_id,
                            company_id, aml_id AS orphan_aml_id,
                            debit AS total_debit, credit AS total_credit, move_name AS refs
                        FROM aml_linked
                        WHERE sale_id IS NULL AND picking_id IS NULL
                    ),

                    agg AS (
                        SELECT * FROM agg_linked
                        UNION ALL
                        SELECT * FROM agg_orphan
                    ),

                    so_totals AS (
                        SELECT
                            sale_id,
                            SUM(total_debit)  AS so_total_debit,
                            SUM(total_credit) AS so_total_credit
                        FROM agg
                        WHERE sale_id IS NOT NULL
                        GROUP BY sale_id
                    ),

                    so_status_base AS (
                        SELECT
                            sale_id,
                            so_total_debit,
                            so_total_credit,
                            CASE
                                WHEN ABS(so_total_debit - so_total_credit) <= 1  THEN 'reconciled'
                                WHEN so_total_credit = 0 AND so_total_debit > 0  THEN 'unreconciled'
                                WHEN so_total_debit  = 0 AND so_total_credit > 0 THEN 'unreconciled'
                                ELSE 'partially'
                            END AS so_level_status
                        FROM so_totals
                    ),

                    reconciled_numbered AS (
                        SELECT
                            sale_id,
                            LPAD(ROW_NUMBER() OVER (ORDER BY sale_id)::text, 4, '0') AS matching_no
                        FROM so_status_base
                        WHERE so_level_status = 'reconciled'
                    ),

                    so_status AS (
                        SELECT
                            sb.sale_id,
                            sb.so_level_status,
                            rn.matching_no 
                        FROM so_status_base sb
                        LEFT JOIN reconciled_numbered rn ON rn.sale_id = sb.sale_id
                    ),

                    enriched AS (
                        SELECT
                            agg.sale_id,
                            so.partner_id,
                            agg.picking_id,
                            sp.date_done,
                            agg.company_id,
                            agg.total_debit,
                            agg.total_credit,
                            agg.refs,
                            COALESCE(ss.so_level_status, 'unreconciled') AS so_level_status,
                            ss.matching_no
                        FROM agg
                        LEFT JOIN sale_order so    ON so.id = agg.sale_id
                        LEFT JOIN stock_picking sp ON sp.id = agg.picking_id
                        LEFT JOIN so_status ss     ON ss.sale_id = agg.sale_id
                    )

                    INSERT INTO cogs_interim_report (
                        y_sale_id, y_customer_id, y_delivery_no, y_date_stock_move,
                        y_invoice_ref, y_debit, y_credit, y_difference,
                        y_status, y_matching, y_company_id, user_id
                    )
                    SELECT
                        e.sale_id, e.partner_id, e.picking_id, e.date_done, e.refs,
                        e.total_debit, e.total_credit,
                        (e.total_debit - e.total_credit)  AS y_difference,
                        e.so_level_status                 AS y_status,
                        COALESCE(e.matching_no, '')       AS y_matching,
                        e.company_id,
                        %(user_id)s
                    FROM enriched e
                    WHERE e.total_debit > 0.001
                       OR e.total_credit > 0.001;
                """

        params = {
            "account_ids": account_ids,
            "company_ids": company_ids,
            "user_id": user_id,
        }

        self._cr.execute(query, params)

    def button_generate_report(self):
        self._get_report_data()
        list_view = self.env.ref("cogs_interim_report.view_cogs_interim_report_list").id
        search_view = self.env.ref("cogs_interim_report.view_cogs_interim_report_search").id
        return {
            "name": _("COGS Interim Report"),
            "type": "ir.actions.act_window",
            "res_model": "cogs.interim.report",
            "view_mode": "list",
            "views": [(list_view, "list")],
            "search_view_id": [search_view, "search"],
            "target": "current",
            "context": self._context,
        }