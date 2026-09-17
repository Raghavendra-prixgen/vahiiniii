# -*- coding: utf-8 -*-
"""
GRIR Reconciliation Report — Odoo 18
======================================
"""

from odoo import fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)


def _fmt_sql(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "NULL" if not v else "TRUE"   # False partner → NULL
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, datetime):
        return "'%s'" % v.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(v, date):
        return "'%s'" % v.strftime('%Y-%m-%d')
    if isinstance(v, str):
        return "'%s'" % v.replace("'", "''")
    raise ValueError("Unsupported: %r" % v)


def _ins(table, data):
    cols = ",".join('"%s"' % k for k in data)
    vals = ",".join(_fmt_sql(v) for v in data.values())
    return 'INSERT INTO "%s" (%s) VALUES (%s)' % (table, cols, vals)


def _ids(lst):
    """Safe SQL IN / = clause from a Python list of ints."""
    lst = [int(x) for x in lst]
    if not lst:
        return "= -1"
    if len(lst) == 1:
        return "= %d" % lst[0]
    return "IN (%s)" % ",".join(str(x) for x in lst)


# ── Business logic helpers ────────────────────────────────────────────────────

def _status(debit, credit):
    diff = debit - credit
    if abs(diff) < 0.01:
        return 'reconciled'
    if debit > 0.01 and credit > 0.01:
        return 'partially'
    return 'un_reconciled'


def _scenario(r):
    """r is a dict of flags from the SQL row."""
    grn    = r['has_grn']
    vb     = r['has_vb']
    dn     = r['has_dn']
    ret    = r['has_return']
    reval  = r['has_reval']
    fcy    = r['has_fcy']
    debit  = r['debit']
    credit = r['credit']

    if grn and fcy and reval:   return '3. FCY Price Diff – Revaluation'
    if grn and fcy:             return '3. FCY Price Difference'
    if ret and dn:              return '9. Return + Debit Note'
    if ret:                     return '9. Return Without Debit Note'
    if dn and not ret:          return '10. Debit Note Without Return'
    if grn and reval and vb:    return '2. Price Diff – Stock Revaluation'
    if grn and reval:           return '11. Return Before Vendor Bill (Reval)'
    if grn and not vb and not dn: return '8. Vendor Bill Not Booked'
    if grn and vb and abs(debit - credit) > 0.01: return '7. Partial Vendor Bill'
    if grn and vb:              return '1. Local PO – Normal Flow'
    if vb:                      return '12. VB / Price Diff (Non-Stock)'
    return '1. Local PO – GRN Entry'


# ── Model ─────────────────────────────────────────────────────────────────────

class GrirReconciliationReport(models.Model):
    _name = "grir.reconciliation.report"
    _description = "GRIR Reconciliation Report"
    _order = "y_date_done desc, y_purchase_id"

    def init(self):
        """Drop any old PostgreSQL VIEW from earlier module versions."""
        self._cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_class
                     WHERE relname = %(n)s AND relkind = 'v'
                ) THEN
                    EXECUTE 'DROP VIEW ' || quote_ident(%(n)s);
                END IF;
            END$$;
        """, {'n': 'grir_reconciliation_report'})

    # ── Fields ────────────────────────────────────────────────────────────────
    y_purchase_id   = fields.Many2one('purchase.order', string="PO Number",          readonly=True)
    y_picking_id    = fields.Many2one('stock.picking',  string="GRN Number",         readonly=True)
    y_partner_id    = fields.Many2one('res.partner',    string="Vendor",             readonly=True)
    y_company_id    = fields.Many2one('res.company',    string="Company",            readonly=True)
    y_date_done     = fields.Date(                      string="Date",               readonly=True)
    y_bill_ref      = fields.Char(                      string="Journal / VB Entry", readonly=True)
    y_case_scenario = fields.Char(                      string="Case / Scenario",    readonly=True)
    y_debit         = fields.Float(string="Debit",   digits=(16, 2), readonly=True)
    y_credit        = fields.Float(string="Credit",  digits=(16, 2), readonly=True)
    y_balance       = fields.Float(string="Balance", digits=(16, 2), readonly=True)
    y_status        = fields.Selection([
        ('reconciled',    'Completely Reconciled'),
        ('partially',     'Partially Reconciled'),
        ('un_reconciled', 'Unreconciled'),
    ], string="Status", readonly=True)
    y_user_id       = fields.Many2one('res.users', string="User",
                                      default=lambda self: self.env.user)

    # ── Entry point ───────────────────────────────────────────────────────────
    def action_open_grir_report(self):
        self._compute_report()
        return {
            'name': _("GRIR Reconciliation Report"),
            'type': 'ir.actions.act_window',
            'res_model': 'grir.reconciliation.report',
            'view_mode': 'list,pivot',
            'views': [(False, 'list'), (False, 'pivot')],
            'domain': [('y_user_id', '=', self.env.user.id)],
            'target': 'current',
            'context': dict(self._context, search_default_group_status=1),
        }

    # ── Core ──────────────────────────────────────────────────────────────────
    def _compute_report(self, start_date=False, end_date=False, companies=False):

        # ── 0. Setup ──────────────────────────────────────────────────────────
        allowed_companies = (
            companies
            or self._context.get('allowed_company_ids')
            or self.env.companies.ids
            or self.env.user.company_ids.ids
        )

        grir_accounts = self.env['account.account'].search([
            ('y_gl_code_type', '=', 'assi'),
            ('company_ids', 'in', allowed_companies),
        ])
        if not grir_accounts:
            raise ValidationError(
                _("GRIR account (y_gl_code_type='assi') not configured for the selected company.")
            )

        grir_ids    = [int(x) for x in grir_accounts.ids]
        company_ids = [int(x) for x in allowed_companies]
        uid         = int(self.env.user.id)

        # date filter fragment (applied to aml.date)
        date_filter = ""
        if start_date:
            date_filter += " AND aml.date >= '%s'" % start_date
        if end_date:
            date_filter += " AND aml.date <= '%s'" % end_date

        # ── 1. Wipe old rows ──────────────────────────────────────────────────
        self._cr.execute(
            "DELETE FROM grir_reconciliation_report WHERE y_user_id = %s",
            (uid,)
        )

        # ══════════════════════════════════════════════════════════════════════
        # STEP 1 — PO-grouped SQL query
        #
        # Joins every posted GRIR AML to a purchase_order through ANY of:
        #   Path A: aml → account_move.stock_move_id → purchase_order_line → PO
        #   Path B: aml.y_stock_move_id → purchase_order_line → PO
        #   Path C: aml → account_move.purchase_id (VB / DN)
        #
        # COALESCE picks the first non-null PO found across paths A/B/C.
        # Rows where all three paths yield NULL are standalone (Step 2).
        # ══════════════════════════════════════════════════════════════════════
        po_sql = """
            SELECT
                po.id                                       AS po_id,
                po.partner_id                               AS partner_id,
                po.company_id                               AS company_id,
                SUM(CASE WHEN aml.debit  > 0 THEN aml.debit  ELSE 0 END)   AS debit,
                SUM(CASE WHEN aml.credit > 0 THEN aml.credit ELSE 0 END)   AS credit,
                STRING_AGG(DISTINCT am.name, ', '
                           ORDER BY am.name)                AS bill_refs,
                MAX(aml.date)                               AS latest_date,
                /* pick one picking (earliest by id) for the GRN column */
                MIN(sp.id)                                  AS picking_id,
                /* flags */
                BOOL_OR(
                    am.move_type = 'entry'
                    AND am.stock_move_id IS NOT NULL
                    AND (sp2.return_id IS NULL
                         AND (sp2.origin IS NULL
                              OR sp2.origin NOT ILIKE 'Return%'))
                )                                           AS has_grn,
                BOOL_OR(am.move_type = 'in_invoice')        AS has_vb,
                BOOL_OR(am.move_type = 'in_refund')         AS has_dn,
                BOOL_OR(
                    am.move_type = 'entry'
                    AND am.stock_move_id IS NOT NULL
                    AND (sp2.return_id IS NOT NULL
                         OR (sp2.origin ILIKE 'Return%%'))
                )                                           AS has_return,
                /* revaluation: nested SVL entry = entry-type move linked to
                   a stock_move whose SVL has a parent SVL */
                BOOL_OR(
                    am.move_type = 'entry'
                    AND am.stock_move_id IS NOT NULL
                    AND EXISTS (
                        SELECT 1 FROM stock_valuation_layer svl2
                         WHERE svl2.stock_move_id = sm_path.sm_id
                           AND svl2.stock_valuation_layer_id IS NOT NULL
                    )
                )                                           AS has_reval,
                BOOL_OR(
                    ABS(COALESCE(aml.amount_currency, 0))
                    != ABS(COALESCE(aml.balance, 0))
                    AND COALESCE(aml.amount_currency, 0) != 0
                )                                           AS has_fcy,
                STRING_AGG(DISTINCT aml.id::text, ',')      AS aml_ids
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            /* ── Path A/B: resolve stock_move id from am or aml ── */
            LEFT JOIN LATERAL (
                SELECT COALESCE(am.stock_move_id, aml.y_stock_move_id) AS sm_id
            ) sm_path ON TRUE
            /* ── PO via stock_move → purchase_order_line (Path A / B) ── */
            LEFT JOIN stock_move sm_pol ON sm_pol.id = sm_path.sm_id
            LEFT JOIN purchase_order_line pol_sm ON pol_sm.id = sm_pol.purchase_line_id
            LEFT JOIN purchase_order po_sm ON po_sm.id = pol_sm.order_id
            /* ── PO via VB/DN: aml.purchase_line_id (Path C, Odoo 18) ── */
            LEFT JOIN purchase_order_line pol_vb ON pol_vb.id = aml.purchase_line_id
            LEFT JOIN purchase_order po_vb ON po_vb.id = pol_vb.order_id
            /* ── Resolve: prefer stock-move path, fall back to invoice line ── */
            JOIN purchase_order po ON po.id = COALESCE(po_sm.id, po_vb.id)
            /* ── GRN picking ── */
            LEFT JOIN stock_move sm_rec ON sm_rec.id = sm_path.sm_id
            LEFT JOIN stock_picking sp  ON sp.id = sm_rec.picking_id
            /* sp2 = same picking, used for return/has_grn flag expressions */
            LEFT JOIN stock_picking sp2 ON sp2.id = sm_rec.picking_id
            WHERE
                aml.account_id {grir_ids}
                AND aml.parent_state = 'posted'
                AND aml.company_id {company_ids}
                AND po.state IN ('purchase','done')
                {date_filter}
            GROUP BY po.id, po.partner_id, po.company_id
        """.format(
            grir_ids    = _ids(grir_ids),
            company_ids = _ids(company_ids),
            date_filter = date_filter,
        )

        self._cr.execute(po_sql)
        po_rows = self._cr.dictfetchall()

        # collect all AML ids already assigned to a PO
        seen_aml_ids = set()
        for row in po_rows:
            if row['aml_ids']:
                seen_aml_ids.update(int(x) for x in row['aml_ids'].split(','))

        # ── INSERT PO rows ────────────────────────────────────────────────────
        for r in po_rows:
            debit  = float(r['debit']  or 0)
            credit = float(r['credit'] or 0)
            diff   = debit - credit
            scen   = _scenario({
                'has_grn':    r['has_grn'],
                'has_vb':     r['has_vb'],
                'has_dn':     r['has_dn'],
                'has_return': r['has_return'],
                'has_reval':  r['has_reval'],
                'has_fcy':    r['has_fcy'],
                'debit':      debit,
                'credit':     credit,
            })
            self._cr.execute(_ins('grir_reconciliation_report', {
                'y_purchase_id':   int(r['po_id']),
                'y_picking_id':    int(r['picking_id']) if r['picking_id'] else None,
                'y_partner_id':    int(r['partner_id']) if r['partner_id'] else None,
                'y_company_id':    int(r['company_id']) if r['company_id'] else None,
                'y_date_done':     r['latest_date'],
                'y_bill_ref':      r['bill_refs'] or '',
                'y_case_scenario': scen,
                'y_debit':         round(debit,  2),
                'y_credit':        round(credit, 2),
                'y_balance':       round(diff,   2),
                'y_status':        _status(debit, credit),
                'y_user_id':       uid,
            }))

        # ══════════════════════════════════════════════════════════════════════
        # STEP 2 — Standalone: service bills / manual JVs (no PO link)
        # Group by account_move → one row per move.
        # ══════════════════════════════════════════════════════════════════════
        if seen_aml_ids:
            excl = "AND aml.id NOT IN (%s)" % ",".join(str(x) for x in seen_aml_ids)
        else:
            excl = ""

        sa_sql = """
            SELECT
                am.id                                       AS move_id,
                am.name                                     AS move_name,
                am.move_type                                AS move_type,
                COALESCE(am.partner_id, aml.partner_id)     AS partner_id,
                aml.company_id                              AS company_id,
                MAX(aml.date)                               AS latest_date,
                SUM(CASE WHEN aml.debit  > 0 THEN aml.debit  ELSE 0 END)  AS debit,
                SUM(CASE WHEN aml.credit > 0 THEN aml.credit ELSE 0 END)  AS credit
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            WHERE
                aml.account_id {grir_ids}
                AND aml.parent_state = 'posted'
                AND aml.company_id {company_ids}
                {excl}
                {date_filter}
            GROUP BY am.id, am.name, am.move_type,
                     COALESCE(am.partner_id, aml.partner_id),
                     aml.company_id
        """.format(
            grir_ids    = _ids(grir_ids),
            company_ids = _ids(company_ids),
            excl        = excl,
            date_filter = date_filter,
        )

        self._cr.execute(sa_sql)
        sa_rows = self._cr.dictfetchall()

        for r in sa_rows:
            debit  = float(r['debit']  or 0)
            credit = float(r['credit'] or 0)
            diff   = debit - credit
            mt     = r['move_type'] or ''
            if mt == 'in_invoice':
                scen = '4. Service Bill (No GRN)'
            elif mt == 'in_refund':
                scen = '10. Debit Note Without Return'
            else:
                scen = '6. Standalone Journal Entry'

            self._cr.execute(_ins('grir_reconciliation_report', {
                'y_purchase_id':   None,
                'y_picking_id':    None,
                'y_partner_id':    int(r['partner_id']) if r['partner_id'] else None,
                'y_company_id':    int(r['company_id']) if r['company_id'] else None,
                'y_date_done':     r['latest_date'],
                'y_bill_ref':      r['move_name'] or '',
                'y_case_scenario': scen,
                'y_debit':         round(debit,  2),
                'y_credit':        round(credit, 2),
                'y_balance':       round(diff,   2),
                'y_status':        _status(debit, credit),
                'y_user_id':       uid,
            }))

        _logger.info(
            "GRIR Report: %d PO rows + %d standalone rows for user %s",
            len(po_rows), len(sa_rows), self.env.user.login
        )
