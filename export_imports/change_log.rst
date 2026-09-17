V17.0.0.9 -----> V18.0.0.1(**22/Oct/2024**)**$@g@r
====================================================
Conversion

V18.0.0.1 -----> V18.0.0.2(**29/Oct/2024**)**$@g@r
====================================================
added manual exchange rate functionality
and addee picking to accounts depends to flow grn valuation rate to account.move

V18.0.0.2 -----> V18.0.0.3(**29/Oct/2024**)***Anke***
=====================================================
Updated Precarrage Fields

V18.0.0.3 -----> V18.0.0.4(**29/Nov/2024**)***Anke***
=====================================================
Mode Of Transportation made required in port master

V18.0.0.4 -----> V18.0.0.5(**10/Dec/2024**)***Anke***
=====================================================
Rename : Mode of transportation to Mode of Shipment
Final Destination ==> link to port master

V18.0.0.5 -----> V18.0.0.6(**31/Dec/2024**)***Anke***
=====================================================
active field added in port master

V18.0.0.7 -----> V18.0.0.8(**31/Dec/2024**)***$@g@r***
=====================================================
added exchange rate functionality

V18.0.1.3 -----> V18.0.1.4(**10/JAN/2025**)***$@g@r***
=====================================================
added mode of shipment in picking screen

V18.0.1.4 -----> V18.0.1.5(**10/JAN/2025**)***$@g@r***
=====================================================
removed mode of shipment in picking screen

V18.0.1.5 -----> V18.0.1.6(**15/JAN/2025**)***$@g@r***
=====================================================
removed code

V18.0.1.6 -----> V18.0.1.7(**25/JAN/2025**)***$@g@r***
=====================================================
changed onchange code

V18.0.1.7 -----> V18.0.1.8(**04/APR/2025**)***$@g@r***
=====================================================
removed Import Report and Export Report

V18.0.1.8 -----> V18.0.1.9(**04/APR/2025**)***Muhammed***
=====================================================
Added fields


V18.0.1.9 -----> V18.0.2.0(**24/SEP/2025**)***$@g@r***
=====================================================
removed import_duty app dependency and commented onchanged
and Removed onchange function to update the exchange rate in account move

V18.0.2.1 -----> V18.0.2.2(**30/Oct/2025**)***Anke***
=====================================================
y_stock_packaging_id update in onchange function

==========================================================================================================
## [18.0.2.3] - 2025-11-05 ***Anke***
### ✏️ Update: Label Correction

**Module:** `export_imports`

#### 🔹 Changes
| File | Line | Old Text | Corrected Text |
|------|------|-----------|----------------|
| `models/import_export_addon.py` | 86 | PackagingList Ids | Package List Lines |

#### ✅ Impact
- Fixed a label typo for improved clarity.
- No functional changes.

==========================================================================================================
[IMP] Improved Currency Rate Calculation on Create
[18.0.2.4] - 2025-11-14 Anke

🔹 Changes

Updated create() method to fetch conversion rate based on payment date.

Added condition to skip rate update when triggered from Register Payment Wizard.

Manual rate now uses inverse of the actual conversion rate using Odoo’s native API.

File	Line	Old Text	New Text
models/account_payment.py	—	res.y_manual_rate = res.currency_id.inverse_rate	Updated logic to compute rate based on res.date using _get_conversion_rate()

✅ Impact

Accurate currency rate applied based on payment date.
Avoids wrong rate override during Register Payment flow.
Ensures consistent and reliable financial values.

V18.0.2.5 -----> V18.0.2.6(**02/DEC/2025**)***$@g@r***
=====================================================
added exchange rate functionality 

V18.0.2.6 -----> V18.0.2.7(**15/DEC/2025**)***$@g@r***
=====================================================
added exchange rate functionality in sale and purchase order

V18.0.2.7 -----> V18.0.2.8(**13/Feb/2025**)***Anke***
===========================================================
method changed from _prepare_move_line_default_vals() to _prepare_move_lines_per_type()

V18.0.2.8 -----> V18.0.2.9(**15/Feb/2025**)***Anke***
===========================================================
Deciaml issue been fixed

V18.0.2.9 -----> V18.0.3.0(**20/Feb/2025**)***Anke***
===========================================================
Fix the manual rate flow register payment to payment

V18.0.3.0 -----> V18.0.3.1(**25/Feb/2026**)***$@g@r***
===========================================================
fix the posting of exchange rate entry


V18.0.3.1 -----> V18.0.3.2(**25/Feb/2026**)***$@g@r***
===========================================================
same code as 3.0 version

18.0.3.2 ----> 18.0.3.3**(26/02/2026)***Anke***
===============================================
Decimal Issue fix

18.0.3.3 ----> 18.0.3.4**(13/03/2026)***Anke***
===============================================
Fixed currency check logic in check_same_currency compute method.
Replaced incorrect assignment that always set y_is_same_currency to True.
Updated compute methods to assign values directly instead of using write() inside compute.


18.0.3.4 ----> 18.0.3.5**(16/03/2026)***$@G@r***
===============================================
flow exchange rate from invoice to register payment screen
changed create method logic to get the exchange rate