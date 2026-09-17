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


class CustSaleRegisterReportWizard(models.TransientModel):
    _name = "cust.sale.register.report.wizard"
    _description = " "
        
    y_start_date = fields.Date(string="Start Date")
    y_end_date = fields.Date(string="End Date")
    y_company_id = fields.Many2one('res.company',string="Company")
    y_move_type = fields.Selection([('out_invoice','Sale Register Report'),('out_refund','Sale Return Report')],default='out_invoice',string="Report")    

    
    @api.constrains('start_date','end_date')
    def _check_dates(self):
        for rec in self:
            if rec.y_end_date < rec.y_start_date:
                raise ValidationError(_("""End Date Can not be less than Start Date"""))

    def get_cust_sale_register_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        if self.y_move_type:
            report_name = "Sale Register Report" if self.y_move_type == 'out_invoice' else "Sale Return Report"
        else:
            report_name = "Sale Register Report"
        worksheet = workbook.add_worksheet(report_name)
        worksheet.freeze_panes(2,5)
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
        style_number_float = workbook.add_format({'border':1,'font_color': 'black','font_name':'Arial','font_size': 10,'align':'center', 'num_format':'###0.000;-###0.000;""'})
        style_num_float = workbook.add_format({'border':1,'font_color': 'black','font_name':'Arial','font_size': 10,'align':'center', 'num_format':'###0.00;-###0.00;""'})

        date_style = workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy','font_size': 10,'font_name':'Arial','align': 'center'})
        worksheet.merge_range('AH1:AJ1', report_name,main_heading_style)
        headers = [
            "Branch",
            "Accounting Date",
            "Journal Name",
            "Invoice Type",
            "Invoice Number",
            "Partner Category",
            "Sales Team",
            "Salesperson",
            "Partner Reference",
            "Customer Name",
            "Customer Display Name",
            "GST Treatment",
            "Partner GST",
            "Product Category",
            "Item Group",
            "Product Group 1",
            "Product Group 2",
            "Product Group 3",
            "Product Reference",
            "Product",
            "Product Display Name",
            "Product Weight( in 3 digits)",
            "Total Weight",
            "Quantity",
            "Product UOM",
            "HSN Code",
            "Indian GST UQC",
            "MRP",
            "Unit Price after all discounts",
            "Gross Total",
            "Trade Discount (%)",
            "Trade Discount Amount",
            "Quantity Discount (%)",
            "Quantity Disount Amount",
            "Special Discount (%)",
            "Special Discount Amount",
            "Subtotal",
            "Taxes",
            "IGST Percent",
            "IGST Amount",
            "CGST Percent",
            "CGST Amount",
            "SGST Percent",
            "SGST Amount",
            "TCS Percent",
            "TCS Amount",
            "Tax Amount",
            "Net Total",
            "Sub Total INR (EXPORT INVOICE)",
            "Net Total INR (EXPORT INVOICE)",
            "Account Group",
            "Account Type",
            "Account Name",
            "Analytic Account",
            "Analytical Plan",
            "Stock Move Ref",
            "SO Number Ref",
            "EWAYBILL NO",
            "TRANSPORTATION TYPE",
            "TRANSPORTER NAME",
            "VEHICLE INDENT NO",
            "TRANSPORTAION COST",
            "Gate Entry Out Date",
            "Gate Entry No",
            "External Vehicle Number",
            "Internal Vechile No.",
            "Driver Name",
            "Delivery Name",
            "Invoice Street 1",
            "Delivery Street 1",
            "Invoice Street 2",
            "Delivery Street 2",
            "Invoice Pincode",
            "Delivery Pincode",
            "Invoice City",
            "Delivery City",
            "Invoice District",
            "Delivery District",
            "Partner State",
            "Delivery State",
            "Partner Country",
            "Delivery Country",
            "Location",     
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
            domain += [('move_type','in',('out_invoice','out_refund'))]

        

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
                worksheet.write(row, 0, invoice.company_id.name ,left_alignment) # Branch
                worksheet.write(row, 1, invoice.date or '' ,date_style) # Accounting Date
                worksheet.write(row, 2, line.journal_id.name or '' ,left_alignment) # Journal Name
                move_type = get_selection_label(self,'account.move','move_type',line.move_type)        
                worksheet.write(row, 3, move_type ,left_alignment) # Invoice Type
                worksheet.write(row, 4, invoice.name ,left_alignment) # Invoice Number
                worksheet.write(row, 5, invoice.y_partner_category_id.y_name or '' ,left_alignment) # Partner Category
                worksheet.write(row, 6, invoice.team_id.name or '' ,left_alignment) # Sales Team
                worksheet.write(row, 7, invoice.invoice_user_id.name or '' ,left_alignment) # Salesperson
                partner_id = line.partner_id if line.partner_id else invoice.partner_id 
                worksheet.write(row, 8, partner_id.ref or '' ,left_alignment) # Partner Reference
                worksheet.write(row, 9, partner_id.name or '' ,left_alignment) # Customer Name
                if partner_id.ref:
                    partner_dispaly_name = "[{}] {}".format(partner_id.ref,partner_id.name)
                else:
                    partner_dispaly_name = partner_id.name
                worksheet.write(row, 10, partner_dispaly_name or '' ,left_alignment) # Customer Display Name
                if partner_id.l10n_in_gst_treatment:
                    gst_treatment = get_selection_label(self,'res.partner','l10n_in_gst_treatment',partner_id.l10n_in_gst_treatment)
                else:
                    gst_treatment = ''
                worksheet.write(row, 11, gst_treatment,left_alignment) # GST Treatment
                worksheet.write(row, 12, partner_id.vat or '' ,left_alignment) # Partner GST
                worksheet.write(row, 13, line.product_category_id.display_name or '' ,left_alignment) # Product Category
                worksheet.write(row, 14, line.y_category_id.y_name or '' ,left_alignment) # Item Group
                worksheet.write(row, 15, line.product_id.product_tmpl_id.y_product_group_1.y_name or '' ,left_alignment) # Product Group 1
                worksheet.write(row, 16, line.product_id.product_tmpl_id.y_product_group_2.y_name or '' ,left_alignment) # Product Group 2
                worksheet.write(row, 17, line.product_id.product_tmpl_id.y_product_group_3.y_name or '' ,left_alignment) # Product Group 3
                worksheet.write(row, 18, line.product_id.default_code or '' ,left_alignment) # Product Reference
                worksheet.write(row, 19, line.product_id.name or '' ,left_alignment) # Product
                worksheet.write(row, 20, line.product_id.display_name or '' ,left_alignment) # Product Display Name
                worksheet.write(row, 21, line.product_id.weight ,style_number_float) # Product Weight( in 3 digits)
                worksheet.write(row, 22, (line.quantity * line.product_id.weight) ,center_alignment) # Total Weight
                worksheet.write(row, 23, line.quantity ,center_alignment) # Quantity
                worksheet.write(row, 24, line.product_uom_id.name or '' ,center_alignment) # Product UOM
                worksheet.write(row, 25, line.product_id.l10n_in_hsn_code or '' ,center_alignment) # HSN Code
                worksheet.write(row, 26, line.product_id.uom_id.l10n_in_code or '' ,left_alignment) # Indian GST UQC
                worksheet.write(row, 27, line.price_unit ,style_number_float) # MRP
                if line.quantity > 0:
                    price_unit_after_dic = line.price_subtotal/line.quantity
                else:
                    price_unit_after_dic = 0
                rate = 1/line.currency_rate
                worksheet.write(row, 28, price_unit_after_dic ,style_number_float) # Unit Price after all discounts
                worksheet.write(row, 29, (line.quantity * line.price_unit) ,left_alignment) # Gross Total
                worksheet.write(row, 30, line.y_trade_discounts ,center_alignment) # Trade Discount (%)
                worksheet.write(row, 31, line.y_trade_discount_amt ,style_number_float) # Trade Discount Amount
                worksheet.write(row, 32, line.y_quantity_discount ,center_alignment) # Quantity Discount (%)
                worksheet.write(row, 33, line.y_quantity_discount_amt ,style_number_float) # Quantity Disount Amount
                worksheet.write(row, 34, line.y_special_discount ,center_alignment) # Special Discount (%)
                worksheet.write(row, 35, line.y_specual_discount_amt ,style_number_float) # Special Discount Amount
                worksheet.write(row, 36, line.price_subtotal ,left_alignment) # Subtotal
                tmp_name = ''
                if line.tax_ids:
                    tmp_name = ",".join(line.tax_ids.mapped('name'))
                worksheet.write(row, 37, tmp_name or '',left_alignment) # Taxes
                cgst_percent = 0.0
                sgst_percent = 0.0
                igst_percent = 0.0
                tcs_percent = 0.0
                
                igst_amount = 0.0
                cgst_amount = 0.0
                sgst_amount = 0.0
                tcs_amount = 0.0
            
                tax_dict = line.sudo()._get_tax_line_group_values()
                if tax_dict:
                    igst_percent = tax_dict.get('IGST_RATE') if tax_dict.get('IGST') > 0 else 0 or 0
                    cgst_percent = tax_dict.get('CGST_RATE') if tax_dict.get('CGST') > 0 else 0 or 0
                    sgst_percent = tax_dict.get('SGST_RATE') if tax_dict.get('SGST') > 0 else 0 or 0
                    tcs_percent = tax_dict.get('TCS_RATE') or 0
                    igst_amount = tax_dict.get('IGST') if tax_dict.get('IGST') > 0 else 0 or 0
                    cgst_amount = tax_dict.get('CGST') if tax_dict.get('CGST') > 0 else 0 or 0
                    sgst_amount = tax_dict.get('SGST') if tax_dict.get('SGST') > 0 else 0 or 0
                    tcs_amount = tax_dict.get('TCS') or 0
                worksheet.write(row, 38, igst_percent ,center_alignment) # IGST Percent 
                worksheet.write(row, 39, igst_amount ,style_number_float) # IGST Amount
                worksheet.write(row, 40, cgst_percent ,center_alignment) # CGST Percent
                worksheet.write(row, 41, cgst_amount ,style_number_float) # CGST Amount
                worksheet.write(row, 42, sgst_percent ,center_alignment) # SGST Percent
                worksheet.write(row, 43, sgst_amount ,style_number_float) # SGST Amount
                worksheet.write(row, 44, tcs_percent ,center_alignment) # TCS Percent
                worksheet.write(row, 45, tcs_amount ,style_number_float) # TCS Amount
                tot_tax_amount = igst_amount + cgst_amount + sgst_amount
                worksheet.write(row, 46, tot_tax_amount ,style_number_float) # Tax Amount
                worksheet.write(row, 47, tot_tax_amount + line.price_subtotal ,style_number_float) # Net Total
                sub_total_inr = 0
                if invoice.currency_id.name == "INR":
                    sub_total_inr = line.price_subtotal
                else:
                    sub_total_inr = rate * line.price_subtotal
                worksheet.write(row, 48, sub_total_inr ,center_alignment) # Sub Total INR (EXPORT INVOICE)
                worksheet.write(row, 49, line.debit ,center_alignment) # Net Total INR (EXPORT INVOICE)
                worksheet.write(row, 50, line.account_id.group_id.name or '',left_alignment) # Account Group
                account_type = get_selection_label(self,'account.account','account_type',line.account_id.account_type)
                worksheet.write(row, 51, account_type or '' ,left_alignment) # Account Type
                worksheet.write(row, 52, line.account_id.display_name or '' ,left_alignment) # Account Name
                
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

                worksheet.write(row, 53, analytic_accounts or '' ,left_alignment) # Analytic Account
                worksheet.write(row, 54, analytic_plans or '' ,left_alignment) # Analytical Plan
                worksheet.write(row, 55, line.y_stock_move_id.picking_id.name  or '',left_alignment) # Stock Move Ref
                worksheet.write(row, 56, ",".join(line.sale_line_ids.order_id.mapped('name')) or '' ,left_alignment) # SO Number Ref
                worksheet.write(row, 57, invoice.l10n_in_transportation_doc_no or '' ,left_alignment) # EWAYBILL NO

                vehicle_type = ''
                vehicle_type_val = line.y_stock_move_id.picking_id.y_transportation_order_id.y_vehicle_type if line.y_stock_move_id.picking_id.y_transportation_order_id else line.y_stock_move_id.picking_id.y_vehicle_type
                if vehicle_type_val:
                    vehicle_type = get_selection_label(self,'stock.picking','y_vehicle_type',vehicle_type_val)   
                worksheet.write(row, 58, vehicle_type or '' ,left_alignment) # TRANSPORTATION TYPE
                worksheet.write(row, 59, line.y_stock_move_id.picking_id.y_transportation_order_id.y_fwd_agent.name or '' ,left_alignment) # TRANSPORTER NAME
                
                indent_num = ''
                if line.y_stock_move_id.picking_id.y_transportation_order_id.y_transportation_order_intent_line_ids:
                    indent_num = ",".join(line.y_stock_move_id.picking_id.y_transportation_order_id.y_transportation_order_intent_line_ids.y_fleet_indent_id.mapped('y_name'))
                worksheet.write(row, 60, indent_num or '' ,left_alignment) # VEHICLE INDENT NO
                worksheet.write(row, 61, sum(line.y_stock_move_id.picking_id.y_transportation_order_id.y_transportation_costing_ids.mapped('y_cost')) or '' ,left_alignment) # TRANSPORTAION COST

                gate_entry_date = ''
                gate_entry_no = ''
                if line.y_stock_move_id.picking_id.y_stock_gate_management_ids:
                    gate_entry_date = line.y_stock_move_id.picking_id.y_stock_gate_management_ids[-1].y_post_datetime
                    if line.y_stock_move_id.picking_id.y_stock_gate_management_ids.mapped('y_name'):
                        gate_entry_no = ",".join(line.y_stock_move_id.picking_id.y_stock_gate_management_ids.mapped('y_name'))
                worksheet.write(row, 62, gate_entry_date or '' ,date_style) # Gate Entry In Date
                worksheet.write(row, 63, gate_entry_no or '' ,left_alignment) # Gate Entry No

                external_vehicle_num = ''
                internal_vehicle_num = ''
                driver_name = ''
                if line.y_stock_move_id.picking_id.y_stock_gate_management_ids:
                    external_vehicle_num = ",".join(line.y_stock_move_id.picking_id.y_stock_gate_management_ids.filtered(lambda x:x.y_external_vehicle_no).mapped('y_external_vehicle_no'))
                    if line.y_stock_move_id.picking_id.y_stock_gate_management_ids.mapped('y_vehicle_no_id.display_name'):
                        internal_vehicle_num = ",".join(line.y_stock_move_id.picking_id.y_stock_gate_management_ids.filtered(lambda x:x.y_vehicle_no_id).mapped('y_vehicle_no_id.display_name'))
                    if line.y_stock_move_id.picking_id.y_stock_gate_management_ids.mapped('y_driver_name'):
                        driver_name = ",".join(line.y_stock_move_id.picking_id.y_stock_gate_management_ids.filtered(lambda x:x.y_driver_name).mapped('y_driver_name'))
                
                worksheet.write(row, 64, external_vehicle_num or '' ,left_alignment) # External Vehicle Number
                worksheet.write(row, 65, internal_vehicle_num or '' ,left_alignment) # Internal Vechile No.
                worksheet.write(row, 66, driver_name or '' ,left_alignment) # Driver Name
                partner_shipping_id = invoice.partner_shipping_id
                worksheet.write(row, 67, partner_shipping_id.name or '' ,left_alignment) # Delivery Name
                worksheet.write(row, 68, partner_id.street or '' ,left_alignment) # Invoice Street 1
                worksheet.write(row, 69, partner_shipping_id.street or '' ,left_alignment) # Delivery Street 1
                worksheet.write(row, 70, partner_id.street2 or '' ,left_alignment) # Invoice Street 2
                worksheet.write(row, 71, partner_shipping_id.street2 or '' ,left_alignment) # Delivery Street 2
                worksheet.write(row, 72, partner_id.zip or '' ,left_alignment) # Invoice Pincode
                worksheet.write(row, 73, partner_shipping_id.zip or '' ,left_alignment) # Delivery Pincode
                worksheet.write(row, 74, partner_id.y_city_id.y_name or '' ,left_alignment) # Invoice City
                worksheet.write(row, 75, partner_shipping_id.y_city_id.y_name or '' ,left_alignment) # Delivery City
                worksheet.write(row, 76, partner_id.y_district_id.y_name or '' ,left_alignment) # Invoice District
                worksheet.write(row, 77, partner_shipping_id.y_district_id.y_name or '' ,left_alignment) # Delivery District
                worksheet.write(row, 78, partner_id.state_id.name or '' ,left_alignment) # Partner State
                worksheet.write(row, 79, partner_shipping_id.state_id.name or '' ,left_alignment) # Delivery State
                worksheet.write(row, 80, partner_id.country_id.name or '' ,left_alignment) # Partner Country
                worksheet.write(row, 81, partner_shipping_id.country_id.name or '' ,left_alignment) # Delivery Country
                worksheet.write(row, 82, line.y_stock_move_id.location_id.display_name or '' ,left_alignment) # Delivery Country
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