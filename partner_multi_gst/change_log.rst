18.0.0.1(23-Oct-2024) ***Anke and $@g@r***
================================================
CREATED New app

18.0.0.1----------->18.0.0.2(23-Oct-2024) ***$@g@r***
================================================
overiding standard method to get name concatinate with GST number and remove parent in customer dropdown with it is child contact

18.0.0.2 ----> 18.0.0.3(17-Jan-2025) ***Anke***
=======================================================
Removed GST number and added Reference for Display name 

18.0.0.3 ----> 18.0.0.4(21-Jan-2025) ***Anke***
=======================================================
Added commercial_partner_id to partner_id

18.0.0.4 ----> 18.0.0.5(15-Apr-2025) ***Anke***
=======================================================
GST Return Access Issue

18.0.0.5 ----> 18.0.0.6(06-Jun-2025) ***Anke***
=======================================================
GST Return Access Issue Removed

18.0.0.6 ----> 18.0.0.7(03-Jul-2026) ***muhammed-shameer***
=======================================================

RPC_ERROR

Odoo Server Error

Occured on localhost:8018 on model l10n_in.gst.return.period on 2026-07-02 13:31:09 GMT

Traceback (most recent call last):
  File "/odoo/odoo-18.0/odoo/http.py", line 2167, in _transactioning
    return service_model.retrying(func, env=self.env)
  File "/odoo/odoo-18.0/odoo/service/model.py", line 157, in retrying
    result = func()
  File "/odoo/odoo-18.0/odoo/http.py", line 2134, in _serve_ir_http
    response = self.dispatcher.dispatch(rule.endpoint, args)
  File "/odoo/odoo-18.0/odoo/http.py", line 2382, in dispatch
    result = self.request.registry['ir.http']._dispatch(endpoint)
  File "/odoo/odoo-18.0/odoo/addons/base/models/ir_http.py", line 333, in _dispatch
    result = endpoint(**request.params)
  File "/odoo/odoo-18.0/odoo/http.py", line 754, in route_wrapper
    result = endpoint(self, *args, **params_ok)
  File "/odoo/odoo-18.0/addons/web/controllers/dataset.py", line 42, in call_button
    action = call_kw(request.env[model], method, args, kwargs)
  File "/odoo/odoo-18.0/odoo/api.py", line 535, in call_kw
    result = getattr(recs, name)(*args, **kwargs)
  File "/odoo/enterprise-18.0/l10n_in_reports_gstr_spreadsheet/models/gst_return_period.py", line 50, in generate_gstr1_spreadsheet
    gstr1_json = self._get_gstr1_json()
  File "/odoo/odoo-18/Avonplast/avonplast-1-main/partner_multi_gst/models/partner_gst.py", line 714, in _get_gstr1_json
    {'data': [{**hsn_dict, 'num': index,
  File "/odoo/odoo-18/Avonplast/avonplast-1-main/partner_multi_gst/models/partner_gst.py", line 715, in <listcomp>
    'txval': AccountEdiFormat._l10n_in_round_value(hsn_dict.get('txval')),
  File "/odoo/odoo-18.0/addons/l10n_in_edi/models/account_edi_format.py", line 331, in _l10n_in_round_value
    value = round(amount, precision_digits)
TypeError: type NoneType doesn't define __round__ method

The above server error caused the following client error:
RPC_ERROR: Odoo Server Error
    RPC_ERROR
        at makeErrorFromResponse (http://localhost:8018/web/assets/07f649a/web.assets_web.min.js:3165:165)
        at XMLHttpRequest.<anonymous> (http://localhost:8018/web/assets/07f649a/web.assets_web.min.js:3171:13)

_get_gstr1_json changed in new patch of odoo 18 and when generating time this error occurred


18.0.0.7 ----> 18.0.0.8(14-Aug-2026) ***muhammed-shameer***
=======================================================
delivery address GST editable

18.0.0.8 ----> 18.0.0.9(15-Aug-2026) ***muhammed-shameer***
=======================================================
- Fixed delivery address VAT synchronization