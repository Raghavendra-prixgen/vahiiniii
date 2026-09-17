# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class GrinNotBilledReport(models.Model):
    _name = "delivery.not.invoiced.report"
    _description = "Delivery Not Invoiced Report"
    _rec_name = 'y_sale_id'

    # Fields
    y_sale_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
    y_partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    y_invoice_reference = fields.Char(string="Entry", readonly=True)

    debit = fields.Float(
        string="Debit",
        readonly=True,
        digits=(16, 2)
    )
    credit = fields.Float(
        string="Credit",
        readonly=True,
        digits=(16, 2)
    )
    difference = fields.Float(
        string="Difference",
        readonly=True,
        digits=(16, 2)
    )

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    y_status = fields.Selection([('reconciled','Completely Reconciled'),('partially','Partially Reconciled'),('un_reconciled','Unreconciled')],string="Status",readonly=True)

    # Utility: SQL Insert Builder
    def dict_to_insert_query(self, table_name, data):

        def fmt(value):
            """Secure SQL formatting"""
            if isinstance(value, str):
                return "'%s'" % value.replace("'", "''")
            if isinstance(value, (int, float)):
                return str(value)
            if value is None:
                return "NULL"
            if isinstance(value, bool):
                return 'TRUE' if value else 'FALSE'
            if isinstance(value, datetime):
                return "'%s'" % value.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(value, date):
                return "'%s'" % value.strftime('%Y-%m-%d')
            raise ValueError(f"Unsupported SQL value type: {type(value)} → {value}")

        columns = ','.join(f'"{k}"' for k in data.keys())
        values = ','.join(fmt(v) for v in data.values())

        return f'INSERT INTO "{table_name}" ({columns}) VALUES ({values})'

    # Main Logic
    def retrieve_cosgs_report(self):
        allowed_companies = (
            self._context.get('allowed_company_ids')
            or self.env.user.company_ids.ids
        )
        
        # Clean old data
        self._cr.execute(
            "DELETE FROM delivery_not_invoiced_report WHERE user_id = %s",
            (self.env.user.id,)
        )

        # GRIR accounts
        cogs_accounts = self.env['account.account'].search([
            ('y_gl_code_type', '=', 'asso'),
            ('company_ids', 'in', allowed_companies)
        ])
        if not cogs_accounts:
            raise ValidationError("GRIR account not configured for selected company.")

        cogs_account_ids = cogs_accounts.ids

        # 1. Get ALL SO Line IDs first (Do not browse objects yet)
        so_lines_domain = [
            ('company_id', 'in', allowed_companies),
            ('state', '=', 'sale'),
            '|', ('move_ids', '!=', False), ('invoice_lines', '!=', False),
        ]
        # Search for IDs only to save memory
        so_line_ids = self.env['sale.order.line'].search(so_lines_domain).ids

        so_result_map = {}
        # Use a SET for performance (O(1) lookup vs O(N) in lists)
        processed_aml_ids = set()

        # 2. Process in Batches
        BATCH_SIZE = 1000
        total_len = len(so_line_ids)
        
        for i in range(0, total_len, BATCH_SIZE):
            batch_ids = so_line_ids[i:i + BATCH_SIZE]
            # Browse only the current batch
            so_lines = self.env['sale.order.line'].browse(batch_ids)

            for so_line in so_lines:
                stock_moves = so_line.move_ids
                account_move_lines = self.env['account.move.line']

                # Collect Stock/Valuation Lines
                # Note: This chain causes the heavy memory usage
                account_move_lines |= stock_moves.stock_valuation_layer_ids.account_move_id.line_ids
                if stock_moves.stock_valuation_layer_ids.stock_valuation_layer_ids:
                    account_move_lines |= stock_moves.stock_valuation_layer_ids.stock_valuation_layer_ids.account_move_id.line_ids

                line_debit = 0.0
                line_credit = 0.0

                # Filter GRIR entries (Received)
                delivered_lines = account_move_lines.filtered(
                    lambda l: l.account_id.id in cogs_account_ids and l.move_id.state == 'posted'
                )
                
                # Manual calculation to avoid sum() overhead on recordsets
                for ll in delivered_lines:
                    if ll.debit > 0:
                        line_debit += ll.debit
                    else:
                        line_credit += ll.credit
                    processed_aml_ids.add(ll.id)

                # Billed Value
                cogs_line_ids = so_line.invoice_lines.move_id.line_ids.filtered(lambda x:x.cogs_origin_id.id in so_line.invoice_lines.ids and x.account_id.id in cogs_account_ids and x.move_id.state == 'posted')
                invoice_lines = cogs_line_ids
                
                for ll in invoice_lines:
                    if ll.debit > 0:
                        line_debit += ll.debit
                    else:
                        line_credit += ll.credit
                    processed_aml_ids.add(ll.id)

                # Get Bill Names
                current_invoice_names = [m.name for m in invoice_lines.move_id if m.name]

                # --- AGGREGATION ---
                so_id = so_line.order_id.id
                if so_id not in so_result_map:
                    so_result_map[so_id] = {
                        'sale_id': so_id,
                        'partner_id': so_line.order_id.partner_id.id,
                        'delivered_value': 0.0,
                        'invoiced_value': 0.0,
                        'company_id': so_line.order_id.company_id.id,
                        'invoice_refs': set(),
                    }
                
                so_result_map[so_id]['delivered_value'] += line_debit
                so_result_map[so_id]['invoiced_value'] += line_credit
                so_result_map[so_id]['invoice_refs'].update(current_invoice_names)

            # CRITICAL: Free up memory after every batch
            self.env.invalidate_all()

        # --- Process Non-PO Lines ---
        # Get all relevant COGS lines IDs from DB
        all_cogs_aml_ids = self.env['account.move.line'].search([
            ('account_id', 'in', cogs_account_ids),
            ('parent_state', '=', 'posted'),
            ('company_id', 'in', allowed_companies)
        ]).ids

        # Set difference: Find IDs in DB that we haven't processed yet
        non_po_aml_ids = set(all_cogs_aml_ids) - processed_aml_ids
        
        # Convert back to list for batching
        non_po_aml_ids = list(non_po_aml_ids)
        non_po_results = []

        # Process Non-PO in batches as well
        for i in range(0, len(non_po_aml_ids), BATCH_SIZE):
            batch_ids = non_po_aml_ids[i:i + BATCH_SIZE]
            non_sales_lines = self.env['account.move.line'].browse(batch_ids)

            for non_sale in non_sales_lines:
                debit = non_sale.debit
                credit = non_sale.credit
                
                non_po_results.append({
                    'sale_id': None,
                    'partner_id': non_sale.partner_id.id if non_sale.partner_id else None,
                    'delivered_value': debit,
                    'invoiced_value': credit,
                    'company_id': non_sale.company_id.id,
                    'y_invoice_reference': non_sale.move_id.name,
                })
            
            self.env.invalidate_all()
        
        # --- INSERTION (Keep existing logic mostly) ---
        
        # 1. Insert PO Data
        for so_id, data in so_result_map.items():
            if abs(data['delivered_value']) < 0.01 and abs(data['invoiced_value']) < 0.01: 
                continue

            bill_ref_str = ", ".join(sorted(list(data['invoice_refs'])))
            difference = data['delivered_value'] - data['invoiced_value']
            
            status = 'un_reconciled'
            if abs(difference) < 0.01:
                status = 'reconciled'
            elif difference != 0:
                status = 'partially'

            report_data = {
                'y_sale_id': data['sale_id'],
                'y_partner_id': data['partner_id'],
                'y_invoice_reference': bill_ref_str,
                'debit': data['delivered_value'],
                'credit': data['invoiced_value'],
                'difference': difference,
                'user_id': self.env.user.id,
                'company_id': data['company_id'],
                'y_status': status,
            }
            self._cr.execute(self.dict_to_insert_query('delivery_not_invoiced_report', report_data))

        # 2. Insert Non-PO Data
        for data in non_po_results:
            report_data = {
                'y_sale_id': data['sale_id'],
                'y_partner_id': data['partner_id'],
                'y_invoice_reference': data['y_invoice_reference'],
                'debit': data['delivered_value'],
                'credit': data['invoiced_value'],
                'difference': data['delivered_value'] - data['invoiced_value'],
                'user_id': self.env.user.id,
                'company_id': data['company_id'],
                'y_status': 'un_reconciled',
            }
            self._cr.execute(self.dict_to_insert_query('delivery_not_invoiced_report', report_data))

    def button_view_report(self):
        self.retrieve_cosgs_report()
        view_id = self.env.ref("delivery_not_invoiced.view_delivery_not_invoiced_report_list").id
        return {
            'name': "COGS Interim Register(New)",
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.not.invoiced.report',
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'target': 'current',
        }