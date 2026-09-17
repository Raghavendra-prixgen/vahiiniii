# GRIR Reconciliation Report — Odoo 18

## Module: `grir_reconciliation_report`

---

## 1. Architecture Overview

```
Menu Click
    └─► ir.actions.server  (action_grir_reconciliation_server)
            └─► model.action_open_grir_report()
                    ├─► _rebuild_view()          ← drops & recreates PG view
                    │       ├─ resolve company filter
                    │       ├─ validate GRIR accounts (y_gl_code_type='assi')
                    │       └─ execute _build_query(…)
                    └─► return ir.actions.act_window → list + pivot
```

### PostgreSQL View Structure

```
grir_reconciliation_report  (PostgreSQL VIEW)
│
├─ ReconciliationAmounts CTE   ← aggregates account_partial_reconcile per aml
│
├─ BUCKET A – GrnBucket        ← stock_move journal entries on GRIR account
├─ BUCKET B – VbBucket         ← in_invoice / in_refund lines on GRIR account
├─ BUCKET C – SvlBucket        ← stock_valuation_layer linked entries
├─ BUCKET D – FxBucket         ← FX gain/loss entries (via partial reconcile chain)
├─ BUCKET E – StandaloneBucket ← manual JVs / service bills
│
├─ Unified CTE                 ← UNION ALL of all buckets + scenario_key tag
│
└─ Final SELECT                ← ROW_NUMBER, human label, status derivation
```

---

## 2. Business Scenario Mapping

| # | Scenario | Buckets Used | scenario_key |
|---|----------|-------------|--------------|
| 1 | Local PO – Normal Flow | A + B | GRN + VB_NORMAL |
| 2 | Price Difference in VB | A + B + C | GRN + VB_NORMAL + PRICE_DIFF_REVAL |
| 3 | FCY Price Difference | A + B + C + D | GRN + VB_NORMAL + FCY_REVAL + FCY_EXCH |
| 4 | Service Bill (no GRN) | E | SERVICE_BILL |
| 5 | Ledger Change in VB | B | VB_NO_GRN (VB line has no stock_move link) |
| 6 | Standalone Journal Entry | E | STANDALONE_JV |
| 7 | Partial Vendor Bill | A + B | GRN (unreconciled/partial) + VB_NORMAL |
| 8 | VB Not Booked | A only | GRN → status = unreconciled |
| 9 | Return Without Debit Note | A (return picking) | RETURN_GRN → unreconciled |
| 10 | Debit Note Without Return | B | DEBIT_NOTE_NO_RETURN |
| 11 | Return Before VB | A (return) + C | RETURN_GRN + PRICE_DIFF_REVAL |
| 12 | VB Price Diff Non-Stock | B only | VB_NORMAL (no SVL exists) |

---

## 3. Reconciliation Status Logic

Status is derived from **`account_partial_reconcile`** and **`account_full_reconcile`**,
NOT from a naive debit-credit comparison.

```python
is_full_reconciled  = aml.full_reconcile_id IS NOT NULL
is_partial          = reconciled_amount > 0 AND full_reconcile_id IS NULL
unreconciled        = reconciled_amount = 0 AND full_reconcile_id IS NULL
```

Residual amount:
```sql
GREATEST(ABS(balance) - ABS(reconciled_amount), 0)
```

---

## 4. Key Field: `y_gl_code_type = 'assi'`

The GRIR account is identified by `account.account.y_gl_code_type = 'assi'`.
Every bucket filters on this field. If no such account exists for the selected
company, the model raises a `ValidationError` before building the view.

---

## 5. Column Reference

| Column | Description |
|--------|-------------|
| Sl. No | Sequential row number |
| Case / Scenario | Human-readable scenario label |
| PO Number | Linked purchase.order |
| GRN Number | Linked stock.picking |
| Vendor | res.partner |
| Date | Invoice date or stock move date |
| Journal / VB Entry | account.move name (e.g. BILL/2024/00001) |
| Currency | Move currency (hidden unless multi-currency) |
| Debit | GRIR account debit amount |
| Credit | GRIR account credit amount |
| Balance | Debit − Credit |
| Reconciled Amt | Sum of account_partial_reconcile.amount |
| Residual / Open | ABS(Balance) − Reconciled Amt |
| Status | Fully Reconciled / Partially / Unreconciled |
| Company | (hidden by default) |
| Bucket | Internal bucket tag (GRN/VB/SVL/FX/STANDALONE) |

---

## 6. Test Cases

### TC-01: Local PO – Full Reconciliation
```
Steps:
  1. Create PO → Confirm
  2. Receive goods (Validate picking)
  3. Create Vendor Bill from PO → Post
Expected:
  GRN row: Debit=PO_value, Status=reconciled
  VB row:  Credit=PO_value, Status=reconciled
  Residual=0 for both rows
```

### TC-02: Price Difference in Vendor Bill
```
Steps:
  1. PO qty=10, unit_price=100 → GRN posted (Debit=1000)
  2. Vendor Bill unit_price=120 → Post
     → Odoo creates stock revaluation JV automatically
Expected:
  GRN row:   Debit=1000,  Bucket=GRN,  Status=reconciled
  VB row:    Credit=1200, Bucket=VB,   Status=reconciled
  Reval row: Debit=200,   Bucket=SVL,  Scenario="2. Price Diff – Stock Revaluation"
```

### TC-03: Foreign Currency
```
Steps:
  1. PO in USD, company currency INR
  2. GRN at rate 82 → Debit=82000 INR
  3. VB posted at rate 84 → triggers exchange diff JV
Expected:
  GRN row:  Debit=82000, Bucket=GRN
  VB row:   Credit=84000, Bucket=VB
  FX row:   Debit or Credit=2000, Bucket=FX, Scenario="3. FCY – Exchange Diff Entry"
```

### TC-04: Service Bill
```
Steps:
  1. Create vendor bill for service (no PO / no stock move)
  2. Post the bill
Expected:
  1 row: Bucket=STANDALONE, Scenario="4. Service Bill (No GRN)", Status=unreconciled
```

### TC-05: Ledger Change in Vendor Bill
```
Steps:
  1. Normal PO + GRN
  2. On VB, manually change account from GRIR to a different account
  3. Post VB
Expected:
  GRN row appears with Status=unreconciled (no matching VB line on GRIR account)
  Possibly a STANDALONE row if a manual JV corrects it
```

### TC-06: Standalone Journal Entry
```
Steps:
  1. Create manual JV debiting/crediting GRIR account
  2. Post JV
Expected:
  1 row: Bucket=STANDALONE, Scenario="6. Standalone Journal Entry"
```

### TC-07: Partial Vendor Bill
```
Steps:
  1. PO qty=10, receive all 10
  2. VB for qty=6 only → Post
Expected:
  GRN row:  Debit=full_value, Status=partially
  VB row:   Credit=partial_value, Status=unreconciled (no matching GRN line fully)
  Residual = GRN_value - partial_VB_value
```

### TC-08: Vendor Bill Not Booked
```
Steps:
  1. PO → GRN received and validated
  2. No vendor bill created
Expected:
  GRN row: Debit=GRN_value, Status=unreconciled, Residual=GRN_value
```

### TC-09: Return Without Debit Note
```
Steps:
  1. PO → GRN
  2. Create Return picking → Validate
  3. No Debit Note
Expected:
  Original GRN row: Debit=value, Scenario="1. Local PO – GRN Entry"
  Return GRN row:   Credit=value, Scenario="9/11. Return Picking Entry", Status=unreconciled
```

### TC-10: Debit Note Without Return
```
Steps:
  1. PO → GRN → VB
  2. Create Debit Note (in_refund) without stock return
Expected:
  VB row:         Status varies
  Debit Note row: Scenario="10. Debit Note Without Return", Bucket=VB
```

### TC-11: Return Before Vendor Bill
```
Steps:
  1. PO → GRN
  2. Return picking validated (with revaluation if applicable)
  3. Vendor bill created after
Expected:
  GRN row:    Debit=value, Scenario="1. Local PO – GRN Entry"
  Return row: Credit=value, Scenario="9/11. Return Picking Entry"
  Reval row:  Scenario="2. Price Diff – Stock Revaluation" (if applicable)
  VB row:     Status=partially or unreconciled depending on amount match
```

### TC-12: VB Price Diff – Non-Stock Product
```
Steps:
  1. PO for consumable/service product with stock valuation disabled
  2. GRN (no SVL created)
  3. VB at different price
Expected:
  GRN row: Debit=GRN_value,  Bucket=GRN
  VB row:  Credit=VB_value,  Bucket=VB, Scenario="1. Local PO – Vendor Bill"
  No SVL row (non-stock product)
  Status=partially if values differ
```

---

## 7. Performance Notes

- The view is rebuilt on every menu click, injecting a company filter directly
  into SQL (no RLS overhead).
- `ReconciliationAmounts` CTE is computed once and joined to all buckets,
  avoiding repeated subquery scans of `account_partial_reconcile`.
- Recommended indexes (add to your migration script if not present):
  ```sql
  CREATE INDEX IF NOT EXISTS idx_aml_account_company
      ON account_move_line (account_id, company_id);
  CREATE INDEX IF NOT EXISTS idx_aml_y_stock_move
      ON account_move_line (y_stock_move_id);
  CREATE INDEX IF NOT EXISTS idx_am_stock_move
      ON account_move (stock_move_id);
  CREATE INDEX IF NOT EXISTS idx_apr_debit_credit
      ON account_partial_reconcile (debit_move_id, credit_move_id);
  CREATE INDEX IF NOT EXISTS idx_svl_account_move
      ON stock_valuation_layer (account_move_id);
  ```

---

## 8. Module Dependencies

| Module | Why needed |
|--------|-----------|
| `purchase` | purchase.order, purchase.order.line |
| `stock` | stock.picking, stock.move |
| `account` | account.move, account.move.line, account_partial_reconcile |
| `stock_account` | stock_valuation_layer, account_move.stock_move_id |
| `purchase_stock` | stock_move.purchase_line_id |

---

## 9. Export to XLSX

The list view has `export_xlsx="1"` attribute. Users can export via the standard
Odoo ⚙️ → Export option. All visible columns including sums are exported.

For a custom XLSX report with formatting, add `xlsxwriter` to your requirements
and create a `report/` directory with a `ReportXlsx` class inheriting
`report.report_xlsx.abstract`.
