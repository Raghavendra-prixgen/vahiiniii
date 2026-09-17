from datetime import datetime, timedelta,date
import pytz
import re

import json
import markupsafe

from babel.dates import get_quarter_names
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from itertools import groupby
from markupsafe import Markup

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning
from odoo.tools import date_utils, get_lang, html_escape, SQL
from odoo.tools.misc import format_date
import io
from datetime import datetime

from odoo import Command, fields, models
from odoo.tools.misc import xlsxwriter

import logging

_logger = logging.getLogger(__name__)
TOLERANCE_AMOUNT = 1.0  # Default fallback tolerance amount for GSTR-2B matching if the system parameter is unset.


    
class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'


    #restrict vat to flow from parent to child in case of type invoice
    @api.model
    def _commercial_fields(self):
        res = super()._commercial_fields()

        if self.type == 'invoice':
            res.remove('vat')
        elif self.type == 'delivery' and self.vat and 'vat' in res:
            res.remove('vat')
        return res + ['ref']


    #standard method
    def _get_complete_name(self):
        self.ensure_one()

        displayed_types = self._complete_name_displayed_types
        type_description = dict(self._fields['type']._description_selection(self.env))

        name = self.name or ''
        if self.company_name :
            if not name and self.type in displayed_types:
                name = type_description[self.type]
            if not self.is_company:
                name = f"{self.commercial_company_name }, {name}"
        #added ref condition
        if self.ref:
            name = f"{name} ‒ {self.ref}"
        return name.strip()

    #standard method
    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name','ref')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            name = partner.with_context(lang=self.env.lang)._get_complete_name()
            if partner._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = re.sub(r'\s+\n', '\n', name)
            if partner._context.get('partner_show_db_id'):
                name = f"{name} ({partner.id})"
            if partner._context.get('address_inline'):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get('show_email') and partner.email:
                name = f"{name} <{partner.email}>"

            #removed vat addition in lst paragraph
            # if partner._context.get('show_vat') and partner.vat:
            #     name = f"{name} ‒ {partner.vat}"


            partner.display_name = name.strip()




class L10nInGSTReturnPeriod(models.Model):
    _inherit = "l10n_in.gst.return.period"

    # def generate_gstr1_spreadsheet(self):
    #     gstr1_json = self._get_gstr1_json()
    #     if self.gstr1_spreadsheet:
    #         # archive the old file
    #         self.gstr1_spreadsheet.active = False
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     cell_formats = self._get_gstr1_cell_formats(workbook)
    #     self._prepare_b2b_sheet(gstr1_json.get('b2b', {}), workbook, cell_formats)
    #     self._prepare_b2cl_sheet(gstr1_json.get('b2cl', {}), workbook, cell_formats)
    #     self._prepare_b2cs_sheet(gstr1_json.get('b2cs', {}), workbook, cell_formats)
    #     self._prepare_cdnr_sheet(gstr1_json.get('cdnr', {}), workbook, cell_formats)
    #     self._prepare_cdnur_sheet(gstr1_json.get('cdnur', {}), workbook, cell_formats)
    #     self._prepare_exp_sheet(gstr1_json.get('exp', {}), workbook, cell_formats)
    #     self._prepare_nil_sheet(gstr1_json.get('nil', {}), workbook, cell_formats)
    #     self._prepare_hsn_sheet(gstr1_json.get('hsn', {}), workbook, cell_formats)
    #     # self._prepare_supeco_sheet(gstr1_json.get('supeco', {}), 'clttx', workbook, cell_formats) # Table 14(a) u/s 52(TCS)
    #     # self._prepare_supeco_sheet(gstr1_json.get('supeco', {}), 'paytx', workbook, cell_formats) # Table 14 (b) u/s 9(5)
    #     workbook.close()
    #     xlsx_data = output.getvalue()
    #     xlsx_doc = self.env['documents.document'].create({
    #         'name': 'gstr1_%s_monthly_report.xlsx' % self.return_period_month_year,
    #         'raw': xlsx_data,
    #         'folder_id': self._get_gstr_document_folder().id,
    #         'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #         'access_ids': [Command.create({'partner_id': partner.id, 'role': 'edit'})
    #                            for partner in self.env.ref('account.group_account_manager').users.partner_id]
    #     })
    #     self.gstr1_spreadsheet = xlsx_doc.clone_xlsx_into_spreadsheet(archive_source=True)
    #     return self.action_open_gstr1_spreadsheet()

    
    def _get_gstr1_json(self):
        def _group_aml(group_by_field, journal_items):
            values = {}
            journal_items = journal_items.sorted(lambda l: l.mapped(group_by_field))
            for groupby_key, grouped_items in groupby(journal_items, lambda l: l.mapped(group_by_field)):
                values.setdefault(groupby_key, AccountMoveLine)
                for grouped_item in grouped_items:
                    values[groupby_key] += grouped_item
            return values

        def is_einvoice_skippable(move_id):
            # Check if the skip e-invoice condition is met for a given move_id.
            return (
                not self.gstr1_include_einvoice and
                any(
                    doc.edi_format_id.code == 'in_einvoice_1_03' and doc.state in ['sent', 'cancelled']
                    for doc in move_id.edi_document_ids
                )
            )

        def _process_hsn_data(hsn_data):
            """Helper function to process HSN data with rounding."""
            return [
                {**hsn_dict, 'num': index, **{
                    key: AccountEdiFormat._l10n_in_round_value(hsn_dict.get(key, 0))
                    for key in ('txval', 'iamt', 'camt', 'samt', 'csamt', 'qty')
                }}
                for index, hsn_dict in enumerate(hsn_data.values(), start=1)
            ]

        def _get_b2b_json(journal_items):
            """
            This method is return b2b json as below
            Here itms is group by of invoice line per gst tax rate
            [{
                'ctin': '24AACCT6304M1ZB',
                'inv': [{
                    'inum': 'INV/2022/00005',
                    'idt': '01-04-2022',
                    'val': 100.00,
                    'pos': '24',
                    'rchrg': 'N',
                    'inv_typ': 'R',
                    'etin': "34AACCT6304M1ZB",
                    'diff_percent': 0.65,
                    'itms': [{
                        'num': 1,
                        'itm_det': {
                          'rt': 28.0,
                          'txval': 100.0,
                          'iamt': 0.0,
                          'samt': 9.0,
                          'camt': 9.0,
                          'csamt': 6.5
                        }
                    }]
                }]
            }]
            """
            b2b_json = []
            for partner, journal_items in _group_aml('move_id.partner_id', journal_items).items():
                inv_json_list = []
                for move_id in journal_items.mapped('move_id'):
                    if is_einvoice_skippable(move_id):
                        continue
                    lines_json = {}
                    is_reverse_charge = False
                    is_igst_amount = False
                    tax_details = tax_details_by_move.get(move_id)
                    for line_tax_details in tax_details.values():
                        # Ignore the lines if invoice is not SEZ and GST taxes are not selected
                        if move_id.l10n_in_gst_treatment != 'special_economic_zone' and not line_tax_details['gst_tax_rate']:
                            continue
                        tax_rate = line_tax_details['gst_tax_rate']
                        if line_tax_details['l10n_in_reverse_charge']:
                            is_reverse_charge = True
                        lines_json.setdefault(tax_rate, {
                            "rt": tax_rate, "txval": 0.00, "iamt": 0.00, "samt": 0.00, "camt": 0.00, "csamt": 0.00})
                        if line_tax_details['igst']:
                            is_igst_amount = True
                        lines_json[tax_rate]['txval'] += line_tax_details['base_amount'] * -1
                        lines_json[tax_rate]['iamt'] += line_tax_details['igst'] * -1
                        lines_json[tax_rate]['camt'] += line_tax_details['cgst'] * -1
                        lines_json[tax_rate]['samt'] += line_tax_details['sgst'] * -1
                        lines_json[tax_rate]['csamt'] += line_tax_details['cess'] * -1
                    if lines_json:
                        invoice_type = 'R'
                        if move_id.l10n_in_gst_treatment == 'deemed_export':
                            invoice_type = 'DE'
                        elif move_id.l10n_in_gst_treatment == "special_economic_zone" and is_igst_amount:
                            invoice_type = 'SEWP'
                        elif move_id.l10n_in_gst_treatment == "special_economic_zone":
                            invoice_type = 'SEWOP'
                        inv_json = {
                            "inum": move_id.name,
                            "idt": move_id.invoice_date.strftime("%d-%m-%Y"),
                            "val": AccountEdiFormat._l10n_in_round_value(move_id.amount_total_signed),
                            "pos": move_id.l10n_in_state_id.l10n_in_tin,
                            "rchrg": is_reverse_charge and "Y" or "N",
                            "inv_typ": invoice_type,
                            #"etin": move_id.l10n_in_reseller_partner_id.vat or "",
                            "itms": [
                                {"num": index, "itm_det": {
                                    'txval': AccountEdiFormat._l10n_in_round_value(line_json.pop('txval')),
                                    'iamt': AccountEdiFormat._l10n_in_round_value(line_json.pop('iamt')),
                                    'camt': AccountEdiFormat._l10n_in_round_value(line_json.pop('camt')),
                                    'samt': AccountEdiFormat._l10n_in_round_value(line_json.pop('samt')),
                                    'csamt': AccountEdiFormat._l10n_in_round_value(line_json.pop('csamt')), **line_json}}
                                for index, line_json in enumerate(lines_json.values(), start=1)
                            ],
                        }
                        inv_json_list.append(inv_json)
                if inv_json_list:
                    b2b_json.append({'ctin': partner.vat, 'inv': inv_json_list})
            return b2b_json

        def _get_b2cl_json(journal_items):
            """
            This method is return b2cl json as below
            Here itms is group by of invoice line per gst tax rate
            [{
                'pos': '30',
                'inv': [{
                    'inum': 'INV/2022/00005',
                    'idt': '01-04-2022',
                    'val': 100.00,
                    'diff_percent': 0.65,
                    'itms': [{
                        'num': 1,
                        'itm_det': {
                          'rt': 28.0,
                          'txval': 100.0,
                          'iamt': 0.0,
                          'csamt': 6.5
                        }
                    }]
                }]
            }]
            """
            b2cl_json = []
            for state_id, journal_items in _group_aml('move_id.l10n_in_state_id', journal_items).items():
                inv_json_list = []
                for move_id in journal_items.mapped('move_id'):
                    lines_json = {}
                    tax_details = tax_details_by_move.get(move_id)
                    for line_tax_details in tax_details.values():
                        if move_id.l10n_in_gst_treatment != 'special_economic_zone' and not line_tax_details['gst_tax_rate']:
                            continue
                        tax_rate = line_tax_details.get('gst_tax_rate')
                        lines_json.setdefault(tax_rate, {
                            "rt": tax_rate, "txval": 0.00, "iamt": 0.00, "csamt": 0.00})
                        lines_json[tax_rate]['txval'] += line_tax_details['base_amount'] * -1
                        lines_json[tax_rate]['iamt'] += line_tax_details['igst'] * -1
                        lines_json[tax_rate]['csamt'] += line_tax_details['cess'] * -1
                    if lines_json:
                        inv_json = {
                            "inum": move_id.name,
                            "idt": move_id.invoice_date.strftime("%d-%m-%Y"),
                            "val": AccountEdiFormat._l10n_in_round_value(move_id.amount_total_signed),
                            #"etin": move_id.l10n_in_reseller_partner_id.vat or "",
                            "itms": [
                                {"num": index, "itm_det": {
                                    'txval': AccountEdiFormat._l10n_in_round_value(line_json.pop('txval')),
                                    'iamt': AccountEdiFormat._l10n_in_round_value(line_json.pop('iamt')),
                                    'csamt': AccountEdiFormat._l10n_in_round_value(line_json.pop('csamt')), **line_json}}
                                for index, line_json in enumerate(lines_json.values(), start=1)
                            ],
                        }
                        inv_json_list.append(inv_json)
                b2cl_json.append({'pos': state_id.l10n_in_tin, 'inv': inv_json_list})
            return b2cl_json

        def _get_b2cs_json(journal_items):
            """
            This method is return b2cs json as below
            Here data is group by gst tax rate and place of supply
            [{
              'sply_ty': 'INTRA',
              'pos': '36',
              'typ': 'OE',
              'rt': 5.0,
              'txval': 100,
              'iamt': 0.0,
              'samt': 2.50,
              'camt': 2.50,
              'csamt': 0.0
            }]
            """
            b2cs_json = {}
            for move_id in journal_items.mapped('move_id'):
                # We sum value of invoice and credit note
                # so we need positive value for invoice and nagative for credit note
                tax_details = tax_details_by_move.get(move_id)
                for line_tax_details in tax_details.values():
                    if move_id.l10n_in_gst_treatment != 'special_economic_zone' and not line_tax_details['gst_tax_rate']:
                        continue
                    tax_rate = line_tax_details.get('gst_tax_rate')
                    group_key = "%s-%s"%(tax_rate, move_id.l10n_in_state_id.l10n_in_tin)
                    b2cs_json.setdefault(group_key, {
                        "sply_ty": move_id.l10n_in_state_id == move_id.company_id.state_id and "INTRA" or "INTER",
                        "pos": move_id.l10n_in_state_id.l10n_in_tin,
                        "typ": "OE",
                        "rt": tax_rate,
                        "txval": 0.00, "iamt": 0.00, "samt": 0.00, "camt": 0.00, "csamt": 0.00})
                    b2cs_json[group_key]['txval'] += line_tax_details['base_amount'] * -1
                    b2cs_json[group_key]['iamt'] += line_tax_details['igst'] * -1
                    b2cs_json[group_key]['camt'] += line_tax_details['cgst'] * -1
                    b2cs_json[group_key]['samt'] += line_tax_details['sgst'] * -1
                    b2cs_json[group_key]['csamt'] += line_tax_details['cess'] * -1
            return list({
                **d,
                "txval": AccountEdiFormat._l10n_in_round_value(d['txval']),
                "iamt": AccountEdiFormat._l10n_in_round_value(d['iamt']),
                "samt": AccountEdiFormat._l10n_in_round_value(d['samt']),
                "camt": AccountEdiFormat._l10n_in_round_value(d['camt']),
                "csamt": AccountEdiFormat._l10n_in_round_value(d['csamt']),
            } for d in b2cs_json.values())

        def _get_cdnr_json(journal_items):
            """
            This method is return cdnr json as below
            Here itms is group by of invoice line per gst tax rate
            [{
                'ctin': '24AACCT6304M1ZB',
                'nt': [{
                    'ntty': 'C',
                    'nt_num': 'RINV/2022/00001',
                    'nt_dt': '02-04-2022',
                    'val': 105296.77,
                    'pos': '24',
                    'rchrg': 'N',
                    'inv_typ': 'R',
                    'diff_percent': 0.65,
                    'itms': [{
                        'num': 1,
                        'itm_det': {
                          'rt': 28.0,
                          'txval': 80000.0,
                          'iamt': 0.0,
                          'samt': 11200.0,
                          'camt': 11200.0,
                          'csamt': 0.0
                        }
                    }]
                }]
            }]
            """
            cdnr_json = []
            for partner, journal_items in _group_aml('move_id.partner_id', journal_items).items():
                inv_json_list = []
                for move_id in journal_items.mapped('move_id'):
                    if is_einvoice_skippable(move_id):
                        continue
                    lines_json = {}
                    is_igst_amount = False
                    is_reverse_charge = False
                    tax_details = tax_details_by_move[move_id]
                    for line_tax_details in tax_details.values():
                        if move_id.l10n_in_gst_treatment != 'special_economic_zone' and not line_tax_details['gst_tax_rate']:
                            continue
                        tax_rate = line_tax_details['gst_tax_rate']
                        if line_tax_details['l10n_in_reverse_charge']:
                            is_reverse_charge = True
                        if line_tax_details['igst']:
                            is_igst_amount = True
                        lines_json.setdefault(tax_rate, {
                            "rt": tax_rate, "txval": 0.00, "iamt": 0.00, "samt": 0.00, "camt": 0.00, "csamt": 0.00})
                        lines_json[tax_rate]['txval'] += line_tax_details['base_amount']
                        lines_json[tax_rate]['iamt'] += line_tax_details['igst']
                        lines_json[tax_rate]['samt'] += line_tax_details['cgst']
                        lines_json[tax_rate]['camt'] += line_tax_details['sgst']
                        lines_json[tax_rate]['csamt'] += line_tax_details['cess']
                    if lines_json:
                        invoice_type = 'R'
                        if move_id.l10n_in_gst_treatment == 'deemed_export':
                            invoice_type = 'DE'
                        elif move_id.l10n_in_gst_treatment == "special_economic_zone" and is_igst_amount:
                            invoice_type = 'SEWP'
                        elif move_id.l10n_in_gst_treatment == "special_economic_zone":
                            invoice_type = 'SEWOP'
                        is_out_refund = move_id.move_type == "out_refund"
                        sign = is_out_refund and 1 or -1
                        inv_json = {
                            "ntty": is_out_refund and "C" or "D",
                            "nt_num": move_id.name,
                            "nt_dt": move_id.invoice_date.strftime("%d-%m-%Y"),
                            "val": AccountEdiFormat._l10n_in_round_value(move_id.amount_total_signed * -sign),
                            "pos": move_id.l10n_in_state_id.l10n_in_tin,
                            "rchrg": is_reverse_charge and "Y" or "N",
                            "inv_typ": invoice_type,
                            "itms": [
                                {"num": index, "itm_det": {
                                    **line_json,
                                    "txval": AccountEdiFormat._l10n_in_round_value(line_json['txval'] * sign),
                                    "iamt": AccountEdiFormat._l10n_in_round_value(line_json['iamt'] * sign),
                                    "samt": AccountEdiFormat._l10n_in_round_value(line_json['samt'] * sign),
                                    "camt": AccountEdiFormat._l10n_in_round_value(line_json['camt'] * sign),
                                    "csamt": AccountEdiFormat._l10n_in_round_value(line_json['csamt'] * sign),
                                }} for index, line_json in enumerate(lines_json.values(), start=1)
                            ],
                        }
                        inv_json_list.append(inv_json)
                if inv_json_list:
                    cdnr_json.append({'ctin': partner.vat, 'nt': inv_json_list})
            return cdnr_json

        def _get_cdnur_json(journal_items):
            """
            This method is return cdnur json as below
            Here itms is group by of invoice line per gst tax rate
            [{
                'ntty': 'C',
                'nt_num': 'RINV/2022/00002',
                'nt_dt': '02-05-2022',
                'val': 212400.0,
                'pos': '30',
                'typ': 'B2CL',
                'diff_percent': 0.65,
                'itms': [{
                    'num': 1,
                    'itm_det': {
                      'rt': 18.0,
                      'txval': 180000.0,
                      'iamt': 32400.0,
                      'csamt': 0.0
                    }
                }]
            }]
            """
            inv_json_list = []
            for move_id in journal_items.mapped('move_id'):
                tax_details = tax_details_by_move.get(move_id)
                lines_json = {}
                is_igst_amount = False
                for line_tax_details in tax_details.values():
                    if move_id.l10n_in_gst_treatment != 'special_economic_zone' and not line_tax_details['gst_tax_rate']:
                        continue
                    if line_tax_details['igst']:
                        is_igst_amount = True
                    tax_rate = line_tax_details['gst_tax_rate']
                    lines_json.setdefault(tax_rate, {
                        "rt": tax_rate, "txval": 0.00, "iamt": 0.00, "csamt": 0.00})
                    lines_json[tax_rate]['txval'] += line_tax_details['base_amount']
                    lines_json[tax_rate]['iamt'] += line_tax_details['igst']
                    lines_json[tax_rate]['csamt'] += line_tax_details['cess']
                if lines_json:
                    invoice_type = 'B2CL'
                    is_out_refund = move_id.move_type == "out_refund"
                    sign = is_out_refund and 1 or -1
                    invoice_total = move_id.amount_total_signed * -sign
                    if move_id.l10n_in_gst_treatment == "overseas" and is_igst_amount:
                        invoice_type = 'EXPWP'
                        # If Base amount and Invoice total is same then add tax values in total for Export with payment only
                        if float_is_zero(invoice_total - sum(line['txval'] for line in lines_json.values()), precision_digits=2):
                            invoice_total += sum(line['iamt'] + line['csamt'] for line in lines_json.values())
                    elif move_id.l10n_in_gst_treatment == "overseas":
                        invoice_type = 'EXPWOP'
                    inv_json = {
                        "ntty": is_out_refund and "C" or "D",
                        "nt_num": move_id.name,
                        "nt_dt": move_id.invoice_date.strftime("%d-%m-%Y"),
                        "val": AccountEdiFormat._l10n_in_round_value(invoice_total),
                        "typ": invoice_type,
                        "itms": [
                            {"num": index, "itm_det": {
                                **line_json,
                                "txval": AccountEdiFormat._l10n_in_round_value(line_json['txval'] * sign),
                                "iamt": AccountEdiFormat._l10n_in_round_value(line_json['iamt'] * sign),
                                "csamt": AccountEdiFormat._l10n_in_round_value(line_json['csamt'] * sign),
                            }} for index, line_json in enumerate(lines_json.values(), start=1)
                        ],
                    }
                    if invoice_type == 'B2CL':
                        inv_json.update({"pos": move_id.l10n_in_state_id.l10n_in_tin})
                    inv_json_list.append(inv_json)
            return inv_json_list

        def _get_exp_json(journal_items):
            """
            This method is return exp json as below
            Here itms is group by of invoice line per gst tax rate
            [{
                'exp_typ': 'WPAY',
                'inv': [{
                    'inum': 'INV/2022/00008',
                    'idt': '01-04-2022',
                    'val': 283200.0,
                    'sbnum': '999704',
                    'sbdt': '02/04/2022',
                    'sbpcode': 'INIXY1',
                    'itms': [
                    {
                        'rt': 18.0,
                        'txval': 240000.0,
                        'iamt': 43200.0,
                        'csamt': 0.0
                    }]
                }]
            }]
            """
            export_json = {}
            for move_id in journal_items.mapped('move_id'):
                if is_einvoice_skippable(move_id):
                    continue
                tax_details = tax_details_by_move.get(move_id)
                lines_json = {}
                is_igst_amount = False
                for line_tax_details in tax_details.values():
                    if line_tax_details['igst']:
                        is_igst_amount = True
                    elif line_tax_details['sgst'] or line_tax_details['cgst']:
                        continue
                    tax_rate = line_tax_details['gst_tax_rate']
                    lines_json.setdefault(tax_rate, {"rt": tax_rate, "txval": 0.00, "iamt": 0.00, "csamt": 0.00})
                    lines_json[tax_rate]['txval'] += line_tax_details['base_amount'] * -1
                    lines_json[tax_rate]['iamt'] += line_tax_details['igst'] * -1
                    lines_json[tax_rate]['csamt'] += line_tax_details['cess'] * -1
                if lines_json:
                    invoice_total = move_id.amount_total_signed
                    invoice_type = 'WOPAY'
                    if is_igst_amount:
                        invoice_type = 'WPAY'
                        # If Base amount and Invoice total is same then add tax values in total for Export with payment only
                        if float_is_zero(invoice_total - sum(line['txval'] for line in lines_json.values()), precision_digits=2):
                            invoice_total += sum(line['iamt'] + line['csamt'] for line in lines_json.values())
                    export_json.setdefault(invoice_type, [])
                    export_inv = {
                        "inum": move_id.name,
                        "idt": move_id.invoice_date.strftime("%d-%m-%Y"),
                        "val": AccountEdiFormat._l10n_in_round_value(invoice_total),
                        "itms": list({
                            **d,
                            "txval": AccountEdiFormat._l10n_in_round_value(d['txval']),
                            "iamt": AccountEdiFormat._l10n_in_round_value(d['iamt']),
                            "csamt": AccountEdiFormat._l10n_in_round_value(d['csamt']),
                            }
                            for d in lines_json.values()),
                    }
                    if move_id.l10n_in_shipping_bill_number:
                        export_inv.update({"sbnum": move_id.l10n_in_shipping_bill_number})
                    if move_id.l10n_in_shipping_bill_date:
                        export_inv.update({"sbdt": move_id.l10n_in_shipping_bill_date.strftime("%d-%m-%Y")})
                    if move_id.l10n_in_shipping_port_code_id.code:
                        export_inv.update({"sbpcode": move_id.l10n_in_shipping_port_code_id.code})
                    export_json[invoice_type].append(export_inv)
            return [{"exp_typ":invoice_type, "inv": inv_json} for invoice_type, inv_json in export_json.items()]

        def _get_nil_json(journal_items):
            """
            This method is return nil json as below
            Here data is grouped by supply_type and sum of base amount of diffrent type of 0% tax
            {
                'inv':[{
                    'sply_ty': 'INTRB2B',
                    'nil_amt': 100.0,
                    'expt_amt': 200.0,
                    'ngsup_amt': 300.0,
                }]
            }
            """
            nil_json = {}
            tags_id = self._get_l10n_in_taxes_tags_id_by_name()
            for move_id in journal_items.mapped('move_id'):
                if is_einvoice_skippable(move_id):
                    continue
                # We sum value of invoice and credit note
                # so we need positive value for invoice and nagative for credit note
                tax_details = tax_details_by_move.get(move_id, {})
                same_state = move_id.l10n_in_state_id == move_id.company_id.state_id
                supply_type = ""
                if same_state:
                    if move_id.l10n_in_gst_treatment in ('special_economic_zone', 'deemed_export', 'regular'):
                        supply_type = "INTRAB2B"
                    else:
                        supply_type = "INTRAB2C"
                else:
                    if move_id.l10n_in_gst_treatment in ('special_economic_zone', 'deemed_export', 'regular'):
                        supply_type = "INTRB2B"
                    else:
                        supply_type = "INTRB2C"
                nil_json.setdefault(supply_type, {
                    "sply_ty": supply_type,
                    "nil_amt": 0.00,
                    "expt_amt": 0.00,
                    "ngsup_amt": 0.00,
                })
                for line, line_tax_detail  in tax_details.items():
                    base_line_tag_ids = line.tax_tag_ids.ids
                    if tags_id['nil_rated'] in base_line_tag_ids:
                        nil_json[supply_type]['nil_amt'] += line_tax_detail['base_amount'] * -1
                    if tags_id['exempt'] in base_line_tag_ids:
                        nil_json[supply_type]['expt_amt'] += line_tax_detail['base_amount'] * -1
                    if tags_id['non_gst_supplies'] in base_line_tag_ids:
                        nil_json[supply_type]['ngsup_amt'] += line_tax_detail['base_amount'] * -1
            return nil_json and {'inv': list({
                **d,
                "nil_amt": AccountEdiFormat._l10n_in_round_value(d['nil_amt']),
                "expt_amt": AccountEdiFormat._l10n_in_round_value(d['expt_amt']),
                "ngsup_amt": AccountEdiFormat._l10n_in_round_value(d['ngsup_amt']),
            } for d in nil_json.values())} or {}

        def _get_supeco_clttx_json(journal_items):
            """
            contains supeco details for section 52
            This method is return clttx list as below
            Here data is grouped by etin(reseller_partner_gstin) and sum of base and gst taxes (TCS 1%)
            [{
                    "etin": "20ALYPD6528PQC5",
                    "suppval": 10000,
                    "igst": 1000,
                    "cgst": 0,
                    "sgst": 0,
                    "cess": 0,
            }]
            """
            clttx_json = {}
            for move_id in journal_items.mapped('move_id'):
                tax_details = tax_details_by_move.get(move_id)
                eco_gstin = move_id.l10n_in_reseller_partner_id.vat
                for line_tax in tax_details.values():
                    clttx_json.setdefault(eco_gstin, {
                        "etin": eco_gstin,
                        "suppval": 0.00,
                        "igst": 0.00,
                        "sgst": 0.00,
                        "cgst": 0.00,
                        "cess": 0.00,
                    })
                    clttx_json[eco_gstin]['suppval'] += line_tax['base_amount'] * -1
                    clttx_json[eco_gstin]['cgst'] += line_tax['cgst'] * -1
                    clttx_json[eco_gstin]['sgst'] += line_tax['sgst'] * -1
                    clttx_json[eco_gstin]['igst'] += line_tax['igst'] * -1
                    clttx_json[eco_gstin]['cess'] += line_tax['cess'] * -1
            return [{
                **d,
                "suppval": AccountEdiFormat._l10n_in_round_value(d['suppval']),
                "igst": AccountEdiFormat._l10n_in_round_value(d['igst']),
                "cgst": AccountEdiFormat._l10n_in_round_value(d['cgst']),
                "sgst": AccountEdiFormat._l10n_in_round_value(d['sgst']),
                "cess": AccountEdiFormat._l10n_in_round_value(d['cess']),
            } for d in clttx_json.values()]

        def _get_supeco_paytx_json(journal_items):
            """
            contains supeco details for section 9(5)
            This method is return paytx list as below
            Here data is grouped by etin(reseller_partner_gstin)
            [{
                "etin": "20ALYPD6528PQC5",
                "suppval": 10000,
                "igst": 1000,
                "cgst": 0,
                "sgst": 0,
                "cess": 0,
            }]
            """
            paytx_json = {}
            for move_id in journal_items.mapped('move_id'):
                tax_details = tax_details_by_move.get(move_id)
                eco_gstin = move_id.l10n_in_reseller_partner_id.vat
                for line_tax_details in tax_details.values():
                    paytx_json.setdefault(eco_gstin, {
                        "etin": eco_gstin,
                        "suppval": 0.00,
                        "igst": 0.00,
                        "sgst": 0.00,
                        "cgst": 0.00,
                        "cess": 0.00,
                    })
                    paytx_json[eco_gstin]['suppval'] += line_tax_details['base_amount'] * -1
                    paytx_json[eco_gstin]['igst'] += line_tax_details['igst'] * -1
                    paytx_json[eco_gstin]['cgst'] += line_tax_details['cgst'] * -1
                    paytx_json[eco_gstin]['sgst'] += line_tax_details['sgst'] * -1
                    paytx_json[eco_gstin]['cess'] += line_tax_details['cess'] * -1

            return [{
                **d,
                "suppval": AccountEdiFormat._l10n_in_round_value(d['suppval']),
                "igst": AccountEdiFormat._l10n_in_round_value(d['igst']),
                "cgst": AccountEdiFormat._l10n_in_round_value(d['cgst']),
                "sgst": AccountEdiFormat._l10n_in_round_value(d['sgst']),
                "cess": AccountEdiFormat._l10n_in_round_value(d['cess']),
            } for d in paytx_json.values()]

        AccountMoveLine = self.env['account.move.line'].sudo()
        AccountEdiFormat = self.env["account.edi.format"]
        tax_details_by_move = self._get_tax_details(self._get_section_domain('hsn'))
        hsn_json = self._get_gstr1_hsn_json(AccountMoveLine.search(self._get_section_domain('hsn')), tax_details_by_move)
        nil_json = _get_nil_json(AccountMoveLine.search(self._get_section_domain('nil')))
        return_json = {
            'gstin': self.tax_unit_id.vat or self.company_id.vat,
            'fp': self.return_period_month_year,
            'b2b': _get_b2b_json(AccountMoveLine.search(self._get_section_domain('b2b'))),
            'b2cl': _get_b2cl_json(AccountMoveLine.search(self._get_section_domain('b2cl'))),
            'b2cs': _get_b2cs_json(AccountMoveLine.search(self._get_section_domain('b2cs'))),
            'cdnr': _get_cdnr_json(AccountMoveLine.search(self._get_section_domain('cdnr'))),
            'cdnur': _get_cdnur_json(AccountMoveLine.search(self._get_section_domain('cdnur'))),
            'exp': _get_exp_json(AccountMoveLine.search(self._get_section_domain('exp'))),
            'doc_issue': self._get_doc_issue_json()
            # Indian Government is not supporting supeco in the production
            # 'supeco': {
            #     'clttx': _get_supeco_clttx_json(AccountMoveLine.search(self._get_section_domain('supeco_clttx'))), # details for section 52 (TCS)
            #     'paytx': _get_supeco_paytx_json(AccountMoveLine.search(self._get_section_domain('supeco_paytx'))) #details for section 9(5)
            # }
        }
        if nil_json:
            return_json.update({'nil': nil_json})
        if hsn_json:
            return_json['hsn'] = {
                hsn_section: _process_hsn_data(hsn_json[hsn_section])
                for hsn_section in hsn_json
            }
        return return_json
