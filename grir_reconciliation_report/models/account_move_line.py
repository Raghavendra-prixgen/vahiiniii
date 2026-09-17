# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Purely custom tag used ONLY by the GRIR Reconciliation Report to group
    # journal items together (e.g. manual closing entries that carry no PO
    # reference). This is intentionally independent of Odoo's native
    # accounting reconciliation (full_reconcile_id / matched_credit_ids /
    # matched_debit_ids) — setting/clearing this field does NOT reconcile or
    # unreconcile anything in Accounting, it only drives grouping/status in
    # the GRIR report.
    y_manual_grir_reco_ref = fields.Char(
        string="Manual GRIR Reconcile Ref",
        copy=False,
        index=True,
        help="Custom matching reference set by the GRIR Reconciliation "
             "Report's 'Manual Reconcile' action when two or more manual "
             "entries (no PO reference at all) are matched to each other. "
             "Lines sharing the same reference are grouped together and "
             "shown as reconciled / partially reconciled in the report, "
             "independent of real accounting reconciliation.",
    )

    # Used when a manual journal entry is posted specifically to close the
    # GRIR gap on an EXISTING Purchase Order (the manual entry itself has
    # no real purchase_line_id trace). Setting this makes the GRIR report
    # fold this journal item into that PO's row on future runs, exactly as
    # if it had been traced there naturally. This is a report-only tag —
    # it intentionally does NOT touch the real purchase_line_id field, so
    # nothing else in Odoo (vendor bill matching, PO billed quantities/
    # amounts, etc.) is affected by it.
    y_manual_po_id = fields.Many2one(
        'purchase.order',
        string="Manual GRIR PO Reference",
        copy=False,
        index=True,
        help="Set by the GRIR Reconciliation Report's 'Manual Reconcile' "
             "action when a manual entry is matched against a specific "
             "Purchase Order's GRIR balance. Report-only — does not affect "
             "purchase billing/matching elsewhere in Odoo.",
    )
