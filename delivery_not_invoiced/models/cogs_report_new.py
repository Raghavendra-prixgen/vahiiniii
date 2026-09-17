# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class GrinNotBilledReport(models.Model):
    _name = "delivery.not.invoiced.report"
    _description = "Delivery Not Invoiced Report"
    _rec_name = 'y_sale_id'

    # Fields
    y_sale_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
    y_partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    y_invoice_reference = fields.Char(string="Entry", readonly=True)

    debit = fields.Float(string="Debit", readonly=True, digits=(16, 2))
    credit = fields.Float(string="Credit", readonly=True, digits=(16, 2))
    difference = fields.Float(string="Difference", readonly=True, digits=(16, 2))

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    y_status = fields.Selection([
        ('reconciled', 'Completely Reconciled'),
        ('partially', 'Partially Reconciled'),
        ('un_reconciled', 'Unreconciled')
    ], string="Status", readonly=True)

    def retrieve_cosgs_report(self):
        allowed_companies = (
            self._context.get('allowed_company_ids')
            or self.env.user.company_ids.ids
        )

        # 1. Clean old data for this user
        self._cr.execute(
            "DELETE FROM delivery_not_invoiced_report WHERE user_id = %s",
            (self.env.user.id,)
        )

        # 2. Get GRIR Accounts
        cogs_accounts = self.env['account.account'].search([
            ('y_gl_code_type', '=', 'asso'),
            ('company_ids', 'in', allowed_companies)
        ])
        if not cogs_accounts:
            raise ValidationError("GRIR account not configured for selected company.")

        account_ids = tuple(cogs_accounts.ids)
        company_ids = tuple(allowed_companies)
        current_user_id = self.env.user.id

        # ---------------------------------------------------------
        # SQL Logic
        # ---------------------------------------------------------
        
        query = """
            -- 1. Gather all COGS lines linked to Sales Orders
            WITH so_cogs_lines AS (
                -- A. Delivery Side (Stock Moves -> Valuation -> Journal Entries)
                SELECT 
                    sol.order_id AS sale_id,
                    aml.id AS aml_id,
                    aml.debit,
                    aml.credit,
                    am.name as move_name,
                    sol.company_id
                FROM sale_order_line sol
                JOIN stock_move sm ON sm.sale_line_id = sol.id
                JOIN stock_valuation_layer svl ON svl.stock_move_id = sm.id
                -- Handle potential secondary layers (landed costs, etc)
                LEFT JOIN stock_valuation_layer svl2 ON svl2.stock_valuation_layer_id = svl.id
                JOIN account_move am ON (am.id = svl.account_move_id OR am.id = svl2.account_move_id)
                JOIN account_move_line aml ON aml.move_id = am.id
                WHERE aml.account_id IN %(account_ids)s
                  AND am.state = 'posted'
                  AND sol.company_id IN %(company_ids)s
                  
                UNION ALL
                
                -- B. Invoice Side (Invoice Lines -> COGS Origin -> Journal Entries)
                -- FIX: Use sale_order_line_invoice_rel table instead of sale_line_ids column
                SELECT 
                    sol.order_id AS sale_id,
                    cogs_aml.id AS aml_id,
                    cogs_aml.debit,
                    cogs_aml.credit,
                    cogs_move.name as move_name,
                    sol.company_id
                FROM sale_order_line sol
                -- JOIN the Many2many relation table
                JOIN sale_order_line_invoice_rel rel ON rel.order_line_id = sol.id
                JOIN account_move_line revenue_aml ON revenue_aml.id = rel.invoice_line_id
                -- Join Revenue Lines to COGS Lines via the Anglosaxon origin
                JOIN account_move_line cogs_aml ON cogs_aml.cogs_origin_id = revenue_aml.id
                JOIN account_move cogs_move ON cogs_move.id = cogs_aml.move_id
                WHERE cogs_aml.account_id IN %(account_ids)s
                  AND cogs_move.state = 'posted'
                  AND sol.company_id IN %(company_ids)s
            ),
            
            -- 2. Aggregate Data per Sale Order
            aggregated_so AS (
                SELECT 
                    sale_id,
                    company_id,
                    SUM(debit) as total_debit,
                    SUM(credit) as total_credit,
                    string_agg(DISTINCT move_name, ', ') as refs
                FROM so_cogs_lines
                GROUP BY sale_id, company_id
            )

            -- 3. Insert Sales Order Data
            INSERT INTO delivery_not_invoiced_report (
                y_sale_id, y_partner_id, y_invoice_reference,
                debit, credit, difference, y_status,
                user_id, company_id
            )
            SELECT
                agg.sale_id,
                so.partner_id,
                agg.refs,
                agg.total_debit,
                agg.total_credit,
                (agg.total_debit - agg.total_credit) as diff,
                CASE 
                    WHEN abs(agg.total_debit - agg.total_credit) < 0.01 THEN 'reconciled'
                    WHEN (agg.total_debit - agg.total_credit) != 0 THEN 'partially'
                    ELSE 'un_reconciled'
                END as status,
                %(user_id)s,
                agg.company_id
            FROM aggregated_so agg
            JOIN sale_order so ON so.id = agg.sale_id
            WHERE abs(agg.total_debit) > 0.01 OR abs(agg.total_credit) > 0.01;
        """

        params = {
            'account_ids': account_ids,
            'company_ids': company_ids,
            'user_id': current_user_id
        }
        
        self._cr.execute(query, params)

        # ---------------------------------------------------------
        # 4. Handle "Non-PO" (Orphan) Lines
        # ---------------------------------------------------------
        
        orphan_query = """
            INSERT INTO delivery_not_invoiced_report (
                y_sale_id, y_partner_id, y_invoice_reference,
                debit, credit, difference, y_status,
                user_id, company_id
            )
            SELECT 
                NULL as y_sale_id,
                aml.partner_id,
                am.name as y_invoice_reference,
                aml.debit,
                aml.credit,
                (aml.debit - aml.credit) as difference,
                'un_reconciled' as y_status,
                %(user_id)s,
                aml.company_id
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            WHERE aml.account_id IN %(account_ids)s
              AND am.state = 'posted'
              AND aml.company_id IN %(company_ids)s
              -- Exclude lines linked to Stock Moves
              AND NOT EXISTS (
                  SELECT 1 FROM stock_valuation_layer svl 
                  JOIN stock_move sm ON svl.stock_move_id = sm.id
                  WHERE (svl.account_move_id = am.id) AND sm.sale_line_id IS NOT NULL
              )
              -- Exclude lines linked to Invoices (via M2M table)
              AND NOT EXISTS (
                  SELECT 1 
                  FROM account_move_line rev_aml
                  JOIN sale_order_line_invoice_rel rel ON rel.invoice_line_id = rev_aml.id
                  WHERE aml.cogs_origin_id = rev_aml.id
              )
        """
        
        self._cr.execute(orphan_query, params)

    def button_view_report(self):
        self.retrieve_cosgs_report()
        view_id = self.env.ref("delivery_not_invoiced.view_delivery_not_invoiced_report_list").id
        return {
            'name': "COGS Interim Register",
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.not.invoiced.report',
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'target': 'current',
        }