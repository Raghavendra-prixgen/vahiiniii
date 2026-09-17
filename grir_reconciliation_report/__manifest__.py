# -*- coding: utf-8 -*-
{
    'name': 'GRIR Reconciliation Report',
    'version': '18.0.0.0.2',
    'category': 'Accounting/Reporting',
    'summary': 'GRIR Reconciliation Report — totals match General Ledger, covers all 12 business scenarios',
    'description': """
GRIR (Goods Receipt / Invoice Receipt) Reconciliation Report
============================================================
Scenarios covered:
  1.  Local PO – normal GRN + VB fully reconciled
  2.  Price Difference in Vendor Bill (stock revaluation)
  3.  FCY Price Difference (exchange-rate entries)
  4.  Service Bill (no GRN)
  5.  VB without GRN / Ledger change
  6.  Standalone Journal Entry
  7.  Partial Vendor Bill
  8.  Vendor Bill Not Booked
  9.  Return Without Debit Note
 10.  Debit Note Without Return
 11.  Return Before Vendor Bill
 12.  VB Price Diff – Non-Stock Product

Prerequisites:
  - account.account must have y_gl_code_type = 'assi' for GRIR accounts
  - account.move.line must have y_stock_move_id field (Many2one stock.move)
    — this field is expected to exist in your customised Odoo instance
    """,
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'depends': [
        'purchase',
        'stock',
        'account',
        'stock_account',
        'purchase_stock',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/grir_report.xml',
        # 'views/grir_reconciliation_report_views.xml',
        # 'views/grir_reconciliation_report_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
