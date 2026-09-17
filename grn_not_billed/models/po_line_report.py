# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class GrinNotBilledReport(models.Model):
    _name = "grin.not.billed.report"
    _description = "GRN Not Billed Report"
    _rec_name = 'y_purchase_id'

    # Fields
    y_purchase_id = fields.Many2one('purchase.order', string="Purchase Order", readonly=True)
    y_partner_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    y_bill_reference = fields.Char(string="Entry", readonly=True)

    total_received_value = fields.Float(
        string="Total Received Value",
        readonly=True,
        digits=(16, 2)
    )
    total_billed_value = fields.Float(
        string="Total Billed Value",
        readonly=True,
        digits=(16, 2)
    )
    not_billed_value = fields.Float(
        string="Not Billed Value",
        readonly=True,
        digits=(16, 2)
    )

    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

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
    def retrieve_grir_report(self):
        allowed_companies = (
            self._context.get('allowed_company_ids')
            or self.env.user.company_ids.ids
        )
        
        # Clean old data
        self._cr.execute(
            "DELETE FROM grin_not_billed_report WHERE user_id = %s",
            (self.env.user.id,)
        )

        # GRIR accounts
        grir_accounts = self.env['account.account'].search([
            ('y_gl_code_type', '=', 'assi'),
            ('company_ids', 'in', allowed_companies)
        ])
        if not grir_accounts:
            raise ValidationError("GRIR account not configured for selected company.")

        grir_account_ids = grir_accounts.ids

        # Get PO lines
        po_lines = self.env['purchase.order.line'].search([
            ('company_id', 'in', allowed_companies),
            ('state', 'in', ('purchase', 'done')),
            '|', ('move_ids', '!=', False), ('invoice_lines', '!=', False),
        ])

        # Map to store aggregated PO data. Key = Purchase Order ID
        po_result_map = {}
        account_move_lines_ids = []

        for po_line in po_lines:
            # Stock moves
            stock_moves = po_line.move_ids

            # Collect Account Move Lines
            account_move_lines = self.env['account.move.line']

            subcon_moves = stock_moves.filtered(lambda m: m.is_subcontract)
            if subcon_moves:
                account_move_lines |= subcon_moves.move_orig_ids.stock_valuation_layer_ids.account_move_id.line_ids
            else:
                account_move_lines |= stock_moves.stock_valuation_layer_ids.account_move_id.line_ids
                if stock_moves.stock_valuation_layer_ids.stock_valuation_layer_ids:
                    account_move_lines |= stock_moves.stock_valuation_layer_ids.stock_valuation_layer_ids.account_move_id.line_ids

            line_debit = 0
            line_credit = 0
            
            # Filter GRIR entries (Received)
            received_lines = account_move_lines.filtered(lambda l: l.account_id.id in grir_account_ids and l.move_id.state == 'posted')
            for ll in received_lines:
                if ll.debit > 0:
                    line_debit += abs(ll.debit)
                else:
                    line_credit += abs(ll.credit)

            account_move_lines_ids += received_lines.ids
            
            # Billed Value
            bill_lines = po_line.invoice_lines.filtered(lambda l: l.account_id.id in grir_account_ids and l.move_id.state == 'posted')
            for ll in bill_lines:
                if ll.debit > 0:
                    line_debit += abs(ll.debit)
                else:
                    line_credit += abs(ll.credit)

            account_move_lines_ids += bill_lines.ids
            
            # Get Bill Names for this line
            current_bill_names = [m.name for m in bill_lines.mapped('move_id') if m.name]

            # --- AGGREGATION LOGIC ---
            po_id = po_line.order_id.id
            
            if po_id not in po_result_map:
                # Initialize Entry
                po_result_map[po_id] = {
                    'purchase_id': po_id,
                    'partner_id': po_line.order_id.partner_id.id,
                    'received_value': 0.0,
                    'billed_value': 0.0,
                    'company_id': po_line.order_id.company_id.id,
                    'bill_refs': set(), # Use a set to handle unique bill numbers
                }
            
            # Aggregate Values
            po_result_map[po_id]['received_value'] += line_debit
            po_result_map[po_id]['billed_value'] += line_credit
            po_result_map[po_id]['bill_refs'].update(current_bill_names)

        # --- Process Non-PO Lines (Manual Journal Entries directly to GRIR) ---
        non_po_results = []
        
        filtered_line_ids = []
        # Find lines in GRIR accounts that were NOT processed in the PO loop above
        # Note: Using search count optimization or SQL might be faster for large DBs, keeping existing logic structure
        all_grir_lines = self.env['account.move.line'].search([
            ('account_id', 'in', grir_account_ids),
            ('parent_state', '=', 'posted'),
            ('company_id', 'in', allowed_companies)
        ])
        
        # Determine which lines are standalone
        for line in all_grir_lines:
            if line.id not in account_move_lines_ids:
                filtered_line_ids.append(line)
    
        for non_purchase in filtered_line_ids:
            debit = 0
            credit = 0
            if non_purchase.debit > 0:
                debit += abs(non_purchase.debit)
            else:
                credit += abs(non_purchase.credit)
            
            non_po_results.append({
                'purchase_id': None,
                'partner_id': non_purchase.partner_id.id if non_purchase.partner_id else None,
                'received_value': debit,
                'billed_value': credit,
                'company_id': non_purchase.company_id.id,
                'y_bill_reference': non_purchase.move_id.name,
            })
        
        # --- INSERTION ---
        
        # 1. Insert Purchase Order Aggregated Data
        for po_id, data in po_result_map.items():
            # Convert set of bill refs to comma-separated string
            bill_ref_str = ", ".join(sorted(list(data['bill_refs'])))
            
            # Only insert if there is value (optional, but keeps report clean)
            # if data['received_value'] == 0 and data['billed_value'] == 0: continue

            report_data = {
                'y_purchase_id': data['purchase_id'],
                'y_partner_id': data['partner_id'],
                'y_bill_reference': bill_ref_str,
                'total_received_value': data['received_value'],
                'total_billed_value': data['billed_value'],
                'not_billed_value': data['received_value'] - data['billed_value'],
                'user_id': self.env.user.id,
                'company_id': data['company_id'],
            }
            self._cr.execute(self.dict_to_insert_query('grin_not_billed_report', report_data))

        # 2. Insert Non-PO Data
        for data in non_po_results:
            report_data = {
                'y_purchase_id': data['purchase_id'],
                'y_partner_id': data['partner_id'],
                'y_bill_reference': data['y_bill_reference'],
                'total_received_value': data['received_value'],
                'total_billed_value': data['billed_value'],
                'not_billed_value': data['received_value'] - data['billed_value'],
                'user_id': self.env.user.id,
                'company_id': data['company_id'],
            }
            self._cr.execute(self.dict_to_insert_query('grin_not_billed_report', report_data))

    def button_view_report(self):
        self.retrieve_grir_report()
        view_id = self.env.ref("grn_not_billed.view_grin_not_billed_report_list").id
        return {
            'name': "GRN Not Billed Report",
            'type': 'ir.actions.act_window',
            'res_model': 'grin.not.billed.report',
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'target': 'current',
        }