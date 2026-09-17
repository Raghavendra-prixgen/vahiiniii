V17.0.3.9 -----> V18.0.0.1(**22/Oct/2024**)**$@g@r
====================================================
Conversion

V18.0.0.1 -----> V18.0.0.2(**23/Oct/2024**)**$@g@r
====================================================
added boe number and boe date concatinationin payment ref field

V18.0.0.2 -----> V18.0.0.3(**24/Oct/2024**)**$@g@r
====================================================
changed detailed type to type


V18.0.0.3 -----> V18.0.0.4(24/Oct/2024)**$@g@r
====================================================

added additional quantity values to calculate IGSt in import duty struct tab and changed user has group


V18.0.0.4 -----> V18.0.0.5(24/Oct/2024)**$@g@r
====================================================
added additional and mis value to boe line total assesable value

V18.0.0.5 -----> V18.0.0.6(29/Oct/2024)**$@g@r
===================================================
removed export import depends
added valuation or grn condition


V18.0.0.6 -----> V18.0.0.7(08/NOV/2024)**$@g@r
===================================================
added autocomplete functionality in custom exchange rate 
record rule 
valuation rate flow

V18.0.0.9 -----> V18.0.1.0(11/NOV/2024)**$@g@r
===================================================
added port of discharge in downpayment screen and payment screen
and commented code for creating landed cost for additional charges

V18.0.1.0 -----> V18.0.1.1(14/NOV/2024)**$@g@r
===================================================
added parent_of record rule

18.0.1.1 ----> 18.0.1.2(19-Nov-2024) ***Anke****
================================================
For Parent Company Updated sudo()

18.0.1.2 ----> 18.0.1.3(28-Nov-2024) ***$@g@r****
================================================
added included landed cost functionality

18.0.1.3 ----> 18.0.1.4(29-Nov-2024) ***Anke****
=============================================================================
Bug fix(You cannot change a cancelled stock move, create a new line instead.)

18.0.1.4 ----> 18.0.1.5(29-Nov-2024) ***Anke****
================================================
Added downpayment restriction

18.0.1.5 ----> 18.0.1.6(02-DEC-2024) ***$@g@r****
================================================
added conditions in import duty code

18.0.1.6 ----> 18.0.1.7(11-Dec-2024) ***Anke****
================================================
Updated remarks

18.0.1.7 ----> 18.0.1.8(13-Dec-2024) ***Anke****
================================================
Updated remarks(Warehouse)

18.0.1.9 ----> 18.0.2.0(19-Dec-2024) ***$@g@r****
================================================
changed landed cost functionlaity

18.0.2.0 ----> 18.0.2.1(20-Dec-2024) ***$@g@r****
================================================
changed duty payable functionlaity

18.0.2.8 ----> 18.0.2.9 ----> 18.0.3.0(27-Dec-2024) ***Anke****
==============================================================
Updated Assessable Value


18.0.3.1---->18.0.3.2(30-Dec-2024) ***$@g@r****
==============================================================
grn exchange rate should pick from inverse rate instead of rate from currency table

18.0.3.2---->18.0.3.3(01-JAN-2024) ***$@g@r****
==============================================================
removed reset values and reset to draft
cancel boe functionality
added landed cost for duties exempted for other charges

18.0.3.5---->18.0.3.6(01-JAN-2024) ***Anke***
=============================================
BOE Sequence make company sepcific

18.0.3.6 ----> 18.0.3.7(03-Jan-2024) ***Anke***
=============================================
added round landed cost

18.0.3.7 ----> 18.0.3.8(07-Jan-2024) ***$@g@r***
=============================================
added FOC boolean in boe line

18.0.3.8 ----> 18.0.3.9(07-Jan-2024) ***$@g@r***
=============================================
added invisible condition


18.0.3.9 ----> 18.0.4.0(07-Jan-2024) ***$@g@r***
=============================================
removed extra code in _get_price_unit function

18.0.4.2 ----> 18.0.4.3(09-Jan-2024) ***$@g@r***
=============================================
added condition to fetch boe line while posting landed cost

18.0.4.3 ----> 18.0.4.4(09-Jan-2024) ***$@g@r***
=============================================
added po company to boe company field

18.0.4.6 ----> 18.0.4.7(22-Jan-2024) ***$@g@r***
=============================================
changed decimal place to 3 for unit price

18.0.4.7 ----> 18.0.4.8(23-Jan-2024) ***$@g@r***
=============================================
added boe field in landed cost

18.0.4.8 ----> 18.0.4.9(24-Jan-2024) ***$@g@r***
=============================================
changed bill of entry rate functionality

18.0.4.9 ----> 18.0.5.0(24-Jan-2024) ***$@g@r***
=============================================
error fixed

18.0.5.1 ----> 18.0.5.2(24-Jan-2024) ***Anke***
=============================================
bug(serial no) fixed

18.0.5.2 ----> 18.0.5.3(10-FEB-2025) ***$@g@r***
=============================================
bug(serial no) fixed

18.0.5.3 ----> 18.0.5.4(12-FEB-2025) ***$@g@r***
=============================================
changed code for update exchange rate in picking screen

18.0.5.4 ----> 18.0.5.5(21-FEB-2025) ***Anke***
===============================================
duplicate boe bill restrictied

18.0.5.5 ----> 18.0.5.6(24-FEB-2025) ***Anke***
====================================================
Added Restriction for Required purchase order in BOE

18.0.5.6 ----> 18.0.5.7(19-MAR-2025) ***$@g@r***
====================================================
added functionality for uom mismatch valuation price unit

18.0.5.7 ----> 18.0.5.8(28-Mar-2025) ***Anke***
====================================================
bug fix(price unit)

18.0.5.8 ----> 18.0.5.9(29-Mar-2025) ***$@g@r***
====================================================
bug fix related to valuation exchange rate


18.0.5.9 ----> 18.0.6.0(29-Mar-2025) ***$@g@r***
====================================================
quantity updation if UOM changes while confirming BOE

18.0.6.0 ----> 18.0.6.1 ----> 18.0.6.2(30-Mar-2025) ***Anke***
===============================================================
Replace depends purchase_base_18 to purchase_down_payment

18.0.6.4 ----> 18.0.6.5 (20-Aug-2025) ***Anke***
=====================================================
Added Order Qty Exceeds validation in Separate Button

18.0.6.5 ----> 18.0.6.6 (21-Aug-2025) ***Anke***
================================================
Bug Fix(AttributeError: 'boe.template.line' object has no attribute 'product_id'. Did you mean: 'y_product_id'?)


18.0.6.6 ----> 18.0.6.7 (24-SEP-2025) ***Anke***
================================================
added export import dependency and adde code in onchange
and added onchange function to update the exchange rate in account move


================================================
### [18.0.6.8] – 2025-11-07 ***Anke***
**Change:** Updated partner form view to make “BOE Required” field visible to all users.

**Details:**
- File: "views/import_duty.xml"
- Record ID: `view_boe_required_res_partner`
- Field: `y_is_boe`
- Change: Removed `groups="base.group_no_one"` restriction.
- Impact: The field is now visible to all users instead of only hidden (group_no_one was effectively making it invisible).


18.0.6.8 ----> 18.0.6.9 (10-DEC-2025) **$@g@ar***
================================================
removed readonly for boe field

18.0.6.9 ----> 18.0.7.0 (10-DEC-2025) **$@g@ar***
================================================
added condition for invisble for reset to draft button

18.0.7.0 ----> 18.0.7.1 (18-DEC-2025) **$@g@ar***
================================================
added in process condition for reset to draft

18.0.7.1 ----> 18.0.7.2 (25-MAR-2026) **$@g@ar***
================================================
removed other chargers while reset to draft

18.0.7.2 ----> 18.0.7.3 (19-JUN-2026) **$@g@ar***
================================================
added _compute_amount_currency method to update amount in currency in journal items


18.0.7.3 ----> 18.0.7.4 (25-JUN-2026) **$@g@ar***
================================================
added depends _compute_amount_currency method to update amount in currency in journal items