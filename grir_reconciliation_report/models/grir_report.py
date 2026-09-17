# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class GrinNotBilledReport(models.Model):
    _name = "grir.reconciliation.report"
    _description = "GRIR Reconciliation Report"
    _order = "y_date_done desc, y_purchase_id"

    # Fields
    y_purchase_id = fields.Many2one('purchase.order', string="Purchase Order", readonly=True)
    y_partner_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    y_picking_id = fields.Many2one('stock.picking', string="GR Number", readonly=True)
    y_date_done = fields.Date(string="Date Of Stock Move")
    y_bill_journal_entry_reference = fields.Char(string="Bill/Journal Entry Reference", readonly=True)
    y_credit = fields.Float(string="Credit", readonly=True)
    y_debit = fields.Float(string="Debit", readonly=True)
    y_diffrence_value = fields.Float(string="Difference", readonly=True)
    y_status = fields.Selection(
        [('reconciled', 'Completely Reconciled'),
         ('partially', 'Partially Reconciled'),
         ('un_reconciled', 'Unreconciled')],
        string="Status", readonly=True)

    y_user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    y_company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    # The real journal items behind this report row — needed so the
    # Manual Reconcile / Revoke actions know exactly which account.move.line
    # records to tag or untag.
    y_move_line_ids = fields.Many2many(
        'account.move.line',
        'grir_reconciliation_report_aml_rel',
        'report_id', 'move_line_id',
        string="Journal Items", readonly=True,
    )

    # Shows the custom match number for rows grouped purely via manual
    # reconcile (no PO involved at all). Empty for PO rows even if a
    # manual entry was folded into them (see y_has_manual_match below).
    y_manual_reco_ref = fields.Char(string="Manual Reconcile Ref", readonly=True)

    # True if this row includes at least one manually-tagged journal item
    # (either folded into a PO row via y_manual_po_id, or grouped via
    # y_manual_grir_reco_ref). Lets you spot at a glance which rows rely on
    # a manual match rather than a fully natural PO/system trace.
    y_has_manual_match = fields.Boolean(string="Includes Manual Entry", readonly=True)

    # ------------------------------------------------------------------
    # Main Logic
    # ------------------------------------------------------------------
    def retrieve_grir_report(self):
        allowed_companies = (
            self._context.get('allowed_company_ids')
            or self.env.user.company_ids.ids
        )

        # Clean old data for the current user
        self._cr.execute(
            "DELETE FROM grir_reconciliation_report WHERE y_user_id = %s",
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

        account_move_lines_domain = [
            ('account_id', 'in', grir_account_ids),
            ('parent_state', '=', 'posted'),  # Only posted entries
            ('company_id', 'in', allowed_companies),
            ('balance', '!=', 0),
        ]
        grir_move_lines = self.env['account.move.line'].with_context(prefetch_fields=False).search(
            account_move_lines_domain)

        # Map to store aggregated PO data. Key = Purchase Order ID
        po_result_map = {}
        # Map to store aggregated MANUAL-MATCH data. Key = y_manual_grir_reco_ref
        manual_result_map = {}
        # Lines with neither a clean PO trace nor a manual match ref
        non_po_singles = {}

        multi_po_aml_ids = []

        for aml in grir_move_lines:
            po_line = aml.purchase_line_id
            stock_move_id = aml.y_stock_move_id
            picking_id = stock_move_id.picking_id
            move_id = aml.move_id
            move_type = move_id.move_type
            if not po_line:
                if move_type == 'entry':
                    stock_move_id = move_id.stock_move_id
                    po_line = stock_move_id.purchase_line_id
                    picking_id = stock_move_id.picking_id
                    stock_valuation_layer_ids = move_id.stock_valuation_layer_ids
                    if stock_valuation_layer_ids and not po_line:
                        stock_move_id = move_id.stock_move_id
                        po_line = stock_move_id.purchase_line_id
                        picking_id = stock_move_id.picking_id
                        if not po_line:
                            stock_move_id = stock_valuation_layer_ids.stock_move_id or stock_valuation_layer_ids.stock_valuation_layer_id.stock_move_id
                            po_line = stock_move_id.purchase_line_id or stock_move_id.purchase_line_id
                            picking_id = stock_move_id.picking_id
                            if not po_line:
                                stock_move_id = stock_valuation_layer_ids.stock_move_id.move_dest_ids or stock_valuation_layer_ids.stock_move_id.move_orig_ids
                                po_line = stock_move_id.purchase_line_id
                                picking_id = stock_move_id.picking_id
                                if not po_line:
                                    stock_move_id = stock_valuation_layer_ids.stock_valuation_layer_id.stock_move_id.move_dest_ids or stock_valuation_layer_ids.stock_valuation_layer_id.stock_move_id.move_orig_ids
                                    po_line = stock_move_id.purchase_line_id
                                    picking_id = stock_move_id.picking_id

                    if not po_line and not stock_valuation_layer_ids:
                        credit_move_id = aml.matched_credit_ids.credit_move_id
                        debit_move_id = aml.matched_debit_ids.debit_move_id
                        stock_move_id = credit_move_id.move_id.stock_move_id or debit_move_id.move_id.stock_move_id
                        if stock_move_id:
                            po_line = stock_move_id.purchase_line_id
                            picking_id = stock_move_id.picking_id
                        else:
                            if credit_move_id:
                                po_line = credit_move_id.purchase_line_id
                                stock_move_id = credit_move_id.y_stock_move_id
                                picking_id = stock_move_id.picking_id
                            if debit_move_id:
                                po_line = debit_move_id.purchase_line_id
                                stock_move_id = debit_move_id.y_stock_move_id
                                picking_id = stock_move_id.picking_id

                elif move_type in ('in_refund', 'in_invoice'):
                    credit_move_id = aml.matched_credit_ids.credit_move_id
                    debit_move_id = aml.matched_debit_ids.debit_move_id
                    stock_move_id = credit_move_id.move_id.stock_move_id or debit_move_id.move_id.stock_move_id
                    if stock_move_id:
                        po_line = stock_move_id.purchase_line_id
                        picking_id = stock_move_id.picking_id
                    else:
                        if credit_move_id:
                            po_line = credit_move_id.purchase_line_id
                            stock_move_id = credit_move_id.y_stock_move_id
                            picking_id = stock_move_id.picking_id
                        if debit_move_id:
                            po_line = debit_move_id.purchase_line_id
                            stock_move_id = debit_move_id.y_stock_move_id
                            picking_id = stock_move_id.picking_id

            is_clean_po = bool(po_line) and len(po_line.order_id) == 1
            # Manual override: a journal item with no real PO trace can be
            # explicitly attached to a PO via the Manual Reconcile action.
            manual_po = aml.y_manual_po_id if not is_clean_po else False

            if is_clean_po or manual_po:
                po_id = po_line.order_id.id if is_clean_po else manual_po.id
                entry = po_result_map.get(po_id)
                if entry is None:
                    if is_clean_po:
                        entry = {
                            'purchase_id': po_id,
                            'partner_id': po_line.order_id.partner_id.id if po_line.order_id.partner_id else None,
                            'picking_id': picking_id.id if picking_id else None,
                            'date_done': stock_move_id.date if stock_move_id else None,
                            'bill_refs': set(),
                            'credit': 0.0,
                            'debit': 0.0,
                            'company_id': aml.company_id.id,
                            'move_line_ids': [],
                            'has_manual': False,
                        }
                    else:
                        entry = {
                            'purchase_id': po_id,
                            'partner_id': manual_po.partner_id.id if manual_po.partner_id else None,
                            'picking_id': None,
                            'date_done': None,
                            'bill_refs': set(),
                            'credit': 0.0,
                            'debit': 0.0,
                            'company_id': aml.company_id.id,
                            'move_line_ids': [],
                            'has_manual': False,
                        }
                    po_result_map[po_id] = entry
                else:
                    # Backfill picking/date/partner if the first time we saw
                    # this PO was via a manual-tagged line lacking them.
                    if is_clean_po:
                        if not entry.get('picking_id') and picking_id:
                            entry['picking_id'] = picking_id.id
                        if not entry.get('date_done') and stock_move_id:
                            entry['date_done'] = stock_move_id.date
                        if not entry.get('partner_id') and po_line.order_id.partner_id:
                            entry['partner_id'] = po_line.order_id.partner_id.id

                if aml.debit > 0:
                    entry['debit'] += aml.debit
                if aml.credit > 0:
                    entry['credit'] += aml.credit
                if aml.move_id.name:
                    entry['bill_refs'].add(aml.move_id.name)
                entry['move_line_ids'].append(aml.id)
                if manual_po:
                    entry['has_manual'] = True
                continue

            # --- Not a clean single-PO trace: ambiguous multi-PO or no PO ---
            if po_line and len(po_line.order_id) > 1 and aml.id not in multi_po_aml_ids:
                multi_po_aml_ids.append(aml.id)

            ref = aml.y_manual_grir_reco_ref
            partner = aml.partner_id or aml.move_id.partner_id

            if ref:
                if ref not in manual_result_map:
                    manual_result_map[ref] = {
                        'purchase_id': None,
                        'partner_id': partner.id if partner else None,
                        'picking_id': None,
                        'date_done': None,
                        'bill_refs': set(),
                        'credit': 0.0,
                        'debit': 0.0,
                        'company_id': aml.company_id.id,
                        'move_line_ids': [],
                        'manual_ref': ref,
                    }
                if aml.debit > 0:
                    manual_result_map[ref]['debit'] += aml.debit
                if aml.credit > 0:
                    manual_result_map[ref]['credit'] += aml.credit
                if aml.move_id.name:
                    manual_result_map[ref]['bill_refs'].add(aml.move_id.name)
                manual_result_map[ref]['move_line_ids'].append(aml.id)
            else:
                non_po_singles[aml.id] = {
                    'purchase_id': None,
                    'partner_id': partner.id if partner else None,
                    'picking_id': None,
                    'date_done': None,
                    'bill_refs': {aml.move_id.name} if aml.move_id.name else set(),
                    'credit': aml.credit,
                    'debit': aml.debit,
                    'company_id': aml.company_id.id,
                    'move_line_ids': [aml.id],
                    'manual_ref': False,
                }

        report_insert_vals = []

        # 1. Purchase Order aggregated rows
        for po_id, data in po_result_map.items():
            if data['debit'] == 0 and data['credit'] == 0:
                continue

            difference = data['credit'] - data['debit']
            status = 'reconciled' if difference == 0 else 'partially'

            report_insert_vals.append({
                'y_purchase_id': data['purchase_id'],
                'y_partner_id': data['partner_id'],
                'y_bill_journal_entry_reference': ", ".join(sorted(list(data['bill_refs']))),
                'y_credit': data['credit'],
                'y_debit': data['debit'],
                'y_diffrence_value': difference,
                'y_user_id': self.env.user.id,
                'y_company_id': data['company_id'],
                'y_status': status,
                'y_move_line_ids': [(6, 0, data['move_line_ids'])],
                'y_manual_reco_ref': False,
                'y_has_manual_match': data.get('has_manual', False),
            })

        # 2. Manually-matched rows (grouped purely by the custom match ref —
        # NOT by Odoo's native reconciliation)
        for data in manual_result_map.values():
            if data['debit'] == 0 and data['credit'] == 0:
                continue

            difference = data['credit'] - data['debit']
            status = 'reconciled' if difference == 0 else 'partially'

            report_insert_vals.append({
                'y_purchase_id': data['purchase_id'],
                'y_partner_id': data['partner_id'],
                'y_bill_journal_entry_reference': ", ".join(sorted(list(data['bill_refs']))),
                'y_credit': data['credit'],
                'y_debit': data['debit'],
                'y_diffrence_value': difference,
                'y_user_id': self.env.user.id,
                'y_company_id': data['company_id'],
                'y_status': status,
                'y_move_line_ids': [(6, 0, data['move_line_ids'])],
                'y_manual_reco_ref': data['manual_ref'],
                'y_has_manual_match': True,
            })

        # 3. Plain non-PO / non-matched singles — always un_reconciled,
        # exactly like the original report behaviour.
        for data in non_po_singles.values():
            report_insert_vals.append({
                'y_purchase_id': data['purchase_id'],
                'y_partner_id': data['partner_id'],
                'y_bill_journal_entry_reference': ", ".join(sorted(list(data['bill_refs']))),
                'y_credit': data['credit'],
                'y_debit': data['debit'],
                'y_diffrence_value': data['credit'] - data['debit'],
                'y_user_id': self.env.user.id,
                'y_company_id': data['company_id'],
                'y_status': 'un_reconciled',
                'y_move_line_ids': [(6, 0, data['move_line_ids'])],
                'y_manual_reco_ref': False,
                'y_has_manual_match': False,
            })

        if report_insert_vals:
            # ORM create (rather than raw bulk INSERT) so the
            # y_move_line_ids many2many relation is populated correctly.
            self.sudo().create(report_insert_vals)

    def button_view_report(self):
        self.retrieve_grir_report()
        view_id = self.env.ref("grir_reconciliation_report.view_grir_reconciliation_report_list").id
        return {
            'name': "GRIR Register(New)1",
            'type': 'ir.actions.act_window',
            'res_model': 'grir.reconciliation.report',
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'target': 'current',
        }

    # ------------------------------------------------------------------
    # Manual reconcile / revoke — these NEVER touch Odoo's native
    # accounting reconciliation. They only set/clear a custom tag
    # (y_manual_grir_reco_ref) on account.move.line, used purely to
    # group rows in this report.
    # ------------------------------------------------------------------
    def _get_next_manual_reco_ref(self):
        ref = self.env['ir.sequence'].sudo().next_by_code('grir.manual.reconcile.ref')
        if not ref:
            # Fall back to creating the sequence on the fly if the data
            # file hasn't been loaded yet.
            seq = self.env['ir.sequence'].sudo().create({
                'name': 'GRIR Manual Reconcile Reference',
                'code': 'grir.manual.reconcile.ref',
                'prefix': 'MREC/%(year)s/',
                'padding': 5,
            })
            ref = seq.next_by_id()
        return ref

    def _reconcile_view_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': "GRIR Register(New)1",
            'res_model': 'grir.reconciliation.report',
            'view_mode': 'list',
            'views': [(self.env.ref("grir_reconciliation_report.view_grir_reconciliation_report_list").id, 'list')],
            'target': 'current',
        }

    def action_manual_reconcile_lines(self):
        """Two supported selections:

        1. One PO row + one or more non-PO (manual entry) rows: the manual
           entries' journal items get tagged with y_manual_po_id = that PO.
           On the next report run they fold directly into that PO's own
           row, carrying its PO number, and the PO's status recalculates
           from the combined (real + manual) credit/debit — reconciled if
           it now nets to zero, partially otherwise.

        2. Two or more non-PO rows, no PO involved: the old pure manual
           match — journal items get tagged with a shared custom
           y_manual_grir_reco_ref and are grouped into their own row.

        Neither path touches Odoo's native accounting reconciliation.
        """
        if not self:
            raise UserError(_("Please select at least one line to reconcile."))

        po_rows = self.filtered(lambda r: r.y_purchase_id)
        non_po_rows = self - po_rows

        if len(po_rows) > 1:
            raise UserError(_(
                "Select only one Purchase Order line at a time — attach "
                "manual entries to one PO per action."
            ))

        if po_rows:
            # --- Path 1: attach manual entries to this PO ---
            po = po_rows.y_purchase_id
            move_lines = non_po_rows.mapped('y_move_line_ids')
            if not move_lines:
                raise UserError(_(
                    "Select at least one manual (non-PO) line along with "
                    "the Purchase Order line."
                ))
            if any(r.y_purchase_id for r in non_po_rows):
                # Shouldn't happen given the split above, but guard anyway.
                raise UserError(_("Only one Purchase Order line may be selected."))

            already_tagged = move_lines.filtered(
                lambda l: l.y_manual_po_id or l.y_manual_grir_reco_ref
            )
            if already_tagged:
                raise UserError(_(
                    "Some selected manual line(s) are already manually "
                    "matched. Revoke first if you want to re-match them."
                ))

            move_lines.write({'y_manual_po_id': po.id})

        else:
            # --- Path 2: pure manual-to-manual match, no PO ---
            move_lines = self.mapped('y_move_line_ids')
            if not move_lines:
                raise UserError(_("The selected line(s) have no journal items to reconcile."))

            already_matched = move_lines.filtered(
                lambda l: l.y_manual_grir_reco_ref or l.y_manual_po_id
            )
            if already_matched:
                raise UserError(_(
                    "Some selected line(s) are already manually reconciled. "
                    "Revoke first if you want to re-match them."
                ))

            if len(move_lines) < 2:
                raise UserError(_(
                    "Select at least two lines (rows) so there's something "
                    "to match against — or select one Purchase Order line "
                    "plus the manual entry line(s) that should close it."
                ))

            ref = self._get_next_manual_reco_ref()
            move_lines.write({'y_manual_grir_reco_ref': ref})

        # Rebuild the report so the grid reflects the new grouping/status
        # right away.
        self.retrieve_grir_report()
        return self._reconcile_view_action()

    def action_revoke_manual_reconcile(self):
        """Select previously manually-matched row(s) — whether folded into
        a PO row (y_manual_po_id) or grouped on their own
        (y_manual_grir_reco_ref) — and clear the relevant tag(s) off their
        underlying journal items. The report then falls back to its
        original state for those lines."""
        if not self:
            raise UserError(_("Please select at least one line to revoke."))

        move_lines = self.mapped('y_move_line_ids')
        po_tagged = move_lines.filtered('y_manual_po_id')
        ref_tagged = move_lines.filtered('y_manual_grir_reco_ref')

        if not po_tagged and not ref_tagged:
            raise UserError(_(
                "None of the selected line(s) are manually reconciled — "
                "nothing to revoke."
            ))

        if po_tagged:
            po_tagged.write({'y_manual_po_id': False})

        if ref_tagged:
            refs = list(set(ref_tagged.mapped('y_manual_grir_reco_ref')))
            # Clear the tag from ALL journal items carrying this ref (not
            # just the ones on the selected report row), so a group is
            # always revoked completely, even if only part of it was
            # selected.
            all_matched_lines = self.env['account.move.line'].search(
                [('y_manual_grir_reco_ref', 'in', refs)]
            )
            all_matched_lines.write({'y_manual_grir_reco_ref': False})

        self.retrieve_grir_report()
        return self._reconcile_view_action()
