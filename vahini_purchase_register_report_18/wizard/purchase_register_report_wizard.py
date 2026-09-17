from odoo import models, fields, api, _
from datetime import datetime, timedelta,date
import calendar
from xlwt import easyxf
import xlwt
import io
import base64
import datetime
import math
import pdb
import json
import xlsxwriter

def get_selection_label(self, object, field_name, field_value):
    return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])


class CustPurchaseRegisterReportWizard(models.TransientModel):
    _name = "cust.purchase.register.report.wizard"
    _description = " "
        
    y_start_date = fields.Date(string="Start Date")
    y_end_date = fields.Date(string="End Date")
    y_company_id = fields.Many2one('res.company',string="Company")
    y_move_type = fields.Selection([('in_invoice','Purchase Register Report'),('in_refund','Purchase Return Report')],default='in_invoice',string="Report")    

    
    @api.constrains('start_date','end_date')
    def _check_dates(self):
        for rec in self:
            if rec.y_end_date < rec.y_start_date:
                raise ValidationError(_("""End Date Can not be less than Start Date"""))

    def get_cust_purchase_register_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        if self.y_move_type:
            report_name = "Purchase Register Report" if self.y_move_type == 'in_invoice' else "Purchase Return Report"
        else:
            report_name = "Purchase Register Report"
        worksheet = workbook.add_worksheet(report_name)
        worksheet.freeze_panes(2,4)
        worksheet.set_column('A:C', 15)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:AR', 15)
        column_heading_style = workbook.add_format({'bold': True,
            'font_color': 'black',
            'bg_color': 'deebf7',
            'font_name':'Arial',
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter'
        })
        main_heading_style = workbook.add_format({'bold': True,
            'font_color': 'black',
            'font_name':'Arial',
            'font_size': 15,
            'align': 'center',
            'valign': 'vcenter'
        })
        left_alignment = workbook.add_format({
            'font_color': 'black',
            'font_name':'Arial',
            'font_size': 10,
            'border':1,
            'border_color':'black',
            'align': 'left',
            'valign': 'vcenter'
        })
        center_alignment = workbook.add_format({
            'font_color': 'black',
            'font_name':'Arial',
            'font_size': 10,
            'border':1,
            'border_color':'black',
            'align': 'center',
            'valign': 'vcenter'
        })

        right_alignment = workbook.add_format({
            'font_color': 'black',
            'font_size': 10,
            'font_name':'Arial',
            'border':1,
            'border_color':'black',
            'align': 'right',
            'valign': 'vcenter'
        })

        date_style = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy','font_size': 10,'font_name':'Arial','align': 'center'})
        style_number_float = workbook.add_format({'border':1,'font_color': 'black','font_name':'Arial','font_size': 10,'align':'center', 'num_format':'###0.000;-###0.000;""'})
        style_numfloat = workbook.add_format({'border':1,'font_color': 'black','font_name':'Arial','font_size': 10,'align':'center', 'num_format':'###0.00;-###0.00;""'})

        worksheet.merge_range('T1:V1', report_name,main_heading_style)
        headers = [
            "Branch",
            "Journal Name",
            "Invoice Type",
            "Bill Number",
            "Accounting Date",
            "Invoice Date",
            "Ref",
            "Partner Category",
            "GST Treatment",
            "Partner GST",
            "Partner State",
            "Partner Country",
            "Currency",
            "Currency Exchange Rate",
            "Partner Reference",
            "Vendor Name",
            "Vendor Display Name",
            "Product Category",
            "Item Group",
            "Account Name",
            "Product Group 1",
            "Product Group 2",
            "Product Group 3",
            "Product Reference",
            "Product",
            "Product Display Name",
            "HSN Code",
            "Quantity",
            "Price",
            "Discount",
            "Subtotal",
            "Taxes",
            "IGST Percent",
            "IGST amount",
            "CGST Percent",
            "CGST amount",
            "SGST Percent",
            "SGST amount",
            "TDS Percent",
            "TDS amount",
            "Total Tax",
            "Sub Total INR",
            "Total",
            "Net Total INR",
            "Gate Entry In Date",
            "Gate Entry No",
            "PO NUM",
            "Stock Move Ref",
            "Analytical Plan",
            "Analytic Account",
        ]

        row = 1
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, column_heading_style)


        row +=1
        domain = [('state','=','posted'),
                  ('date','>=',self.y_start_date),
                  ('date','<=',self.y_end_date)]
        if self.y_move_type:
            domain += [('move_type','=',self.y_move_type)]
        else:
            domain += [('move_type','in',('in_invoice','in_refund'))]

        company_ids = self.env['res.company']
        if not self.sudo().y_company_id.child_ids:
            domain+=[('company_id','=',self.y_company_id.id)]
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id)
            if len(access_company_ids) == 1:
                domain+=[('company_id','=',access_company_ids[0].id)]
            else:
                domain+=[('company_id','in',access_company_ids.ids)]

        invoice_ids = self.env['account.move'].search(domain)
        for invoice in invoice_ids:
            for line in invoice.invoice_line_ids.filtered(lambda x:x.product_id or x.account_id):
                worksheet.write(row, 0, invoice.company_id.name ,left_alignment)
                worksheet.write(row, 1, line.journal_id.name ,left_alignment)

                move_type = get_selection_label(self,'account.move','move_type',line.move_type)        
                
                worksheet.write(row, 2, move_type ,left_alignment)
                worksheet.write(row, 3, invoice.name ,left_alignment)
                worksheet.write(row, 4, invoice.date ,date_style)
                worksheet.write(row, 5, line.invoice_date ,date_style)
                worksheet.write(row, 6, invoice.ref or '' ,left_alignment)
                worksheet.write(row, 7, invoice.y_partner_category_id.y_name or '' ,left_alignment)

                partner_id = line.partner_id if line.partner_id else invoice.partner_id
                if partner_id.l10n_in_gst_treatment:
                    gst_treatment = get_selection_label(self,'res.partner','l10n_in_gst_treatment',partner_id.l10n_in_gst_treatment)
                else:
                    gst_treatment = ''
                worksheet.write(row, 8, gst_treatment ,left_alignment)
                worksheet.write(row, 9, partner_id.vat or '' ,left_alignment)
                worksheet.write(row, 10, partner_id.state_id.name or '' ,left_alignment)
                worksheet.write(row, 11, partner_id.country_id.name or '' ,left_alignment)
                worksheet.write(row, 12, invoice.currency_id.name or '' ,left_alignment)
                rate = 1/line.currency_rate
                worksheet.write(row, 13, rate ,center_alignment)
                worksheet.write(row, 14, partner_id.ref or '' ,left_alignment)
                worksheet.write(row, 15, partner_id.name  or '',left_alignment)
                if partner_id.ref:
                    partner_dispaly_name = "[{}] {}".format(partner_id.ref,partner_id.name)
                else:
                    partner_dispaly_name = partner_id.name
                worksheet.write(row, 16, partner_dispaly_name or '',left_alignment)
                worksheet.write(row, 17, line.product_category_id.name or '',left_alignment)
                worksheet.write(row, 18, line.y_category_id.y_name or '' ,left_alignment)
                worksheet.write(row, 19, line.account_id.display_name or '' ,left_alignment)
                worksheet.write(row, 20, line.product_id.product_tmpl_id.y_product_group_1.y_name or '' ,left_alignment)
                worksheet.write(row, 21, line.product_id.product_tmpl_id.y_product_group_2.y_name or '' ,left_alignment)
                worksheet.write(row, 22, line.product_id.product_tmpl_id.y_product_group_3.y_name or '' ,left_alignment)
                worksheet.write(row, 23, line.product_id.default_code or '' ,left_alignment)
                worksheet.write(row, 24, line.product_id.name or '' ,left_alignment)
                worksheet.write(row, 25, line.product_id.display_name or '' ,left_alignment)
                worksheet.write(row, 26, line.product_id.l10n_in_hsn_code or '' ,center_alignment)
                worksheet.write(row, 27, line.quantity ,center_alignment)
                worksheet.write(row, 28, line.price_unit ,style_number_float)
                worksheet.write(row, 29, line.discount ,center_alignment)
                worksheet.write(row, 30, line.price_subtotal ,center_alignment)
                tmp_name = ''
                if line.tax_ids:
                    tmp_name = ",".join(line.tax_ids.mapped('name'))
                worksheet.write(row, 31, tmp_name or '',left_alignment)
                cgst_percent = 0.0
                sgst_percent = 0.0
                igst_percent = 0.0
                tds_percent = 0.0
                igst_amount = 0.0
                cgst_amount = 0.0
                sgst_amount = 0.0
                tds_amount = 0.0
                tax_dict = line.sudo()._get_tax_line_group_values()
                if tax_dict:
                    igst_percent = tax_dict.get('IGST_RATE') if tax_dict.get('IGST') > 0 else 0 or 0
                    cgst_percent = tax_dict.get('CGST_RATE') if tax_dict.get('CGST') > 0 else 0 or 0
                    sgst_percent = tax_dict.get('SGST_RATE') if tax_dict.get('SGST') > 0 else 0 or 0
                    tds_percent = tax_dict.get('TDS_RATE') or 0
                    igst_amount = tax_dict.get('IGST') if tax_dict.get('IGST') > 0 else 0 or 0
                    cgst_amount = tax_dict.get('CGST') if tax_dict.get('CGST') > 0 else 0 or 0
                    sgst_amount = tax_dict.get('SGST') if tax_dict.get('SGST') > 0 else 0 or 0
                    tds_amount = tax_dict.get('TDS') or 0
                worksheet.write(row, 32, igst_percent ,center_alignment)
                worksheet.write(row, 33, igst_amount ,style_number_float)
                worksheet.write(row, 34, cgst_percent ,center_alignment)
                worksheet.write(row, 35, cgst_amount ,style_number_float)
                worksheet.write(row, 36, sgst_percent ,center_alignment)
                worksheet.write(row, 37, sgst_amount ,style_number_float)
                worksheet.write(row, 38, tds_percent ,center_alignment)
                worksheet.write(row, 39, tds_amount ,style_numfloat)
                tot_tax_amount = igst_amount + cgst_amount + sgst_amount
                worksheet.write(row, 40, tot_tax_amount ,style_number_float)
                sub_total_inr = 0
                if invoice.currency_id.name == "INR":
                    sub_total_inr = line.price_subtotal
                else:
                    sub_total_inr = rate * line.price_subtotal

                worksheet.write(row, 41, sub_total_inr ,style_number_float)
                worksheet.write(row, 42, tot_tax_amount + line.price_subtotal ,style_number_float)
                worksheet.write(row, 43, line.debit ,center_alignment)
                gate_entry_date = ''
                gate_entry_no = ''
                if line.y_stock_move_id.picking_id.y_stock_gate_management_ids:
                    gate_entry_date = line.y_stock_move_id.picking_id.y_stock_gate_management_ids[-1].y_post_datetime
                    gate_entry_no = ",".join(line.y_stock_move_id.picking_id.y_stock_gate_management_ids.mapped('y_name'))
                worksheet.write(row, 44, gate_entry_date  or '',date_style)
                worksheet.write(row, 45, gate_entry_no  or '',left_alignment)
                worksheet.write(row, 46, line.purchase_line_id.order_id.name  or '',left_alignment)
                worksheet.write(row, 47, line.y_stock_move_id.picking_id.name  or '',left_alignment)
                analytic_accounts = ''
                analytic_plans = ''
                if line.analytic_distribution:
                    analytic_ids = []
                    for analytic_keys in line.analytic_distribution.keys():
                        for analytic_key in analytic_keys.split(','):
                            int_analytic_key = int(analytic_key)
                            analytic_account_obj = line.env['account.analytic.account'].browse(int_analytic_key)
                            if analytic_account_obj.active:
                                analytic_ids.append(analytic_account_obj)
                    if analytic_ids:
                        analytic_accounts = ",".join([analytic.name for analytic in analytic_ids])
                        analytic_plans = ",".join([analytic.plan_id.name for analytic in analytic_ids])

                worksheet.write(row, 48, analytic_plans  or '',left_alignment)
                worksheet.write(row, 49, analytic_accounts  or '',left_alignment)
                row +=1
        
        workbook.close()
        output.seek(0)
        file_name = "{}.xlsx".format(report_name)
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': file_name,
            'res_model': self._name,
            'res_id': self.id,
        })
        # Return the action to download the report
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}'.format(attachment_id.id),
            'target': 'self',
        }