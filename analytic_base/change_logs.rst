18.0.0.1 (31-03-2025) **$@g@r
==================================================================
created new app

18.0.0.1 ----> 18.0.0.2 (04-04-2025) ***Anke***
===============================================
_get_inventory_move_values() Funtion kw updated

18.0.0.3 ----> 18.0.0.4 (05-04-2025) ***$@g@r***
===============================================
added sale line id condition for flow analytic distribution

18.0.0.7 ----> 18.0.0.8 (14-06-2025) ***Anke***
===============================================
Bug fix()
File "/home/odoo/src/user/analytic_base/models/account_move_line.py", line 36, in _prepare_exchange_difference_move_vals
line_dict['analytic_distribution'] = self.analytic_distribution
ValueError: Expected singleton: account.move.line(79116, 79114, 79118)

18.0.0.8 ----> 18.0.0.9 (22-09-2025) ***Anke***
===============================================
Bug Fix(Analytic Account Updating Mismatch)

18.0.0.9 ----> 18.0.1.0(04/Nov/2025) ***Anke***
===============================================
Corrected Mandetory

============================================
[FIX] Added Company

## [18.0.1.1] - 2025-11-22 ***Anke***

#### 🔹 Changes
Added Company field in stock.inventory.adjustment.name table