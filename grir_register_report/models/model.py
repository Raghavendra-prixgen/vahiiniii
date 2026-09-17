# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools

class GrirRegisterReport(models.Model):
    _name = "grir.register.report"
    _description = "GRIR Register Report"
    _auto = False
    _rec_name = 'y_purchase_id'

    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order",readonly=True)
    y_partner_id = fields.Many2one('res.partner',string="Vendor",readonly=True)
    y_picking_id = fields.Many2one('stock.picking',string="GR Number",readonly=True)
    y_date_done = fields.Date(string="Date Of Stock Move")
    y_bill_journal_entry_reference = fields.Char(string="Bill/Journal Entry Reference",readonly=True)
    y_credit = fields.Float(string="Credit",readonly=True)
    y_debit = fields.Float(string="Debit",readonly=True)
    y_diffrence_value = fields.Float(string="Difference",readonly=True)
    y_status = fields.Selection([('reconciled','Completely Reconciled'),('partially','Partially Reconciled'),('un_reconciled','Unreconciled')],string="Status",readonly=True)
    

    # y_product_id = fields.Many2one('product.product',string="Product",readonly=True)
    # y_product_category_id = fields.Many2one('product.category',string="Product Category",readonly=True)
    # y_product_uom_id = fields.Many2one('uom.uom',string="UoM",readonly=True)
    # y_company_id = fields.Many2one('res.company',string="Company",readonly=True)
    
    def init(self):        
        tools.drop_view_if_exists(self._cr, 'grir_register_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW grir_register_report AS (
                 SELECT row_number() OVER () AS id,
                                       result.*
                                FROM (
                                WITH
                                    StockMoveData AS (
                                        SELECT
                                            po.id AS y_purchase_id,
                                            po.partner_id AS y_partner_id,
                                            sm.id AS y_stock_move_id,
                                            sm.picking_id AS y_picking_id,
                                            sm.date AS stock_move_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN account_move am ON aml.move_id = am.id 
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id 
                                        LEFT JOIN stock_move sm ON sm.id = am.stock_move_id
                                        LEFT JOIN purchase_order_line po_line ON po_line.id = sm.purchase_line_id
                                        LEFT JOIN purchase_order po ON po.id = po_line.order_id
                                        WHERE
                                            am.state = 'posted'
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.move_type = 'entry'
                                            AND am.stock_move_id IS NOT NULL
                                            -- {company_clause}
                                        GROUP BY sm.id, sm.picking_id, sm.date,po.id,po.partner_id
                                    ),


                                    -- CTE: Invoice-related stock move financials
                                    InvoiceData AS (
                                        SELECT
                                            aml.y_stock_move_id,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN aml.balance > 0 THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN aml.balance < 0 THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_move am ON am.id = aml.move_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        WHERE
                                            aml.y_stock_move_id IS NOT NULL
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.state = 'posted'
                                            AND am.move_type IN ('in_invoice', 'in_refund')
                                            -- {company_clause}
                                        GROUP BY aml.y_stock_move_id
                                    ),

                                    UnmatchedInvoiceData AS (
                                        SELECT
                                            po.partner_id,
                                            aml.date AS journal_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN aml.balance > 0 THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN aml.balance < 0 THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_move am ON am.id = aml.move_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        LEFT JOIN stock_move sm ON sm.id = aml.y_stock_move_id
                                        LEFT JOIN purchase_order_line po_line ON po_line.id = sm.purchase_line_id
                                        LEFT JOIN purchase_order po ON po.id = po_line.order_id
                                        WHERE
                                            aml.y_stock_move_id IS NOT NULL
                                            AND aml.y_stock_move_id NOT IN (
                                                SELECT y_stock_move_id FROM StockMoveData
                                            )
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.state = 'posted'
                                            AND am.move_type IN ('in_invoice', 'in_refund')
                                            -- {company_clause}
                                        GROUP BY po.partner_id, aml.date
                                    ),

                                    -- CTE: Manual Journal Entries (not linked to stock moves)
                                    RegularJournalEntryData AS (
                                        SELECT
                                            aml.partner_id,
                                            aml.date AS journal_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move am
                                        LEFT JOIN res_company company ON company.id = am.company_id
                                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        WHERE
                                            am.state = 'posted'
                                            AND am.move_type IN ('entry', 'in_invoice', 'in_refund')
                                            AND aml.y_stock_move_id IS NULL
                                            AND am.stock_move_id IS NULL
                                            AND acc.y_gl_code_type = 'assi'
                                            -- {company_clause}
                                        GROUP BY aml.partner_id, aml.date
                                    )

                                    -- Final Data Selection and Union
                                    SELECT
                                        sm.y_purchase_id,
                                        sm.y_partner_id,
                                        sm.y_picking_id,
                                        COALESCE(inv.bill_journal_entry_reference, sm.bill_journal_entry_reference) AS y_bill_journal_entry_reference,
                                        COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0) AS y_debit,
                                        COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0) AS y_credit,
                                        (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) - (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) AS y_diffrence_value,
                                        sm.stock_move_date AS y_date_done,
                                        CASE 
                                            WHEN (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) - (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) = 0 THEN 'reconciled'
                                            WHEN (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) != 0 AND (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) != 0 THEN 'partially'
                                            ELSE 'un_reconciled'
                                        END AS y_status
                                    FROM StockMoveData sm
                                    LEFT JOIN InvoiceData inv ON inv.y_stock_move_id = sm.y_stock_move_id

                                    UNION ALL

                                    SELECT
                                        NULL AS y_purchase_id,
                                        rje.partner_id AS y_partner_id,
                                        NULL AS y_picking_id,
                                        rje.bill_journal_entry_reference,
                                        rje.debit,
                                        rje.credit,
                                        rje.debit - rje.credit AS y_difference_value,
                                        rje.journal_date AS y_date_done,
                                        'un_reconciled' AS y_status
                                    FROM RegularJournalEntryData rje

                                    UNION ALL

                                    SELECT
                                        NULL AS y_purchase_id,
                                        uid.partner_id AS y_partner_id,
                                        NULL AS y_picking_id,
                                        uid.bill_journal_entry_reference,
                                        uid.debit,
                                        uid.credit,
                                        uid.debit - uid.credit AS y_difference_value,
                                        uid.journal_date AS y_date_done,
                                        'un_reconciled' AS y_status
                                    FROM UnmatchedInvoiceData uid
                                ) result
                                -- Optional final sort
                                ORDER BY y_date_done DESC, y_purchase_id NULLS LAST

                )""")

    def grir_register_report_query(self):
        grir_account_id = self.env['account.account'].search([('y_gl_code_type','=','assi')],limit=1)
        if not grir_account_id:
            raise ValidationError("GRIR code not configured in chart of accounts.")
        if self._context.get('allowed_company_ids'):
            if len(self._context.get('allowed_company_ids')) == 1:
                company_clause = "AND company.id = {}".format(self._context.get('allowed_company_ids')[0])
            else:
                company_clause = "AND company.id in {}".format(tuple(self._context.get('allowed_company_ids')))
        else:
            company_ids = self.env.user.company_ids.ids
            if len(company_ids) == 1:
                company_clause = "AND company.id = {}".format(company_ids[:1])
            else:
                company_clause = "AND company.id in {}".format(tuple(company_ids))
            
        tools.drop_view_if_exists(self._cr, 'grir_register_report')
        query = """
            CREATE OR REPLACE VIEW grir_register_report AS (
                                SELECT row_number() OVER () AS id,
                                       result.*
                                FROM (
                                WITH
                                    StockMoveData AS (
                                        SELECT
                                            po.id AS y_purchase_id,
                                            po.partner_id AS y_partner_id,
                                            sm.id AS y_stock_move_id,
                                            sm.picking_id AS y_picking_id,
                                            sm.date AS stock_move_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN account_move am ON aml.move_id = am.id 
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id 
                                        LEFT JOIN stock_move sm ON sm.id = am.stock_move_id
                                        LEFT JOIN purchase_order_line po_line ON po_line.id = sm.purchase_line_id
                                        LEFT JOIN purchase_order po ON po.id = po_line.order_id
                                        WHERE
                                            am.state = 'posted'
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.move_type = 'entry'
                                            AND am.stock_move_id IS NOT NULL
                                            {company_clause}
                                        GROUP BY sm.id, sm.picking_id, sm.date,po.id,po.partner_id
                                    ),


                                    -- CTE: Invoice-related stock move financials
                                    InvoiceData AS (
                                        SELECT
                                            aml.y_stock_move_id,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN aml.balance > 0 THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN aml.balance < 0 THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_move am ON am.id = aml.move_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        WHERE
                                            aml.y_stock_move_id IS NOT NULL
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.state = 'posted'
                                            AND am.move_type IN ('in_invoice', 'in_refund')
                                            {company_clause}
                                        GROUP BY aml.y_stock_move_id
                                    ),

                                    UnmatchedInvoiceData AS (
                                        SELECT
                                            po.id AS y_purchase_id,
                                            po.partner_id,
                                            aml.date AS journal_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN aml.balance > 0 THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN aml.balance < 0 THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move_line aml
                                        LEFT JOIN res_company company ON company.id = aml.company_id
                                        LEFT JOIN account_move am ON am.id = aml.move_id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        LEFT JOIN stock_move sm ON sm.id = aml.y_stock_move_id
                                        LEFT JOIN purchase_order_line po_line ON po_line.id = sm.purchase_line_id
                                        LEFT JOIN purchase_order po ON po.id = po_line.order_id
                                        WHERE
                                            aml.y_stock_move_id IS NOT NULL
                                            AND aml.y_stock_move_id NOT IN (
                                                SELECT y_stock_move_id FROM StockMoveData
                                            )
                                            AND acc.y_gl_code_type = 'assi'
                                            AND am.state = 'posted'
                                            AND am.move_type IN ('in_invoice', 'in_refund')
                                            {company_clause}
                                        GROUP BY po.partner_id, aml.date,po.id
                                    ),

                                    -- CTE: Manual Journal Entries (not linked to stock moves)
                                    RegularJournalEntryData AS (
                                        SELECT
                                            aml.partner_id,
                                            aml.date AS journal_date,
                                            STRING_AGG(DISTINCT am.name::text, ', ') AS bill_journal_entry_reference,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.debit ELSE 0 END), 0) AS debit,
                                            COALESCE(SUM(CASE WHEN acc.y_gl_code_type = 'assi' THEN aml.credit ELSE 0 END), 0) AS credit
                                        FROM account_move am
                                        LEFT JOIN res_company company ON company.id = am.company_id
                                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                        LEFT JOIN account_account acc ON acc.id = aml.account_id
                                        WHERE
                                            am.state = 'posted'
                                            AND am.move_type IN ('entry', 'in_invoice', 'in_refund')
                                            AND aml.y_stock_move_id IS NULL
                                            AND am.stock_move_id IS NULL
                                            AND acc.y_gl_code_type = 'assi'
                                            {company_clause}
                                        GROUP BY aml.partner_id, aml.date
                                    )

                                    -- Final Data Selection and Union
                                    SELECT
                                        sm.y_purchase_id,
                                        sm.y_partner_id,
                                        sm.y_picking_id,
                                        COALESCE(inv.bill_journal_entry_reference, sm.bill_journal_entry_reference) AS y_bill_journal_entry_reference,
                                        COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0) AS y_debit,
                                        COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0) AS y_credit,
                                        (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) - (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) AS y_diffrence_value,
                                        sm.stock_move_date AS y_date_done,
                                        CASE 
                                            WHEN (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) - (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) = 0 THEN 'reconciled'
                                            WHEN (COALESCE(sm.debit, 0) + COALESCE(inv.debit, 0)) != 0 AND (COALESCE(sm.credit, 0) + COALESCE(inv.credit, 0)) != 0 THEN 'partially'
                                            ELSE 'un_reconciled'
                                        END AS y_status
                                    FROM StockMoveData sm
                                    LEFT JOIN InvoiceData inv ON inv.y_stock_move_id = sm.y_stock_move_id

                                    UNION ALL

                                    SELECT
                                        NULL AS y_purchase_id,
                                        rje.partner_id AS y_partner_id,
                                        NULL AS y_picking_id,
                                        rje.bill_journal_entry_reference,
                                        rje.debit,
                                        rje.credit,
                                        rje.debit - rje.credit AS y_difference_value,
                                        rje.journal_date AS y_date_done,
                                        'un_reconciled' AS y_status
                                    FROM RegularJournalEntryData rje

                                    UNION ALL

                                    SELECT
                                        uid.y_purchase_id AS y_purchase_id,
                                        uid.partner_id AS y_partner_id,
                                        NULL AS y_picking_id,
                                        uid.bill_journal_entry_reference,
                                        uid.debit,
                                        uid.credit,
                                        uid.debit - uid.credit AS y_difference_value,
                                        uid.journal_date AS y_date_done,
                                        'un_reconciled' AS y_status
                                    FROM UnmatchedInvoiceData uid
                                ) result
                                -- Optional final sort
                                ORDER BY y_date_done DESC, y_purchase_id NULLS LAST

                )""".format(company_clause=company_clause)

        # print('\n'*2)
        # print(query)
        # print('\n'*2)
        self._cr.execute(query)
        return {
            'name': _("GRIR Register"),
            'type': 'ir.actions.act_window',
            'res_model': 'grir.register.report',
            'view_mode': 'list,pivot',
            'view_type': 'list',
            'views': [[False, 'list'],[False, 'pivot'],],
            'target': 'current'
            }