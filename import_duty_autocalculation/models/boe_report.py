from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
from odoo import api, fields, models, _
from num2words import num2words
from calendar import monthrange
from lxml import etree
from odoo import fields, models, tools
from odoo.tools import formatLang
import json
import re
from odoo.exceptions import AccessError, UserError, ValidationError
# from forex_python.converter import CurrencyRates
import requests
import json
import psycopg2
import simplejson
from odoo.tools import float_compare, date_utils, email_split, html_escape, is_html_empty


class BoeReport(models.Model):
    _name = "boe.report"
    _description = "Boe Report"

    y_sl_no = fields.Integer(string="Sr. No.")
    y_boe_id = fields.Many2one('boe.template')
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order NO.")
    y_partner_id = fields.Many2one(related="y_boe_id.y_partner_id",string="Supplier Name")
    y_bill_of_entry_no = fields.Char(related="y_boe_id.y_bill_of_entry_no",string="BOE No.")
    y_bill_of_entry_date = fields.Date(related="y_boe_id.y_bill_of_entry_date",string="BOE Date")
    y_boe_line_id = fields.Many2one('boe.template.line')
    y_product_id = fields.Many2one(related="y_boe_line_id.y_product_id")
    y_default_code = fields.Char(related="y_product_id.default_code",string="Part No")
    y_product_name = fields.Char(related="y_product_id.name",string="Description Of Goods")
    y_with_service_value_included = fields.Float(related="y_boe_line_id.y_with_service_value_included",string="Value in INR")
    y_product_qty = fields.Float(related="y_boe_line_id.y_product_qty",string="Qty")
    y_price_unit = fields.Float(related="y_boe_line_id.y_price_unit",string="Unit Price")
    y_total_assessable_value = fields.Float(related="y_boe_line_id.y_total_assessable_value",string="Assessable Value (As per BOE)")
    y_calculate_value_for_additional = fields.Float(related="y_boe_line_id.y_calculate_value_for_additional",string="Invoice Value in INR")
    y_bill_of_entry_rate = fields.Float(related="y_boe_id.y_bill_of_entry_rate")

    y_addtional_duty1 = fields.Float(string="Additional Duties 1")
    y_addtional_duty2 = fields.Float(string="Additional Duties 2")
    y_addtional_duty3 = fields.Float(string="Additional Duties 3")
    y_addtional_duty4 = fields.Float(string="Additional Duties 4")
    y_addtional_duty5 = fields.Float(string="Additional Duties 4")

    y_service_imports1 = fields.Float(string="Service Imports1")
    y_service_imports2 = fields.Float(string="Service Imports2")
    y_service_imports3 = fields.Float(string="Service Imports3")
    y_service_imports4 = fields.Float(string="Service Imports4")
    y_service_imports5 = fields.Float(string="Service Imports5")

    y_importy_duty_structure_calculated_value1 = fields.Float(string="IDS Cal Value1")
    y_importy_duty_structure_calculated_amount1 = fields.Float(string="IDS Cal Amount1")
    y_importy_duty_structure_calculated_value2 = fields.Float(string="IDS Cal Value2")
    y_importy_duty_structure_calculated_amount2 = fields.Float(string="IDS Cal Amount2")
    y_importy_duty_structure_calculated_value3 = fields.Float(string="IDS Cal Value3")
    y_importy_duty_structure_calculated_amount3 = fields.Float(string="IDS Cal Amount3")
    y_importy_duty_structure_calculated_value4 = fields.Float(string="IDS Cal Value4")
    y_importy_duty_structure_calculated_amount4 = fields.Float(string="IDS Cal Amount4")
    y_importy_duty_structure_calculated_value5 = fields.Float(string="IDS Cal Value5")
    y_importy_duty_structure_calculated_amount5 = fields.Float(string="IDS Cal Amount5")


    y_invoice_number = fields.Many2one(related="y_boe_id.y_invoice_number")
    



    def boe_register_query(self,y_start_date,y_end_date):
        attedance_details = self.env['boe.report'].search([]).unlink()
        boe_obj = self.env['boe.template'].search([('y_bill_of_entry_date','>=',y_start_date),('y_bill_of_entry_date','<=',y_end_date),('y_state','=','confirm')])
        y_sl_no = 0

        for boe in boe_obj:
            importy_duty_structure_calculated_value1=importy_duty_structure_calculated_amount1=importy_duty_structure_calculated_value2=importy_duty_structure_calculated_amount2=importy_duty_structure_calculated_value3=importy_duty_structure_calculated_amount3=importy_duty_structure_calculated_value4=importy_duty_structure_calculated_amount4=importy_duty_structure_calculated_value5=importy_duty_structure_calculated_amount5=0
            addtional_duty1=addtional_duty2=addtional_duty3=addtional_duty4=addtional_duty5=service_imports1=service_imports2=service_imports3=service_imports4=service_imports5 = 0
            for boe_lines in boe.y_boe_template_line_ids:
                if boe_lines.y_addtional_quanitity_boe_line_ids:
                    if 0 < len(boe_lines.y_addtional_quanitity_boe_line_ids):
                        addtional_duty1 = boe_lines.y_addtional_quanitity_boe_line_ids[0].y_sum_value
                    if 1 < len(boe_lines.y_addtional_quanitity_boe_line_ids):
                        addtional_duty2 = boe_lines.y_addtional_quanitity_boe_line_ids[1].y_sum_value
                    if 2 < len(boe_lines.y_addtional_quanitity_boe_line_ids):
                        addtional_duty3 = boe_lines.y_addtional_quanitity_boe_line_ids[2].y_sum_value
                    if 3 < len(boe_lines.y_addtional_quanitity_boe_line_ids):
                        addtional_duty4 = boe_lines.y_addtional_quanitity_boe_line_ids[3].y_sum_value
                    if 4 < len(boe_lines.y_addtional_quanitity_boe_line_ids):
                        addtional_duty5 = boe_lines.y_addtional_quanitity_boe_line_ids[4].y_sum_value
                
                if boe_lines.y_service_import_report_line_ids:
                    if 0 < len(boe_lines.y_service_import_report_line_ids):
                        service_imports1 = boe_lines.y_service_import_report_line_ids[0].y_sum_value
                    if 1 < len(boe_lines.y_service_import_report_line_ids):
                        service_imports2 = boe_lines.y_service_import_report_line_ids[1].y_sum_value
                    if 2 < len(boe_lines.y_service_import_report_line_ids):
                        service_imports3 = boe_lines.y_service_import_report_line_ids[2].y_sum_value
                    if 3 < len(boe_lines.y_service_import_report_line_ids):
                        service_imports4 = boe_lines.y_service_import_report_line_ids[3].y_sum_value
                    if 4 < len(boe_lines.y_service_import_report_line_ids):
                        service_imports5 = boe_lines.y_service_import_report_line_ids[4].y_sum_value

                if boe_lines.y_import_duty_structure_line_boe_ids:
                    if 0 < len(boe_lines.y_import_duty_structure_line_boe_ids):
                        importy_duty_structure_calculated_value1 = boe_lines.y_import_duty_structure_line_boe_ids[0].y_calculated_value
                        importy_duty_structure_calculated_amount1 = boe_lines.y_import_duty_structure_line_boe_ids[0].y_assesable_value
                    if 1 < len(boe_lines.y_import_duty_structure_line_boe_ids):
                        importy_duty_structure_calculated_value2 = boe_lines.y_import_duty_structure_line_boe_ids[1].y_calculated_value
                        importy_duty_structure_calculated_amount2 = boe_lines.y_import_duty_structure_line_boe_ids[1].y_assesable_value                    
                    if 2 < len(boe_lines.y_import_duty_structure_line_boe_ids):
                        importy_duty_structure_calculated_value3 = boe_lines.y_import_duty_structure_line_boe_ids[2].y_calculated_value
                        importy_duty_structure_calculated_amount3 = boe_lines.y_import_duty_structure_line_boe_ids[2].y_assesable_value
                    if 3 < len(boe_lines.y_import_duty_structure_line_boe_ids):
                        importy_duty_structure_calculated_value4 = boe_lines.y_import_duty_structure_line_boe_ids[3].y_calculated_value
                        importy_duty_structure_calculated_amount4 = boe_lines.y_import_duty_structure_line_boe_ids[3].y_assesable_value
                    if 4 < len(boe_lines.y_import_duty_structure_line_boe_ids):
                        importy_duty_structure_calculated_value5 = boe_lines.y_import_duty_structure_line_boe_ids[4].y_calculated_value
                        importy_duty_structure_calculated_amount5 = boe_lines.y_import_duty_structure_line_boe_ids[4].y_assesable_value
                # addtional_duty1 = sum(boe_lines.addtional_quanitity_boe_line_ids.filtered(lambda x:x.product_id.name == 'Freight').mapped('sum_value'))
                # addtional_duty2 = sum(boe_lines.addtional_quanitity_boe_line_ids.filtered(lambda x:x.product_id.name == 'Insurance').mapped('sum_value'))
                # service_imports1 = sum(boe_lines.service_import_report_line_ids.filtered(lambda x:x.product_id.name == 'Freight').mapped('sum_value'))
                # service_imports2 = sum(boe_lines.service_import_report_line_ids.filtered(lambda x:x.product_id.name == 'Insurance').mapped('sum_value'))

                vals={
                'y_boe_id':boe.id,
                'y_sl_no':y_sl_no+1,
                'y_boe_line_id':boe_lines.id,
                'y_purchase_id':boe_lines.y_purchase_id.id,

                'y_addtional_duty1':addtional_duty1,
                'y_addtional_duty2':addtional_duty2,
                'y_addtional_duty3':addtional_duty3,
                'y_addtional_duty4':addtional_duty4,
                'y_addtional_duty5':addtional_duty5,
                'y_service_imports1':service_imports1,
                'y_service_imports2':service_imports2,
                'y_service_imports3':service_imports3,
                'y_service_imports4':service_imports4,
                'y_service_imports5':service_imports5,
                'y_importy_duty_structure_calculated_value1':importy_duty_structure_calculated_value1,
                'y_importy_duty_structure_calculated_amount1':importy_duty_structure_calculated_amount1,
                'y_importy_duty_structure_calculated_value2':importy_duty_structure_calculated_value2,
                'y_importy_duty_structure_calculated_amount2':importy_duty_structure_calculated_amount2,
                'y_importy_duty_structure_calculated_value3':importy_duty_structure_calculated_value3,
                'y_importy_duty_structure_calculated_amount3':importy_duty_structure_calculated_amount3,
                'y_importy_duty_structure_calculated_value4':importy_duty_structure_calculated_value4,
                'y_importy_duty_structure_calculated_amount4':importy_duty_structure_calculated_amount4,
                'y_importy_duty_structure_calculated_value5':importy_duty_structure_calculated_value5,
                'y_importy_duty_structure_calculated_amount5':importy_duty_structure_calculated_amount5,

                }
                self.env['boe.report'].create(vals)
                y_sl_no = y_sl_no+1

        


        return {
            'name': _("Boe Report"),
            'type': 'ir.actions.act_window',
            'res_model': 'boe.report',
            'view_mode': 'list,pivot',
            'views': [(self.env.ref('import_duty_autocalculation.view_boe_report_list').id, 'list'),(False, 'pivot')],
            'target': 'current',
        }


