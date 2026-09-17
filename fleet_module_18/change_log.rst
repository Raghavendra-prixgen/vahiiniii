17.0.2.1 ----> 18.0.0.1(25-Oct-2024) ***Anke***
===============================================
Conversion



18.0.0.4 ----> 18.0.0.5(21-NOV-2024) ***$@g@r***
===============================================
added driver number


18.0.0.5 ----> 18.0.0.6(21-NOV-2024) ***$@g@r***
===============================================
added company field in freight master

18.0.0.6 ----> 18.0.0.7(22-Nov-2024) ***Anke***
===============================================
Updated indents

18.0.0.9 ----> 18.0.1.0 ----> 18.0.1.1(28-Nov-2024) ***Anke***
==============================================================
Added Non Contract Transporter

18.0.1.1 ----> 18.0.1.2 (28-Nov-2024) ***Anke***
==============================================================
Updated Changed the condition for Indent duplicate validation

18.0.1.2 ----> 18.0.1.3 (10-Dec-2024) ***Anke***
================================================
Moved Transportation Order in other info

18.0.1.3 ----> 18.0.1.4 ----> 18.0.1.5 ----> 18.0.1.6(18-Dec-2024) ***Anke***
================================================================================
bugs fix:
--------
1.Non contract- Only for the approved persons its allowing to create transport Order it should allow to create even for the person without approval access
2.Sub Total is need in TO
3. When creating a Purchase Order through TO cost is updating wrongly
4.Mutiple company should not allow to create indent.
5.Dates issue(planned date and end date, Actual start date , Actual end date)
6.Need a field Via in TO
7. TO and vehicle indent should not be visible to other legal entity.

18.0.1.6 ----> 18.0.1.7 (19-Dec-2024) ***Anke***
================================================
Added Currency in FREIGHT Cost Line
Shipping Type => update Air
Updated Weight Bug

18.0.1.7 ----> 18.0.1.8 (24-Dec-2024) ***Anke***
================================================
Updated buttons in Non Contract Order Tree View

18.0.1.8 ----> 18.0.1.9 (26-Dec-2024) ***Anke***
================================================
Updated Record Rule and added domain

18.0.1.9 ----> 18.0.2.0 (27-Dec-2024) ***$@g@r***
================================================
added vehicle type in picking screen and validation while creating vehicle indent

18.0.2.0 ----> 18.0.2.1 (27-Dec-2024) ***Anke***
================================================
Added Attributes for Transport field in Picking

18.0.2.1 ----> 18.0.2.2 (30-Dec-2024) ***Anke***
================================================
Changed Transpotaion Setting company dependent

18.0.2.2 ----> 18.0.2.3 (09-JAN-2024) ***$@g@r***
================================================
added vehicle number in picking screen

18.0.2.3 ----> 18.0.2.4 (09-JAN-2024) ***Anke***
================================================
Removed Default company 

18.0.2.4 ----> 18.0.2.5(16-Jan-2025) ***Anke****
================================================
String Updated Request for Approval

18.0.2.5 ----> 18.0.2.6(24-MAR-2025) ***$@g@r****
================================================
updated field to kanban view

18.0.2.6 ----> 18.0.2.7(01-APR-2025) ***$@g@r****
================================================
added billing status in TO

18.0.2.7 ----> 18.0.2.8(04-APR-2025) ***Anke****
================================================
Updated domains

18.0.2.9 ----> 18.0.3.0(12-May-2025) ***Anke****
================================================
Added Condition in Picking (Vehicle Type)


18.0.3.0 ----> 18.0.3.1(02-JUN-2025) ***$@g@r****
================================================
 Vehicle Indent
1. In list view, add
a. Sale Order Number
b. Customer Name

> Transportation Order
1. Non-Contract - Approval with reason
2. Transportation order list view
a. Sales Order number
b. Customer Name
c. LR Number
d. Creation Date
4. The Transportation Order should not be moved to 'In-transit' if the Picking is in a ready state in the case of Dispatch.

18.0.3.1 ----> 18.0.3.2(09-JUN-2025) ***$@g@r****
================================================
added copy false for picking when backorder is created value should be empty

18.0.3.2 ----> 18.0.3.4(25-Jun-2025) ***Anke****
================================================
Added y_other_weight field 

18.0.3.4 ----> 18.0.3.5(30-Jun-2025) ***Anke****
================================================
Added Function for flexiblity

18.0.3.5 ----> 18.0.3.6(30-Jun-2025) ***Anke****
================================================
Bug Fix(POD Mandatory)