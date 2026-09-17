# -*- coding: utf-8 -*-
from markupsafe import Markup
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
from odoo import api, fields, models, _
from num2words import num2words
from calendar import monthrange
from lxml import etree
from odoo import fields, models, tools
from odoo.tools import formatLang
import re
from odoo.exceptions import AccessError, UserError, ValidationError
# from forex_python.converter import CurrencyRates
import requests
import json
import psycopg2
import simplejson
from odoo.tools import float_compare, date_utils, email_split, html_escape, is_html_empty
from odoo.tools.misc import clean_context, formatLang
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)



class ResCompany(models.Model):
    _inherit = "res.company"

    y_is_export_oriented_unit = fields.Boolean(string="Export Oriented Unit")



class ResPartner(models.Model):
    _inherit = 'res.partner'

    y_is_boe = fields.Boolean(string="Bill Of Entry")



#separate file
class AccountIncoterm(models.Model):
    _inherit = "account.incoterms"

    y_additional_cost_applied = fields.Boolean(string="Additional Cost")
    y_included_landed_cost = fields.Boolean(string="Included Landed Cost")

    y_additional_incoterms_line_ids = fields.One2many('additional.incoterms.line','y_incoterm_id',string="Additional Incoterm Line")


class AdditionalIncotermLine(models.Model):
    _name = "additional.incoterms.line"
    _description = "Additional Incoterm Lines"

    y_product_id = fields.Many2one('product.product',string="Product")
    y_incoterm_id = fields.Many2one('account.incoterms',string="Incoterm")
    y_cost = fields.Float(string="Cost")

#############################




#Miscellaneous total assesable value
class BoeMiscellaneousValues(models.Model):
    _name = "boe.miscellaneous.value.line"
    _description = "BOE Miscellaneous Value Line"

    y_product_id = fields.Many2one('product.product',string="Product")
    y_calculated_type =  fields.Selection([('value','Value'),('percentage','Percentage')], string='Calculation Type', copy=False)
    y_currency_id = fields.Many2one('res.currency',string="Currency")
    y_currency_excahange_rate = fields.Float(string="Currency Exchange Rate")
    y_calculated_value  = fields.Float(string="Calculation Value",digits=(12, 3))
    y_miscellaneous_boe_id = fields.Many2one('boe.template')
    y_is_diff_country = fields.Boolean(string="Is diff country")
    y_sum_value = fields.Float(string="Total Sum")
    y_miscellaneous_value_boe_line_id = fields.Many2one('boe.template.line')
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")

    @api.onchange('y_currency_id')
    def onchange_currency(self):
        for line in self:
            if line.y_currency_id:
                if line.y_miscellaneous_boe_id.y_company_id.currency_id != line.y_currency_id:
                    line.y_is_diff_country = True



#po wise total assesable value
class PurchaseOrderTotAccesVal(models.Model):
    _name = "po.total.accessable.value.line"

    y_boe_template_id = fields.Many2one('boe.template')
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_total_assessable_value = fields.Float(string="Total Assessable Value(FCY)(Basic)")
    y_total_assessable_value_lcy = fields.Float(string="Total Assessable Value(LCY)(Including additional duties)")


#after update qty from boe validation if qty done is changes
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('qty_done')
    def onchange_qty_done(self):
        for rec in self:
            if rec.qty_done and rec.picking_id.y_boe_template_id:
                raise UserError(_("You cannot modify the quantity after processing BOE"))


class StockMove(models.Model):
    _inherit = "stock.move"

    y_boe_template_line_id = fields.Many2one('boe.template.line',string="Boe Template Line")


#inside BOE Line wizard line wise service calculation
class ServiceDataImports(models.Model):
    _name = "service.data.imports"
    _description = "Service Data Imports"

    y_service_boe_line_id = fields.Many2one('boe.template.line')
    y_product_id = fields.Many2one('product.product',string="Product")
    y_sum_value = fields.Float(string="Total Sum")



#inside wizard line wise additional quantity lines
class AdditionalComponentLines(models.Model):
    _name = "additional.quantity.lines"
    _description = "Additional Quantity Lines"

    y_product_id = fields.Many2one('product.product',string="Product")
    y_calculated_type =  fields.Selection([('value','Value'),('percentage','Percentage')], string='Calculation Type', copy=False)
    y_currency_id = fields.Many2one('res.currency',string="Currency")
    y_currency_excahange_rate = fields.Float(string="Currency Exchange Rate")
    y_calculated_value  = fields.Float(string="Calculation Value",digits=(12, 5))
    y_additional_boe_id = fields.Many2one('boe.template')
    y_is_diff_country = fields.Boolean()
    y_sum_value = fields.Float(string="Total Sum")
    y_addtional_quanitity_boe_line_id = fields.Many2one('boe.template.line')
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_is_duty_payable = fields.Boolean(string="Is Duty Payable")

    @api.onchange('y_currency_id')
    def onchange_currency(self):
        for line in self:
            if line.y_currency_id:
                if line.y_additional_boe_id.y_company_id.currency_id != line.y_currency_id:
                    line.y_is_diff_country = True
                if line.y_currency_id == line.y_additional_boe_id.y_currency_id:
                    line.write({'y_currency_excahange_rate':line.y_additional_boe_id.y_bill_of_entry_rate})




# Separate tab for service products which are coming from PO
class AdditionalImportServices(models.Model):
    _name = "additional.import.services"
    _description = "Additional Import Services"

    y_product_id = fields.Many2one('product.product',string="Product")
    y_product_qty = fields.Float('Quantity')
    y_price_unit = fields.Float(string="Unit Price")
    y_currency_id = fields.Many2one('res.currency',string="Currency Code")
    y_price_subtotal = fields.Monetary(currency_field='y_currency_id',string='Subtotal')
    y_with_service_value_included = fields.Float(string="Basic Assessable Value",compute="get_compute_value")
    y_addtional_import_service_line_id = fields.Many2one('boe.template.line')
    y_addtional_import_service_id = fields.Many2one('boe.template')
    y_purchase_line_id = fields.Many2one('purchase.order.line',string="Purchase Line")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")


    @api.depends('y_addtional_import_service_id.y_bill_of_entry_rate','y_price_subtotal')
    def get_compute_value(self):
        for rec in self:
            if rec.y_addtional_import_service_id.y_bill_of_entry_rate or rec.y_price_subtotal:
                rec.y_with_service_value_included = rec.y_price_subtotal * rec.y_addtional_import_service_id.y_bill_of_entry_rate
            else:
                rec.y_with_service_value_included = 0


# Main Model
class BoeMaster(models.Model):
    _name = "boe.template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "BOE Template"
    _rec_name = "y_bill_of_entry_code"

    y_name = fields.Char(string="Transaction Number")
    y_date = fields.Date(string='Date', readonly=True)
    y_amount = fields.Float(string='Amount', readonly=True)
    y_bill_of_entry_code = fields.Char(string="BOE Code",default=lambda self: _('Draft'))
    y_bill_of_entry_no = fields.Char(string="Bill of Entry No",tracking=True)
    y_bill_of_entry_date = fields.Date(string="Bill of Entry Date",copy=False,tracking=True)
    y_bill_of_entry_rate = fields.Float(string="Exchange Rate",copy=False,tracking=True,store=True,compute="compute_exchange_rate",inverse="inverse_boe_rate")
    y_currency_id = fields.Many2one('res.currency',string="Currency Code")
    y_partner_id = fields.Many2one('res.partner',string="Vendor")
    y_duty_to_pay_vendor_id = fields.Many2one('res.partner',string="Duty to Pay Vendor",tracking=True)
    y_total_assessable_value = fields.Float(string="Total Assessable Value(FCY)",compute="compute_total_assessable_value")
    y_total_assessable_value_lcy = fields.Float(string="Total Assessable Value(LCY)",compute="compute_total_assessable_value")
    y_invoice_number = fields.Many2one('account.move',string="Invoice")
    y_invoice_ids = fields.One2many('account.move','y_boe_id',string="Bills")
    y_invoice_name = fields.Char(string="Invoice No",tracking=True)
    y_invoice_date = fields.Date(string="Invoice Date",tracking=True)
    y_invoice_value = fields.Float(string="Invoice Value",tracking=True)
    y_warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse",tracking=True)
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order",domain="[('state','in',('purchase','done'))]")
    y_company_id = fields.Many2one('res.company',string="Company",readonly=True)

    y_is_execute_all_clicked = fields.Boolean(string="Is execute all")
    y_duties_exempted = fields.Boolean(string="Duties Exempted",tracking=True)
    y_exim_notification = fields.Char(string="Exim Notification",tracking=True)
    y_boe_template_id = fields.Many2one('boe.template')
    y_payment_id = fields.Many2one('account.payment',string="Payment")


    y_boe_template_line_ids = fields.One2many('boe.template.line','y_boe_template_id',string="BOE Lines")
    y_import_duty_boe_structure_ids = fields.One2many('import.duty.structure','y_boe_template_strucure_id')

    y_import_duty_boe_line_ids = fields.One2many('import.duty.structure.line','y_boe_template_id',string="Import Duty Structure Line")
    y_additional_quantity_line_ids = fields.One2many('additional.quantity.lines','y_additional_boe_id',string="Additional Duties",copy=False)
    y_additional_import_service_ids = fields.One2many('additional.import.services','y_addtional_import_service_id',string="Service Imports")
    y_po_total_accessable_value_line_ids = fields.One2many('po.total.accessable.value.line','y_boe_template_id',string="Po Wise Total Assesable Value")

    y_miscellaneous_value_line_ids = fields.One2many('boe.miscellaneous.value.line','y_miscellaneous_boe_id',string="Miscellaneous Assesable Value")
    y_other_charges_line_ids = fields.One2many('other.chargers','y_boe_template_id',string="Other Charges")


    y_state = fields.Selection([('draft','Open'),('in_process','In Process'),('confirm','Validated'),('cancel','Cancelled')], string='Status', copy=False,default='draft',tracking=True)
    y_purchase_boe_bill_id = fields.Many2one('purchase.boe.bill',
        string='Auto-complete',
        help="Auto-complete from a past Invoice / sale order.",default='draft',copy=False)

    y_purchase_order_ids = fields.Many2many('purchase.order',string="Purchase Orders")
    y_picking_ids = fields.Many2many('stock.picking',string="Receipt numbers")

    y_country_orgin_goods_id = fields.Many2one('res.country',string="Country of origin",tracking=True)
    y_port_loading_id = fields.Many2one('l10n_in.port.code',string="Port of Loading",tracking=True)
    y_port_discharge_id = fields.Many2one('l10n_in.port.code',string="Port of Discharge",tracking=True)
    y_incoterm_id = fields.Many2one('account.incoterms',string="Incoterm",tracking=True)
    y_additional_cost_applied = fields.Boolean(string="Additional Cost",related="y_incoterm_id.y_additional_cost_applied")

    y_duty_payable = fields.Float(string="Duty Payable",compute="_compute_totoal_assesable_value")


    y_advance_request_form_approval_id = fields.Many2one('advance.request.approval.form',string="Advance Request Approval")
    y_purchase_account_payment_ids = fields.One2many('purchase.account.payment','y_boe_id')
    y_is_downpayment_generated = fields.Boolean(string="Is Downpayment Generated")

    # y_boe_downpayment_ids = fields.Char()


    def write(self,vals):
        new_dist = []
        if vals.get('y_boe_template_line_ids'):
            new_list = []
            for list1 in vals.get('y_boe_template_line_ids'):
                new_list.append(list1)
                boe_line_ids = self.y_boe_template_line_ids.filtered(lambda x:x.id in [value[1] for value in new_list])
                new_dist = []
                for dicts in boe_line_ids:
                    for newval in new_list:
                        if not isinstance(newval[-1],int):
                            if newval[1] == dicts.id:
                               
                                foc_value = newval[-1].get('y_is_foc')

                                new_dist.append('{}{} ---> {}'.format(f"FOC for {dicts.y_product_id.name}:",dicts.y_is_foc,foc_value))
                                  
            if new_dist:
                msg = ', '.join(dic for dic in new_dist)
                if self.env.user:
                    self.message_post(body=msg)                
        
        return super().write(vals)





    @api.onchange('y_incoterm_id')
    def onchange_incoterm(self):
        for rec in self:
            if rec.y_incoterm_id and rec.y_incoterm_id.y_additional_cost_applied:
                rec.y_additional_quantity_line_ids=[(5,0,0)]
                for incoterm_lines in rec.y_incoterm_id.y_additional_incoterms_line_ids:
                    if incoterm_lines.y_product_id not in rec.y_additional_quantity_line_ids.mapped('y_product_id'):
                        rec.y_additional_quantity_line_ids = [(0, 0,{'y_product_id': incoterm_lines.y_product_id.id,'y_calculated_value': incoterm_lines.y_cost})]
                    





    #to fetch exchange rate from custom exchange rate
    @api.depends('y_currency_id','y_bill_of_entry_date','y_company_id')
    def compute_exchange_rate(self):
        for line in self:
            if line.y_currency_id or line.y_bill_of_entry_date:
                exim_currency_id = self.env['exim.currency'].search([('y_currency_id','=',line.y_currency_id.id)])
                company_currency = self.y_company_id.currency_id
                exim_company_currency_id = self.env['exim.currency'].search([('y_currency_id','=',company_currency.id)])
                # currency_rate = self.currency_id._get_conversion_rate(line.y_currency_id, company_currency, self.company_id, line.y_bill_of_entry_date or  fields.Date.context_today(line))
                currency_rate = self.env['exim.currency']._get_conversion_rate(exim_currency_id, exim_company_currency_id, line.y_company_id, line.y_bill_of_entry_date or  fields.Date.context_today(line))

                line.y_bill_of_entry_rate = currency_rate
            else:
                line.y_bill_of_entry_rate = 1

    def inverse_boe_rate(self):
        for rec in self:
            rec.y_bill_of_entry_rate = rec.y_bill_of_entry_rate



    # currency rate updation in account.move
    # @api.depends('currency_id', 'company_currency_id', 'company_id', 'invoice_date','y_manual_rate')
    # def _compute_invoice_currency_rate(self):
    #     res = super()._compute_invoice_currency_rate
    #     for move in self:
    #         if move.is_invoice(include_receipts=True):
    #             if move.currency_id and move.y_manual_rate:
    #                 move.invoice_currency_rate = 1.0 / move.y_manual_rate
    #             else:
    #                 move.invoice_currency_rate = 1
                


   

    #changed
    @api.constrains('y_bill_of_entry_date','y_invoice_date')
    def check_boe_date(self):
        for rec in self:
            if rec.y_bill_of_entry_date and rec.y_invoice_date:
                if rec.y_bill_of_entry_date < rec.y_invoice_date:
                    raise UserError(_("The BOE date should be on or before the invoice date."))

    def action_cancel(self):
        for rec in self:
            if 'done' not in rec.y_picking_ids.mapped('state'):
                rec.write({'y_state':'cancel'})
            else:
                raise UserError(_("BOE cannot be canceled as the corresponding receipt has already been completed"))




    def create_down_payment(self,object):
    
        if object.y_payment_id:
            raise UserError(_("Payment already created for this BOE"))
        if object.y_state != 'confirm':            
            raise UserError(_('Down Payment Request can be processed only if the Order is in Confirmed State!'))

        down_payment_ids = object.y_purchase_account_payment_ids.filtered(lambda x:x.y_approval_status in ('approval_pending','approved'))
        if down_payment_ids:
            raise ValidationError("Down Payment Amount Already Created!")

        
        domain = [('y_company_id','=',object.y_company_id.id)]
        advance_request_form_approval_obj = self.env['advance.request.approval.form'].search(domain,limit=1)
        if not advance_request_form_approval_obj and object.y_company_id.sudo().parent_id:
            domain = [('y_company_id','=',object.y_company_id.sudo().parent_id.id)]
            advance_request_form_approval_obj = self.env['advance.request.approval.form'].sudo().search(domain,limit=1)
        if not advance_request_form_approval_obj:
            raise UserError(_("Please Map Approvals for Down Payment Request"))

        object.y_advance_request_form_approval_id = advance_request_form_approval_obj.id 

        y_bill_of_entry_date = object.y_bill_of_entry_date

        # remarks = f"{object.y_bill_of_entry_code}/ {str(y_bill_of_entry_date)}"

        remarks = Markup("""BOE No : {BOE_no} \nBOE Date : {BOE_date} \nPort of Discharge : {port_discharge} \nWarehouse : {warehouse} \nCompany : {company}""".format(BOE_no=object.y_bill_of_entry_no,BOE_date=str(y_bill_of_entry_date),port_discharge=object.y_port_discharge_id.display_name,company=object.y_company_id.display_name,warehouse=object.y_warehouse_id.name))
        
        return {
            "name":"Down Payment Request",
            "type": "ir.actions.act_window",
            "res_model": "boe.advance.payment.wizard",
            "views": [[False, "form"]],
            "target": 'new',
            "context":dict(y_boe_id=object.id,default_y_boe_id=object.id,default_y_payment_amount=object.y_duty_payable,default_y_company_id=object.y_company_id.id,default_y_currency_id=object.y_company_id.currency_id.id,default_y_port_discharge_id = object.y_port_discharge_id.id,default_y_remark=str(remarks)),
            }
        
        

    def view_payment(self):
        return {
                    "name": "Payments",
                    "type": "ir.actions.act_window",
                    "res_model": "account.payment",
                    "view_mode": 'form',
                    "res_id": self.y_payment_id.id,
                    }

    def view_downpayment(self):
        return {
                    "name": "Down payment",
                    "type": "ir.actions.act_window",
                    "res_model": "purchase.account.payment",
                    "view_mode": 'list',
                    'domain': [('y_boe_id', '=', self.id)],
                    }


    
    

    @api.depends('y_import_duty_boe_line_ids.y_assesable_value','y_additional_quantity_line_ids.y_calculated_value')
    def _compute_totoal_assesable_value(self):
        for rec in self:
            rec.y_duty_payable = sum(rec.y_import_duty_boe_line_ids.mapped('y_assesable_value')) + sum(rec.y_additional_quantity_line_ids.filtered(lambda x:x.y_is_duty_payable).mapped('y_calculated_value'))

    def update_record(self):
        for record in self:
            if record.y_bill_of_entry_rate == 0.0:
                raise UserError(_("Please maintain Exchange Rate"))
            value = self.y_boe_template_line_ids.mapped('y_product_qty')
            if 0.0 in value:
                raise UserError(_("Update Quantity in Boe Lines"))

            for rec in record.y_boe_template_line_ids:
                if record.y_bill_of_entry_rate:
                    rec.y_with_service_value_included = (rec.y_price_subtotal * record.y_bill_of_entry_rate)
                    rec.y_total_assessable_value = (rec.y_price_subtotal * record.y_bill_of_entry_rate)

            for rec in record.y_boe_template_line_ids:
                service_total = sum(record.y_additional_import_service_ids.mapped('y_with_service_value_included'))
                without_service_total = sum(record.y_boe_template_line_ids.mapped('y_with_service_value_included'))
                rec.y_total_calculated_assessable_value = (service_total*rec.y_with_service_value_included)/without_service_total
                rec.y_calculate_value_for_additional = rec.y_total_calculated_assessable_value + rec.y_with_service_value_included
                # rec.miscellaneous_value_for_additional = rec.y_with_service_value_included + rec.y_total_calculated_assessable_value
                rec.y_total_assessable_value = (rec.y_price_subtotal * record.y_bill_of_entry_rate) + rec.y_total_calculated_assessable_value


    @api.onchange('y_duties_exempted','y_exim_notification')
    def trigger_line_duties(self):
        if self.y_duties_exempted and self.y_exim_notification:
            for boe_line in self.y_boe_template_line_ids:
                boe_line.write({'y_duties_exempted':self.y_duties_exempted,'y_exim_notification':self.y_exim_notification})

    @api.constrains('y_bill_of_entry_no')
    def _check_duplicate_boe_no(self):
        moves = self.filtered(lambda move: move.y_state == 'draft' and move.y_bill_of_entry_no)
        if not moves:
            return
        self.env["boe.template"].flush_model([
            "y_bill_of_entry_no", 
            "y_company_id",
        ])
        self._cr.execute('''
            SELECT move2.id
            FROM boe_template move
            INNER JOIN boe_template move2 ON
                move2.y_bill_of_entry_no = move.y_bill_of_entry_no
                AND move2.y_company_id = move.y_company_id
                AND move2.id != move.id
            WHERE move.id IN %s
        ''', [tuple(moves.ids)])
        duplicated_moves = self.browse([r[0] for r in self._cr.fetchall()])
        if duplicated_moves:
            raise ValidationError(_('Duplicated Bill of Entry No detected. You probably encoded twice the same BOE:\n%s') % "\n".join(
                duplicated_moves.mapped(lambda m: "%(y_bill_of_entry_no)s" % {
                    'y_bill_of_entry_no': m.y_bill_of_entry_no,
                })
            ))

    def calculate_all(self):
        for rec in self:
            rec.update_record()
            if rec.y_miscellaneous_value_line_ids:
                rec.execute_miscellaneous_value()
            if rec.y_additional_quantity_line_ids:
                rec.execute_calculated_value()
            if rec.y_other_charges_line_ids:
                rec.execute_other_charger()
            rec.execute_all()

            for boe_line in rec.y_boe_template_line_ids:
                boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + sum(boe_line.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value')) + sum(boe_line.y_boe_miscellaneous_value_line_ids.mapped('y_sum_value'))
            rec.write({'y_state':'in_process'})

    def reset_value(self):
        for rec in self:
            total_po = rec.mapped('y_purchase_order_ids')
            rec.y_purchase_order_ids = False
            rec.y_boe_template_line_ids.unlink()
            rec.y_import_duty_boe_line_ids.unlink()
            rec.y_additional_quantity_line_ids.unlink()
            rec.y_po_total_accessable_value_line_ids.unlink()
            rec.y_miscellaneous_value_line_ids.unlink()
            rec.y_additional_import_service_ids.unlink()
            rec.y_is_execute_all_clicked = False
            rec.y_state = 'draft'
            for boe_lines in rec.y_boe_template_line_ids:
                boe_lines.y_is_excecute_clicked = False
                boe_lines.y_is_arrow_clicked = False
                boe_lines.y_import_duty_structure_line_boe_ids.unlink()

            for po in total_po:
                rec.y_purchase_id = po.id
                rec._onchange_sale_auto_complete()




    def execute_all(self):
        if not self.y_is_execute_all_clicked:
            for line in self.y_boe_template_line_ids:
                line.execute_all_action_show_details()
                line.button_execute()
            self.y_is_execute_all_clicked = True

    def reset_to_draft(self):
        if self.env.user.has_group('import_duty_autocalculation.group_reset_to_draft'):
            for rec in self:
                if rec.y_state in ('confirm','in_process'):
                    if rec.y_picking_ids:
                        if 'done' in rec.y_picking_ids.mapped('state'):
                            raise UserError(_("Picking already completed"))
                    rec.y_import_duty_boe_line_ids.unlink()
                    rec.y_po_total_accessable_value_line_ids.unlink()
                    rec.y_is_execute_all_clicked = False
                    rec.y_state = 'draft'
                    for boe_lines in rec.y_boe_template_line_ids:
                        boe_lines.y_is_excecute_clicked = False
                        boe_lines.y_is_arrow_clicked = False
                        boe_lines.y_import_duty_structure_line_boe_ids.unlink()
                        boe_lines.y_boe_other_charger_line_ids.unlink()
                        # boe_lines.y_po_total_accessable_value_line_ids.unlink()
                        
        else:
            raise UserError(_("You are Not Authorised"))

    def unlink(self):
        for rec in self:
            if rec.y_state != 'draft':
                raise UserError("Confirmed document cannot be deleted")
        res = super().unlink()
        return res

    def calculate_percent(self,percentage,value):
        percentage_value = percentage/100
        return (percentage_value*value)

    def execute_calculated_value(self):
        value = self.y_boe_template_line_ids.mapped('y_product_qty')
        if 0.0 in value:
            raise UserError(_("Update Quantity in Boe Lines"))
       
        else:
            for addtional_lines in self.y_additional_quantity_line_ids.filtered(lambda x:x.y_is_duty_payable == False):
                for boe_line in self.y_boe_template_line_ids:
                    if not boe_line.y_is_additional_quantity_executed:
                        if addtional_lines.y_purchase_id == boe_line.y_purchase_id:
                            if addtional_lines.y_calculated_type == 'percentage':
                                if addtional_lines.y_product_id.product_tmpl_id.y_is_insurance_for_idc == True:
                                    boe_value = boe_line.y_calculate_value_for_additional + boe_line.y_miscellaneous_value_for_additional
                                    percent_value = self.calculate_percent(addtional_lines.y_calculated_value,boe_value)
                                    boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': percent_value})]
                                    boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + percent_value 
                                else:
                                    boe_value = boe_line.y_calculate_value_for_additional
                                    percent_value = self.calculate_percent(addtional_lines.y_calculated_value,boe_value)
                                    boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': percent_value})]
                                    boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + percent_value + boe_line.y_miscellaneous_value_for_additional

                            if addtional_lines.y_calculated_type == 'value':
                                if addtional_lines.y_currency_id != boe_line.y_boe_template_id.y_company_id.currency_id:
                                    calculate_value = addtional_lines.y_calculated_value * addtional_lines.y_currency_excahange_rate
                                    if addtional_lines.y_product_id.product_tmpl_id.y_is_insurance_for_idc == True:
                                        boe_value = boe_line.y_calculate_value_for_additional + boe_line.y_miscellaneous_value_for_additional
                                        total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                        total_value = (calculate_value * boe_value)/total_boe_line_val
                                        boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': total_value})]
                                        boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + total_value
                                    else:
                                        boe_value = boe_line.y_calculate_value_for_additional
                                        total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                        total_value = (calculate_value * boe_value)/total_boe_line_val
                                        boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': total_value})]
                                        boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + total_value + boe_line.y_miscellaneous_value_for_additional


                                else:
                                    calculate_value = addtional_lines.y_calculated_value
                                    if addtional_lines.y_product_id.product_tmpl_id.y_is_insurance_for_idc == True:
                                        boe_value = boe_line.y_calculate_value_for_additional + boe_line.y_miscellaneous_value_for_additional
                                        total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                        total_value = (calculate_value * boe_value)/total_boe_line_val
                                        boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': total_value})]
                                        boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + total_value 
                                    else:
                                        boe_value = boe_line.y_calculate_value_for_additional                                        
                                        total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                        total_value = (calculate_value * boe_value)/total_boe_line_val
                                        boe_line.y_addtional_quanitity_boe_line_ids = [(0, 0,{'y_product_id': addtional_lines.y_product_id.id,'y_sum_value': total_value})]
                                        boe_line.y_total_assessable_value = boe_line.y_total_assessable_value + total_value + boe_line.y_miscellaneous_value_for_additional
                                # boe_line.y_is_additional_quantity_executed = True


    def execute_miscellaneous_value(self):
        value = self.y_boe_template_line_ids.mapped('y_product_qty')
        if 0.0 in value:
            raise UserError(_("Update Quantity in Boe Lines"))
        else:
            for miscellaneous_lines in self.y_miscellaneous_value_line_ids:
                for boe_line in self.y_boe_template_line_ids:
                    if miscellaneous_lines.y_purchase_id == boe_line.y_purchase_id:
                        if miscellaneous_lines.y_calculated_type == 'percentage':
                            percent_value = self.calculate_percent(miscellaneous_lines.y_calculated_value,boe_line.y_calculate_value_for_additional)
                            boe_line.y_boe_miscellaneous_value_line_ids = [(0, 0,{'y_product_id': miscellaneous_lines.y_product_id.id,'y_sum_value': percent_value})]
                            boe_line.y_miscellaneous_value_for_additional = boe_line.y_miscellaneous_value_for_additional + percent_value

                        if miscellaneous_lines.y_calculated_type == 'value':
                            if miscellaneous_lines.y_currency_id != boe_line.y_boe_template_id.y_company_id.currency_id:
                                calculate_value = miscellaneous_lines.y_calculated_value * miscellaneous_lines.y_currency_excahange_rate
                                boe_value = boe_line.y_calculate_value_for_additional
                                total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                total_value = (calculate_value * boe_value)/total_boe_line_val
                                boe_line.y_boe_miscellaneous_value_line_ids = [(0, 0,{'y_product_id': miscellaneous_lines.y_product_id.id,'y_sum_value': total_value})]
                                boe_line.y_miscellaneous_value_for_additional = boe_line.y_miscellaneous_value_for_additional + total_value

                            else:
                                calculate_value = miscellaneous_lines.y_calculated_value
                                boe_value = boe_line.y_calculate_value_for_additional
                                total_boe_line_val = sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == boe_line.y_purchase_id).mapped('y_calculate_value_for_additional'))
                                total_value = (calculate_value * boe_value)/total_boe_line_val
                                boe_line.y_boe_miscellaneous_value_line_ids = [(0, 0,{'y_product_id': miscellaneous_lines.y_product_id.id,'y_sum_value': total_value})]

                                boe_line.y_miscellaneous_value_for_additional = boe_line.y_miscellaneous_value_for_additional + total_value



    def execute_other_charger(self):
        value = self.y_boe_template_line_ids.mapped('y_product_qty')
        if 0.0 in value:
            raise UserError(_("Update Quantity in Boe Lines"))
        else:
            for other_charges_line in self.y_other_charges_line_ids:
                for boe_line in self.y_boe_template_line_ids:
                    if other_charges_line.y_purchase_id == boe_line.y_purchase_id:

                        if other_charges_line.y_product_id.split_method_landed_cost == 'by_weight':
                            # Filter BOE lines of the same purchase
                            same_purchase_lines = self.y_boe_template_line_ids.filtered(
                                lambda x: x.y_purchase_id == boe_line.y_purchase_id
                            )

                            # Calculate total weight × qty for that purchase
                            total_weight_qty = sum(
                                line.y_product_id.weight * line.y_product_qty
                                for line in same_purchase_lines
                            )

                            # Avoid division by zero
                            if total_weight_qty:
                                value = (
                                    (other_charges_line.y_amount / total_weight_qty)
                                    * (boe_line.y_product_id.weight * boe_line.y_product_qty)
                                )
                            else:
                                value = 0.0

                        else:
                            # Default logic: by quantity
                            total_boe_line_qty = sum(
                                self.y_boe_template_line_ids.filtered(
                                    lambda x: x.y_purchase_id == boe_line.y_purchase_id
                                ).mapped('y_product_qty')
                            )

                            if total_boe_line_qty:
                                value = (other_charges_line.y_amount * boe_line.y_product_qty) / total_boe_line_qty
                            else:
                                value = 0.0

                        # Create record in the One2many
                        boe_line.y_boe_other_charger_line_ids = [(0, 0, {
                            'y_product_id': other_charges_line.y_product_id.id,
                            'y_amount': value,
                        })]


    @api.onchange('y_purchase_boe_bill_id','y_purchase_id')
    def _onchange_sale_auto_complete(self):
        if self.y_purchase_boe_bill_id.y_boe_template_id:
            self.y_boe_template_id = self.y_purchase_boe_bill_id.y_boe_template_id._origin
        elif self.y_purchase_boe_bill_id.y_purchase_order_id:
            self.y_purchase_id = self.y_purchase_boe_bill_id.y_purchase_order_id
        self.y_purchase_boe_bill_id = False

        if not self.y_purchase_id:
            return
        # Copy purchase lines.
        po_lines = self.y_purchase_id.order_line
        new_lines = self.env['boe.template.line']
        import_service_lines = self.env['additional.import.services']
        for line in po_lines.filtered(lambda l: not l.display_type and l.product_id.type != 'service'):
            new_line = new_lines.new(line._prepare_boe_purchase_line(self))
            new_lines += new_line

        for line in po_lines.filtered(lambda l: not l.display_type and l.product_id.type == 'service'):
            new_line = import_service_lines.new(line._prepare_boe_purchase_service_line(self))
            import_service_lines += new_line


        if self.y_boe_template_line_ids:
            self.y_boe_template_line_ids = self.y_boe_template_line_ids + new_lines
        else:
            self.y_boe_template_line_ids = new_lines

        if self.y_additional_import_service_ids:
            self.y_additional_import_service_ids = self.y_additional_import_service_ids + import_service_lines
        else:
            self.y_additional_import_service_ids = import_service_lines
        self.y_partner_id = self.y_purchase_id.partner_id.id
        self.y_warehouse_id = self.y_purchase_id.picking_type_id.warehouse_id.id
        self.y_currency_id = self.y_purchase_id.currency_id.id
        self.y_company_id = self.y_purchase_id.company_id.id
        self.y_country_orgin_goods_id = self.y_purchase_id.y_country_orgin_goods_id.id
        self.y_port_loading_id = self.y_purchase_id.y_port_loading_id.id
        self.y_port_discharge_id = self.y_purchase_id.y_port_discharge_id.id

       

        self.y_incoterm_id = self.y_purchase_id.incoterm_id.id
        boe_currency = self.y_currency_id.name
        start_date = (datetime.now().date())
        end_date = (datetime.now().date())
        company_currency = self.y_purchase_id.company_id.currency_id.name

        if len(self.y_picking_ids) == 1:
            self.y_picking_ids = [(4, self.y_purchase_id.picking_ids.filtered(lambda x:x.state=='assigned').id)] 
        else:
            self.y_picking_ids = self.y_purchase_id.picking_ids.filtered(lambda x:x.state=='assigned').ids

        if self.y_purchase_order_ids:
            self.y_purchase_order_ids = [(4, self.y_purchase_id.id)]  
        else:
            self.y_purchase_order_ids = self.y_purchase_id.ids
        self.y_purchase_id = False

    @api.depends('y_boe_template_line_ids.y_price_subtotal','y_boe_template_line_ids.y_total_assessable_value')
    def compute_total_assessable_value(self):
        for rec in self:
            rec.y_total_assessable_value = sum(rec.y_boe_template_line_ids.mapped('y_price_subtotal'))
            total_assessable_value = 0
            if rec.y_duties_exempted:
                if rec.y_company_id.y_is_export_oriented_unit:
                    for import_lines in rec.y_boe_template_line_ids:
                        total_assessable_value = total_assessable_value + sum(import_lines.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value')) + sum(import_lines.y_boe_miscellaneous_value_line_ids.mapped('y_sum_value'))
                else:
                    for import_lines in rec.y_boe_template_line_ids:
                        total_assessable_value = total_assessable_value 
            # else:
            #     for import_lines in rec.y_boe_template_line_ids:
            #         total_assessable_value = total_assessable_value + sum(import_lines.y_boe_miscellaneous_value_line_ids.mapped('y_sum_value'))


            total_assessable_value = total_assessable_value + sum(rec.y_boe_template_line_ids.mapped('y_total_assessable_value'))
            rec.y_total_assessable_value_lcy =  total_assessable_value


    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        for vals in vals_list:
            if not vals.get('y_purchase_order_ids'):
                raise UserError("Purchase Order Required to Create Bill Of Entry.")

        moves = super().create(vals_list)
        for move in moves:
            purchase = move.y_purchase_id
            if not purchase:
                continue
            refs = ["<a href=# data-oe-model=purchase.order data-oe-id=%s>%s</a>" % tuple(name_get) for name_get in purchase.name_get()]
            message = _("This BOE has been created from: %s") % ','.join(refs)
            move.message_post(body=message)
        return moves

    def button_confirm(self):
        if self.env.user.has_group('import_duty_autocalculation.group_action_confirm'):

            value = self.y_boe_template_line_ids.mapped('y_product_qty')
            if 0.0 in value:
                raise UserError(_("Quantity is not mapped"))

            for po_line in self.y_boe_template_line_ids.mapped('y_purchase_id'):
                self.y_po_total_accessable_value_line_ids = [(0, 0,{'y_purchase_id':po_line.id,'y_total_assessable_value':sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == po_line).mapped('y_price_subtotal')),'y_total_assessable_value_lcy': sum(self.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == po_line).mapped('y_total_assessable_value'))})]
            for rec in self:
                if not rec.y_bill_of_entry_rate:
                    raise UserError(_("Please Maintain Exchange Rate"))

                boe_sequence_id = rec.y_company_id.y_bill_of_entry_sequence_id
                if rec.y_company_id.sudo().parent_id:
                    boe_sequence_id = rec.y_company_id.sudo().parent_id.y_bill_of_entry_sequence_id
                if not boe_sequence_id:
                    raise UserError("Kindly! Configure the BOE Sequence")
               
                rec.y_bill_of_entry_code = boe_sequence_id.next_by_id()
                for boe_line in rec.y_boe_template_line_ids:
                    if boe_line.y_import_duty_structure_id and  not boe_line.y_is_excecute_clicked:
                        raise UserError("Kindly execute import duty structure for {}".format(boe_line.y_product_id.name))

                #update boe quantity to stock move
                for boe_lines in rec.y_boe_template_line_ids:
                    move_quantity = boe_lines.y_product_qty
                    move = boe_lines.y_purchase_line_id.move_ids.filtered(lambda x:x.state not in ('done','cancel'))
                    if move.product_uom != boe_lines.y_purchase_line_id.product_uom:
                        move_quantity = move.purchase_line_id.product_uom._compute_quantity(boe_lines.y_product_qty,move.product_uom)

                    boe_lines.y_purchase_line_id.move_ids.filtered(lambda x:x.state not in ('done','cancel')).quantity = move_quantity
                    boe_lines.y_purchase_line_id.move_ids.filtered(lambda x:x.state not in ('done','cancel')).y_boe_template_line_id = boe_lines.id

                rec.write({'y_state':'confirm'})
                for picking in rec.y_picking_ids:
                    picking.y_boe_template_id = rec.id
                    if picking.company_id:
                        company_id = picking.company_id
                        if picking.company_id.sudo().parent_id:
                            company_id = picking.company_id.sudo().parent_id
                        valuation_based_on = company_id.y_valuation_based_on
                        if valuation_based_on == 'boerate':
                            if picking.y_boe_template_id:
                                picking.y_valuation_exchange_rate = picking.y_boe_template_id.y_bill_of_entry_rate

        else:
            raise UserError(_("You are Not Authorised"))



#Main Boe Lines
class BoeMaster(models.Model):
    _name = "boe.template.line"

    y_import_duty_structure_id = fields.Many2one('import.duty.structure',string="Import Duty Structure")
    y_product_id = fields.Many2one('product.product',string="Product")

    y_ordered_quantity = fields.Float(string="Ordered Quantity")
    y_product_qty = fields.Float('Quantity')
    y_price_unit = fields.Float(string="Unit Price")
    y_currency_id = fields.Many2one('res.currency',string="Currency Code")
    y_is_arrow_clicked = fields.Boolean()
    y_is_additional_quantity_executed = fields.Boolean(string="Is additional quantity executed")
    y_is_foc = fields.Boolean(string="FOC")
    y_is_excecute_clicked = fields.Boolean()
    y_duties_exempted = fields.Boolean(string="Duties Exempted")
    y_exim_notification = fields.Char(string="Exim Notification")
    y_price_subtotal = fields.Monetary(currency_field='y_currency_id',string='Subtotal',compute="calculate_price_subtotal")
    y_total_assessable_value = fields.Float(string="Total Assessable Value")
    y_total_calculated_assessable_value = fields.Float(string="Service Charges as per PO")
    y_with_service_value_included = fields.Float(string="Basic Assessable Value")
    y_calculate_value_for_additional = fields.Float(string="Calculated Assessable Value")
    y_miscellaneous_value_for_additional = fields.Float(string="Miscellaneous Assessable Value")
    y_boe_template_id = fields.Many2one('boe.template')
    y_company_id = fields.Many2one('res.company',string="Company",readonly=True,related="y_boe_template_id.y_company_id")

    y_purchase_line_id = fields.Many2one('purchase.order.line',string="Purchase Line")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_import_duty_structure_boe_ids = fields.One2many('import.duty.structure','y_boe_import_duty_structure_id',copy=False)
    y_import_duty_structure_line_boe_ids = fields.One2many('import.duty.structure.line','y_boe_import_duty_structure_line_id',copy=False,string="Import Duty Structure Line")
    y_addtional_quanitity_boe_line_ids = fields.One2many('additional.quantity.lines','y_addtional_quanitity_boe_line_id',copy=False,string="Additional Quantity")
    y_addtional_import_services_line_ids = fields.One2many('additional.import.services','y_addtional_import_service_line_id',copy=False)
    y_service_import_report_line_ids = fields.One2many('service.data.imports','y_service_boe_line_id',copy=False,string="Service Imports")
    y_boe_miscellaneous_value_line_ids = fields.One2many('boe.miscellaneous.value.line','y_miscellaneous_value_boe_line_id',copy=False,string="Miscellaneous Quantity")
    y_duty_payable = fields.Float(string="Duty Payable",compute="_compute_totoal_assesable_value")
    y_boe_other_charger_line_ids = fields.One2many('boe.line.other.chargers','y_boe_template_line_id',copy=False,string="BOE Other Charges Lines")


    

    @api.depends('y_import_duty_structure_line_boe_ids.y_assesable_value')
    def _compute_totoal_assesable_value(self):
        for rec in self:
            rec.y_duty_payable = sum(rec.y_import_duty_structure_line_boe_ids.mapped('y_assesable_value'))


    def check_order_quantity_exceeds(self):
        for line in self:
            if line.y_product_qty > line.y_ordered_quantity:
                raise UserError(_('The quantity exceeds the ordered quantity.'))

    @api.constrains('y_ordered_quantity', 'y_product_qty')
    def _check_ordered_quantity(self):
        for line in self:
            if line.y_product_id.y_purchase_tol_reqd == True:
                if (line.y_product_qty - line.y_ordered_quantity) > ((line.y_ordered_quantity / 100) * line.y_product_id.y_purchase_tolerance):
                    raise UserError(_('The received quantity for {} exceeds the allowed tolerance of {} % over the ordered quantity.'.format(line.y_product_id.name, line.y_product_id.y_purchase_tolerance)))
            else:
                line.check_order_quantity_exceeds()

    @api.depends('y_product_qty','y_price_unit')
    def calculate_price_subtotal(self):
        for rec in self:
            if rec.y_product_qty:
                rec.y_price_subtotal = rec.y_product_qty * rec.y_price_unit
            else:
                rec.y_price_subtotal = 0

    @api.onchange('y_calculate_value_for_additional',)
    def calculate_value(self):
        for rec in self:
            rec.y_total_assessable_value = rec.y_calculate_value_for_additional



    def execute_all_action_show_details(self):
        import_obj = self.y_import_duty_structure_id
        if not import_obj:
            raise UserError("Please maintain Import Duty Structure for {}".format(self.y_product_id.name))

        if not self.y_is_arrow_clicked:
            for import_lines in import_obj.y_import_duty_structure_ids:
                self.y_import_duty_structure_line_boe_ids = [(0, 0,{'y_duties_exempted':self.y_duties_exempted,
                                                                    'y_import_duty_structure_master_id':import_lines.y_import_duty_structure_master_id.id,
                                                                    'y_description':import_lines.y_description,
                                                                    'y_calculated_on':import_lines.y_calculated_on,
                                                                    'y_product_id':self.y_product_id.id,
                                                                    'y_duty_type_id': import_lines.y_duty_type_id.id,
                                                                    'y_calculated_value': import_lines.y_calculated_value,
                                                                    'y_calculation_type':import_lines.y_calculation_type,
                                                                    'y_product_exp_account_id':import_lines.y_product_exp_account_id.id,
                                                                    'y_taxes_ids':import_lines.y_import_duty_structure_master_id.y_taxes_ids.ids,
                                                                    'y_base_formula':import_lines.y_base_formula})]
                self.y_is_arrow_clicked = True

            #creation service imports for report
            if self.y_boe_template_id.y_additional_import_service_ids:
                for import_lines in self.y_boe_template_id.y_additional_import_service_ids:
                    if import_lines.y_purchase_id == self.y_purchase_id:
                        without_service_total = sum(self.y_boe_template_id.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == import_lines.y_purchase_id).mapped('y_with_service_value_included'))
                        sum_value = (import_lines.y_price_subtotal*self.y_with_service_value_included)/without_service_total
                        self.y_service_import_report_line_ids = [(0, 0,{'y_service_boe_line_id':self.id,'y_product_id':import_lines.y_product_id.id,'y_sum_value': sum_value})]
                        self.y_is_arrow_clicked = True



    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref('import_duty_autocalculation.boe_template_line_button_form')
        # import_obj = self.env['import.duty.structure'].browse(self.product_id.product_tmpl_id.import_duty_structure_id.id)
        import_obj = self.y_import_duty_structure_id

        if not import_obj:
            raise UserError("Please maintain Import Duty Structure for {}".format(self.y_product_id.name))

        if not self.y_is_arrow_clicked:
            for import_lines in import_obj.y_import_duty_structure_ids:
                self.y_import_duty_structure_line_boe_ids = [(0, 0,{'y_duties_exempted':self.y_duties_exempted,
                                                                    'y_import_duty_structure_master_id':import_lines.y_import_duty_structure_master_id.id,
                                                                    'y_description':import_lines.y_description,
                                                                    'y_calculated_on':import_lines.y_calculated_on,
                                                                    'y_product_id':self.y_product_id.id,
                                                                    'y_duty_type_id': import_lines.y_duty_type_id.id,
                                                                    'y_calculated_value': import_lines.y_calculated_value,
                                                                    'y_calculation_type':import_lines.y_calculation_type,
                                                                    'y_product_exp_account_id':import_lines.y_product_exp_account_id.id,
                                                                    'y_taxes_ids':import_lines.y_import_duty_structure_master_id.y_taxes_ids.ids,
                                                                    'y_base_formula':import_lines.y_base_formula})]
                self.y_is_arrow_clicked = True

            #creation service imports for report
            if self.y_boe_template_id.y_additional_import_service_ids:
                for import_lines in self.y_boe_template_id.y_additional_import_service_ids:
                    if import_lines.y_purchase_id == self.y_purchase_id:
                        without_service_total = sum(self.y_boe_template_id.y_boe_template_line_ids.filtered(lambda x:x.y_purchase_id == import_lines.y_purchase_id).mapped('y_with_service_value_included'))
                        sum_value = (import_lines.y_price_subtotal*self.y_with_service_value_included)/without_service_total
                        self.y_service_import_report_line_ids = [(0, 0,{'y_service_boe_line_id':self.id,'y_product_id':import_lines.y_product_id.id,'y_sum_value': sum_value})]
                        self.y_is_arrow_clicked = True



                
        return {
            'name': _('Import Duty Structure'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'boe.template.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'domain': [('id', '=', self.id)],
            'context':self.env.context,
        }

    def calculate_percent(self,percentage,value):
        percentage_value = percentage/100
        return (percentage_value*value)

    def button_execute(self):
        if self.y_boe_template_id.y_is_execute_all_clicked == False:
            if not self.y_is_excecute_clicked:
                if self.y_duties_exempted:
                    for rec in self:
                        if rec.y_boe_template_id.y_bill_of_entry_rate:
                            rec.y_with_service_value_included = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate)
                            rec.y_total_assessable_value = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate)

                    for rec in self:
                        service_total = sum(rec.y_boe_template_id.y_additional_import_service_ids.mapped('y_with_service_value_included'))
                        without_service_total = sum(rec.y_boe_template_id.y_boe_template_line_ids.mapped('y_with_service_value_included'))
                        if without_service_total:
                            rec.y_total_calculated_assessable_value = (service_total*rec.y_with_service_value_included)/without_service_total
                        else:
                            rec.y_total_calculated_assessable_value = 0


                        rec.y_calculate_value_for_additional = rec.y_total_calculated_assessable_value + rec.y_with_service_value_included
                        # rec.miscellaneous_value_for_additional = rec.y_with_service_value_included + rec.y_total_calculated_assessable_value
                        rec.y_total_assessable_value = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate) + rec.y_total_calculated_assessable_value


                    for line in self.y_import_duty_structure_line_boe_ids.filtered(lambda x:not x.y_duty_type_id ):
                        if not line.y_base_formula:
                            if line.y_calculation_type == 'percentage':
                                # if self.y_company_id.y_is_export_oriented_unit:
                                #     y_total_assessable_value = self.y_total_assessable_value + sum(self.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value')) + sum(self.y_boe_miscellaneous_value_line_ids.mapped('y_sum_value'))
                                # else:
                                y_total_assessable_value = self.y_total_assessable_value 

                                line.y_assesable_value = self.calculate_percent(line.y_calculated_value,y_total_assessable_value)
                            else:
                                line.y_assesable_value = line.y_calculated_value 
                        else:
                            
                            if line.y_calculated_on == 'assessable':
                                line.y_assesable_value = line.y_calculated_value
                            elif line.y_calculated_on == 'formula':
                                duty_id = self.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_import_duty_structure_master_id.y_name == line.y_base_formula)
                                if duty_id:
                                    line.y_assesable_value = self.calculate_percent(duty_id.y_assesable_value,line.y_calculated_value)                                
                            elif line.y_calculated_on == 'assessable_formula':
                                str_obj = tuple(line.y_base_formula.split())
                                duty_ids = self.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_import_duty_structure_master_id.y_name in str_obj)
                                if duty_ids:
                                    total_assessable_value = sum(duty_ids.mapped('y_assesable_value')) + self.y_total_assessable_value + sum(self.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value'))
                                    line.y_assesable_value = self.calculate_percent(total_assessable_value,line.y_calculated_value)
                            else:
                                line.y_assesable_value = line.y_calculated_value

                else:
                    for rec in self:
                        if rec.y_boe_template_id.y_bill_of_entry_rate:
                            rec.y_with_service_value_included = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate)
                            rec.y_total_assessable_value = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate)

                    for rec in self:
                        service_total = sum(rec.y_boe_template_id.y_additional_import_service_ids.mapped('y_with_service_value_included'))
                        without_service_total = sum(rec.y_boe_template_id.y_boe_template_line_ids.mapped('y_with_service_value_included'))
                        rec.y_total_calculated_assessable_value = (service_total*rec.y_with_service_value_included)/without_service_total
                        rec.y_calculate_value_for_additional = rec.y_total_calculated_assessable_value + rec.y_with_service_value_included
                        # rec.miscellaneous_value_for_additional = rec.y_with_service_value_included + rec.y_total_calculated_assessable_value
                        rec.y_total_assessable_value = (rec.y_price_subtotal * rec.y_boe_template_id.y_bill_of_entry_rate) + rec.y_total_calculated_assessable_value
                    for line in self.y_import_duty_structure_line_boe_ids:

                        if not line.y_base_formula:
                            if line.y_calculation_type == 'percentage':
                                y_total_assessable_value = self.y_total_assessable_value + sum(self.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value')) + sum(self.y_boe_miscellaneous_value_line_ids.mapped('y_sum_value'))
                                line.y_assesable_value = self.calculate_percent(line.y_calculated_value,y_total_assessable_value)
                            else:
                                line.y_assesable_value = line.y_calculated_value
                        else:
                            
                            if line.y_calculated_on == 'assessable':
                                line.y_assesable_value = line.y_calculated_value
                            elif line.y_calculated_on == 'formula':
                                duty_id = self.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_import_duty_structure_master_id.y_name == line.y_base_formula)
                                if duty_id:
                                    line.y_assesable_value = self.calculate_percent(duty_id.y_assesable_value,line.y_calculated_value)                                
                            elif line.y_calculated_on == 'assessable_formula':
                                str_obj = tuple(line.y_base_formula.split())
                                duty_ids = self.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_import_duty_structure_master_id.y_name in str_obj)
                                if duty_ids:
                                    total_assessable_value = sum(duty_ids.mapped('y_assesable_value')) + self.y_total_assessable_value + sum(self.y_addtional_quanitity_boe_line_ids.mapped('y_sum_value'))
                                    line.y_assesable_value = self.calculate_percent(total_assessable_value,line.y_calculated_value)
                            else:
                                line.y_assesable_value = line.y_calculated_value
                

                structure_line = 1
                for line in self.y_import_duty_structure_line_boe_ids:
                    self.y_boe_template_id.y_import_duty_boe_line_ids = [(0, 0,{'y_import_duty_structure_line_serial_no':structure_line,
                                                                                'y_import_duty_structure_master_id':line.y_import_duty_structure_master_id.id,
                                                                                'y_description':line.y_description,
                                                                                'y_calculated_on':line.y_calculated_on,
                                                                                'y_product_id':line.y_product_id.id,
                                                                                'y_purchase_id':self.y_purchase_id.id,
                                                                                'y_purchase_line_id':self.y_purchase_line_id.id,
                                                                                'y_duty_type_id': line.y_duty_type_id.id,
                                                                                'y_assesable_value': line.y_assesable_value,
                                                                                'y_taxes_ids':line.y_import_duty_structure_master_id.y_taxes_ids.ids,
                                                                                'y_duties_exempted':line.y_duties_exempted,
                                                                                'y_base_formula':line.y_base_formula,})]
                    structure_line = structure_line + 1
                self.y_is_excecute_clicked = True


class OtherCharges(models.Model):
    _name ="other.chargers"
    _description = "Other Charges"

    y_product_id = fields.Many2one('product.product',string="Product")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")

    y_name = fields.Char(string="Description",related="y_product_id.name")
    y_amount = fields.Float(string="Amount")
    y_boe_template_id = fields.Many2one('boe.template', string='Boe Template', readonly=True)
    y_company_id = fields.Many2one('res.company', 'Company', readonly=True,related="y_boe_template_id.y_company_id")
    y_currency_id = fields.Many2one('res.currency',string="Currency",default=lambda self: self.env.company.currency_id.id)





class BOELineOtherCharges(models.Model):
    _name ="boe.line.other.chargers"
    _description = "BOE line Other Charges"


    y_product_id = fields.Many2one('product.product',string="Product")
    y_amount = fields.Float(string="Amount")
    y_boe_template_line_id = fields.Many2one('boe.template.line', string='Boe Template Line')
    y_company_id = fields.Many2one('res.company', 'Company', related="y_boe_template_line_id.y_company_id")
    y_currency_id = fields.Many2one('res.currency',string="Currency",default=lambda self: self.env.company.currency_id.id)













class PurchaseOrderNews(models.Model):
    _inherit = "purchase.order"

    y_boe_id = fields.Many2one('boe.template')
    y_is_same_country = fields.Boolean(string="Is Same Country",copy=False)
    y_picking_state = fields.Selection(related="picking_ids.state", copy=False)


    @api.depends('name', 'partner_ref', 'amount_total', 'currency_id')
    @api.depends_context('show_total_amount')
    def _compute_display_name(self):
        for po in self:
            name = po.name
            # if po.partner_ref:
            #     name += ' (' + po.partner_ref + ')'
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total, currency_obj=po.currency_id)
            po.display_name = name

    def button_confirm(self):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.country_id != rec.company_id.country_id and rec.partner_id.y_is_boe:
                    rec.y_is_same_country = True
                else:
                    rec.y_is_same_country = False

        return super().button_confirm()

    def button_approve(self,force=False):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.country_id != rec.company_id.country_id and rec.partner_id.y_is_boe:
                    rec.y_is_same_country = True
                else:
                    rec.y_is_same_country = False
        return super(PurchaseOrderNews, self).button_approve(force)


class PurchaseBoeBill(models.Model):
    _name = "purchase.boe.bill"
    _auto = False
    _description = 'Purchases & Boe Union'
   
    y_partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    y_currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    y_company_id = fields.Many2one('res.company', 'Company', readonly=True,default=lambda self: self.env.company.id)
    y_boe_template_id = fields.Many2one('"boe.template', string='Boe Template', readonly=True)
    y_purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)

    def init(self):
        print(22222222222222222222222222222222222222222222)
        tools.drop_view_if_exists(self.env.cr, 'purchase_boe_bill')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW purchase_boe_bill AS (
                SELECT
                    id,y_partner_id,  y_currency_id,y_company_id,
                    id as y_boe_template_id, NULL as y_purchase_order_id
                FROM boe_template
                WHERE
                    y_state = 'confirm'  
            UNION
                SELECT
                    id,partner_id, currency_id,company_id,
                    NULL as y_boe_template_id, id as y_purchase_order_id
                FROM purchase_order
                WHERE
                    state in ('done') AND
                    invoice_status in ('no','to invoice') AND
                    y_is_same_country = True
            )""")

       
    def name_get(self):
        result = []
        for doc in self:
            if doc.y_purchase_order_id:
                result.append((doc.y_purchase_order_id.id,doc.y_purchase_order_id.name))
        return result

class ImportDutyStructureMaster(models.Model):
    _name = 'import.duty.structure.master'
    _rec_name = 'y_name'
    _description = "Import Duty Structure Master"

    y_name = fields.Char(string="Code")
    y_description = fields.Char(string="Description")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_taxes_ids = fields.Many2many('account.tax',string="Taxes")


class ImportDutyStructure(models.Model):
    _name = "import.duty.structure"
    _rec_name="y_name"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Import Duty Structure"

    y_name = fields.Char(string="Name")
    y_start_date = fields.Date(string="Start Date")
    y_end_date = fields.Date(string="End Date")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id,readonly=True)
    y_active_toggle = fields.Boolean(default=False,string="Active")
    y_assesable_value = fields.Float(string="Assessable Value")
    y_boe_import_duty_structure_id = fields.Many2one('boe.template.line')
    y_boe_template_strucure_id = fields.Many2one('boe.template') 
    y_import_duty_structure_ids = fields.One2many('import.duty.structure.line','y_import_duty_structure_id',string="Import Duty Structure Line",copy=False)


class ImportDutyStructureLine(models.Model):
    _name = "import.duty.structure.line"
    _description = "Import Duty Structure Line"

    y_import_duty_structure_id = fields.Many2one('import.duty.structure',string="Import Duty Structure")
    y_boe_template_id = fields.Many2one('boe.template')
    y_boe_import_duty_structure_line_id = fields.Many2one('boe.template.line')
    y_import_duty_structure_master_id = fields.Many2one('import.duty.structure.master',string="Duties")
    y_description = fields.Char(string="Description")
    y_product_id = fields.Many2one('product.product',string="Service Item")
    y_import_duty_structure_line_serial_no = fields.Integer(string='#',compute='_compute_import_sl')
    y_serial_no = fields.Char(string='#',compute='_compute_sl')
    y_duty_type_id = fields.Many2one('product.product',string="Service Item")
    y_calculation_type = fields.Selection([('percentage','Percentage'),('fixedvalue','Fixed Value')], string='Calculation Type', copy=False)
    y_calculated_value = fields.Float(string="Calculated Value")
    y_assesable_value = fields.Float(string="Amount")
    y_duties_exempted = fields.Boolean(string="Duties Exempted")
    y_base_formula = fields.Char(string="Base Formula")
    y_product_exp_account_id = fields.Many2one(related="y_duty_type_id.property_account_expense_id")
    y_taxes_ids = fields.Many2many('account.tax',string="Taxes")
    y_purchase_line_id = fields.Many2one('purchase.order.line',string="Purchase Line")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_calculated_on = fields.Selection([('assessable','Assessable Value'),('formula','Formula'),('assessable_formula','Assessable + Formula')],string="Calculated On")

    @api.onchange('y_import_duty_structure_master_id')
    def _onchange_import_duty_structure_master_id(self):
        for line in self:
            if line.y_import_duty_structure_master_id.y_product_id:
                line.y_duty_type_id = line.y_import_duty_structure_master_id.y_product_id.id
                line.y_description = line.y_import_duty_structure_master_id.y_description
            else:
                line.y_taxes_ids = [(6,0,line.y_import_duty_structure_master_id.y_taxes_ids.ids)]
                line.y_description = line.y_import_duty_structure_master_id.y_description
                line.y_calculated_value = sum(line.y_import_duty_structure_master_id.y_taxes_ids.mapped('amount'))


    @api.depends('y_boe_template_id')
    def _compute_import_sl(self):
        if self.y_boe_template_id:
            for order in self.mapped('y_boe_template_id'):
                number=1
                for line in order.y_import_duty_boe_line_ids:
                    if line.y_duty_type_id:
                        line.y_import_duty_structure_line_serial_no = number
                        number += 1
                    else:
                        line.y_import_duty_structure_line_serial_no = number
        else:
            self.y_import_duty_structure_line_serial_no = ''



    @api.depends('y_boe_import_duty_structure_line_id')
    def _compute_sl(self):
        if self.y_boe_import_duty_structure_line_id:
            for order in self.mapped('y_boe_import_duty_structure_line_id'):
                number=1
                for line in order.y_import_duty_structure_line_boe_ids:
                    if line.y_duty_type_id:
                        line.y_serial_no = str(number)
                        number += 1
                    else:
                        line.y_serial_no = str(number)
        else:
            self.y_serial_no = ''


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_boe_purchase_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.y_currency_id or self.currency_id
        date = move and move.y_date or fields.Date.today()
        res = {
            'y_product_id': self.product_id.id,
            'y_ordered_quantity':self.product_qty,
            'y_product_qty':0.0,
            'y_import_duty_structure_id':self.product_id.product_tmpl_id.y_import_duty_structure_id.id,
            'y_purchase_line_id':self.id,
            'y_purchase_id':self.order_id.id,
            'y_price_unit':self.price_unit,
            # 'price_subtotal':self.price_subtotal
            'y_price_subtotal':0.0
        }
        return res

    def _prepare_boe_purchase_service_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.y_currency_id or self.currency_id
        date = move and move.y_date or fields.Date.today()
        res = {
            'y_product_id': self.product_id.id,
            'y_product_qty':self.product_qty,
            'y_purchase_line_id':self.id,
            'y_purchase_id':self.order_id.id,
            'y_price_unit':self.price_unit,
            'y_price_subtotal':self.price_subtotal
        }
        
        return res 

            
class ProductProductnew(models.Model):
    _inherit = "product.product"

    y_import_duty_structure_id = fields.Many2one('import.duty.structure',string="Import Duty Structure")


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        res = super().process()
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(skip_backorder=True)
            pickings_to_validate.importduty_validate()
        return res
       
    def process_cancel_backorder(self):
        res = super().process_cancel_backorder()

        pickings_to_validate_ids = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate_ids:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate_ids)
            pickings_to_validate.importduty_validate()
        return res

    

class StockPicking(models.Model):
    _inherit = "stock.picking"

    y_boe_template_id = fields.Many2one('boe.template',string="BOE",copy=False)
    y_is_boe_done = fields.Boolean()
    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('purchase_id','purchase_id.currency_id','company_id')
    def check_same_currency(self):
        for rec in self:
            if rec.purchase_id and rec.purchase_id.currency_id != rec.company_id.currency_id:
                rec.write({'y_is_same_currency':True})
            else:
                rec.write({'y_is_same_currency':False})



    def button_validate(self):
        for rec in self:
            if rec.purchase_id and not rec.y_boe_template_id:
                is_boe = rec.partner_id.with_company(rec.company_id).y_is_boe
                if not is_boe and rec.company_id.sudo().parent_id:
                    is_boe = rec.partner_id.sudo().with_company(rec.company_id.sudo().parent_id).y_is_boe
                if is_boe:
                    raise UserError(_("Please create the BOE before validating the GRN."))

        result = super(StockPicking,self).button_validate()

        for picking in self:
            if picking.y_boe_template_id:
                pickings_to_backorder = picking._check_backorder()
                if not pickings_to_backorder:
                    picking.importduty_validate()

        return result


    def importduty_validate(self):
        if self.y_is_boe_done == False:
            number_of_landedcost = 0
            for rec in self.y_boe_template_id:  
                for move_line in self.move_ids_without_package:
                    line = self.env['boe.template.line'].search([('y_boe_template_id','=',self.y_boe_template_id.id),('y_purchase_line_id','=',move_line.purchase_line_id.id),('y_boe_template_id.y_state','=','confirm')],limit=1)
                    
                    if move_line.product_uom != line.y_purchase_line_id.product_uom:
                        move_quantity = line.y_purchase_line_id.product_uom._compute_quantity(line.y_product_qty,move_line.product_uom)
                    else:
                        move_quantity = line.y_product_qty
                    if not line.y_duties_exempted:
                        boe_val_list = []
                        for po_line in line.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_duty_type_id):

                            y_assesable_value = (po_line.y_assesable_value * move_line.quantity)/move_quantity

                            boe_val_list.append({
                                'product_id':po_line.y_duty_type_id.id,
                                'name':po_line.y_duty_type_id.name,
                                'account_id':po_line.y_product_exp_account_id.id,
                                'split_method':po_line.y_duty_type_id.split_method_landed_cost,
                                # 'split_method':'by_current_cost_price',
                                'price_unit': round(y_assesable_value),
                            }) 

                        for other_charges_lines in line.y_boe_other_charger_line_ids:
                            amount = (other_charges_lines.y_amount * move_line.quantity)/move_quantity
                            boe_val_list.append({
                                'product_id':other_charges_lines.y_product_id.id,
                                'name':other_charges_lines.y_product_id.name,
                                'account_id':other_charges_lines.y_product_id.property_account_expense_id.id,
                                'split_method':other_charges_lines.y_product_id.split_method_landed_cost,
                                # 'split_method':'by_current_cost_price',
                                'price_unit': round(amount),
                            })

                        
                        if rec.y_incoterm_id.y_included_landed_cost:
                            for additional_charges_lines in line.y_addtional_quanitity_boe_line_ids:
                                y_sum_value = (additional_charges_lines.y_sum_value * move_line.quantity)/move_quantity

                                boe_val_list.append({
                                    'product_id':additional_charges_lines.y_product_id.id,
                                    'name':additional_charges_lines.y_product_id.name,
                                    'account_id':additional_charges_lines.y_product_id.property_account_expense_id.id,
                                    'split_method':additional_charges_lines.y_product_id.split_method_landed_cost,
                                    # 'split_method':'by_current_cost_price',
                                    'price_unit':round(y_sum_value),
                                }) 

                        for mis_charges_lines in line.y_boe_miscellaneous_value_line_ids:
                            y_sum_value = (mis_charges_lines.y_sum_value * move_line.quantity)/move_quantity
                            boe_val_list.append({
                                'product_id':mis_charges_lines.y_product_id.id,
                                'name':mis_charges_lines.y_product_id.name,
                                'account_id':mis_charges_lines.y_product_id.property_account_expense_id.id,
                                'split_method':mis_charges_lines.y_product_id.split_method_landed_cost,
                                # 'split_method':'by_current_cost_price',
                                'price_unit':round(y_sum_value),
                            })
                        _logger.info("Landed Cost Lines Details %s", boe_val_list)

                        if boe_val_list:
                            mr_id = self.env['stock.landed.cost'].create({
                            'picking_ids' :self.ids,
                            'y_boe_ids' :self.y_boe_template_id.ids,
                            'company_id':rec.y_company_id.id,
                            'cost_lines' : [(0, 0, line_vals) for line_vals in boe_val_list]

                            })

                            mr_id.compute_landed_cost()

                            for lines in mr_id.valuation_adjustment_lines:
                                if move_line.id != lines.move_id.id:
                                    lines.unlink()
                                else:
                                    lines.additional_landed_cost = lines.cost_line_id.price_unit



                            mr_id.button_validate()
                            number_of_landedcost = number_of_landedcost + 1
                    else:
                        boe_val_list = []
                        for other_charges_lines in line.y_boe_other_charger_line_ids:
                            amount = (other_charges_lines.y_amount * move_line.quantity)/move_quantity
                            boe_val_list.append({
                                'product_id':other_charges_lines.y_product_id.id,
                                'name':other_charges_lines.y_product_id.name,
                                'account_id':other_charges_lines.y_product_id.property_account_expense_id.id,
                                'split_method':other_charges_lines.y_product_id.split_method_landed_cost,
                                # 'split_method':'by_current_cost_price',
                                'price_unit':round(amount),
                            })
                        _logger.info("Landed Cost Lines Details %s", boe_val_list)

                        if boe_val_list:

                            mr_id = self.env['stock.landed.cost'].create({
                            'picking_ids' :self.ids,
                            'y_boe_ids' :self.y_boe_template_id.ids,

                            'company_id':rec.y_company_id.id,
                            'cost_lines' : [(0, 0, line_vals) for line_vals in boe_val_list]

                            })

                            mr_id.compute_landed_cost()

                            for lines in mr_id.valuation_adjustment_lines:
                                if move_line.id != lines.move_id.id:
                                    lines.unlink()
                                else:
                                    lines.additional_landed_cost = lines.cost_line_id.price_unit


                            mr_id.button_validate()
                            number_of_landedcost = number_of_landedcost + 1

                # bill_val_list = []
                # for boe_lines in rec.y_boe_template_line_ids:
                #     if not boe_lines.y_duties_exempted:
                #         taxes_ids = boe_lines.y_import_duty_structure_line_boe_ids.mapped('y_taxes_ids').ids
                #         #import dut strcuture line
                #         for import_lines in boe_lines.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_duty_type_id):
                #             bill_val_list.append({
                #                 'product_id':import_lines.y_duty_type_id.id,
                #                 'account_id':import_lines.y_duty_type_id.property_account_expense_id.id,
                #                 'price_unit':import_lines.y_assesable_value,
                #                 'tax_ids':taxes_ids,
                #                 })

                #         #additional lines
                #         for additional_lines in boe_lines.y_addtional_quanitity_boe_line_ids:
                #             bill_val_list.append({
                #                 'product_id':additional_lines.y_product_id.id,
                #                 'account_id':additional_lines.y_product_id.property_account_expense_id.id,
                #                 'price_unit':additional_lines.y_sum_value,
                #                 'tax_ids':taxes_ids,

                #                 })


                #         #service lines
                #         for service_lines in boe_lines.y_service_import_report_line_ids:
                #             bill_val_list.append({
                #                 'product_id':service_lines.y_product_id.id,
                #                 'account_id':service_lines.y_product_id.property_account_expense_id.id,
                #                 'price_unit':service_lines.y_sum_value,
                #                 'tax_ids':taxes_ids,

                #                 })



                #         for mis_lines in boe_lines.y_boe_miscellaneous_value_line_ids:
                #             bill_val_list.append({
                #                 'product_id':mis_lines.y_product_id.id,
                #                 'account_id':mis_lines.y_product_id.property_account_expense_id.id,
                #                 'price_unit':mis_lines.y_sum_value,
                #                 'tax_ids':taxes_ids,

                #                 })

                #     else:
                #         #import duty strcuture line
                #         for import_lines in boe_lines.y_import_duty_structure_line_boe_ids.filtered(lambda x:not x.y_duty_type_id):
                #             account = False
                #             if boe_lines.y_import_duty_structure_id.y_import_duty_structure_ids:
                #                 account = boe_lines.y_import_duty_structure_id.y_import_duty_structure_ids[0].y_product_exp_account_id.id
                #             if not account:
                #                 raise ValidationError(_("Please map expense account for import duty strcuture lines"))
                #             total_assessable_value = boe_lines.y_total_assessable_value
                #             bill_val_list.append({
                #                 'account_id':account,
                #                 'price_unit':total_assessable_value,
                #                 'tax_ids':import_lines.y_taxes_ids.ids,

                #                 })

                #             bill_val_list.append({
                #                 'account_id':account,
                #                 'price_unit':-total_assessable_value,
                #                 })


                # account_move_id = self.env['account.move'].create({
                # 'move_type': 'in_invoice',
                # 'company_id':rec.y_company_id.id,
                # 'partner_id':rec.y_duty_to_pay_vendor_id.id,
                # 'invoice_line_ids' : [(0, 0, line_vals) for line_vals in bill_val_list],
               
                # })
                
                # account_move_id.y_boe_id = self.y_boe_template_id.id
                # self.y_boe_template_id.y_invoice_number = account_move_id.id
                self.y_is_boe_done = True


           
            # rainbow man
            message = str(number_of_landedcost) + ' ' + 'Landed Costs Created Successfully'
            print()
            return {
                   'effect': {
                       'fadeout': 'slow',
                       'message': message,
                       'type': 'rainbow_man',
                   }
               }


class ProductTemplateNew(models.Model):
    _inherit = "product.template"

    y_import_duty_structure_id = fields.Many2one('import.duty.structure',string="Import Duty Structure")
    y_is_insurance_for_idc = fields.Boolean(string="Insurance for Import Duty Calcualtion")


    @api.constrains('y_is_insurance_for_idc')
    def check_duplicate_boolean(self):
        if self.y_is_insurance_for_idc:
            product_insurance_onb = self.env['product.template'].search([('type','=','service'), ('y_is_insurance_for_idc','=',True),'|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])
            if len(product_insurance_onb) > 1:
                raise UserError(_("Creation of multiple Insurance product is restricted"))



class ResCompany(models.Model):
    _inherit = 'res.company'

    y_bill_of_entry_sequence_id = fields.Many2one('ir.sequence',string="BOE Sequence")
    
class ResConfigSettingsNew(models.TransientModel):
    _inherit = 'res.config.settings'

    y_bill_of_entry_sequence_id = fields.Many2one('ir.sequence',string='BOE Sequence',readonly=False,related="company_id.y_bill_of_entry_sequence_id")


class AccountMoveNew(models.Model):
    _inherit = "account.move"

    y_boe_id = fields.Many2one('boe.template',string="BOE",domain="[('y_invoice_number','=',False),('y_company_id','=',company_id),('y_state','in',('in_process','confirm'))]")
    y_is_same_currency = fields.Boolean(string="Is same Currency",copy=False,compute="check_same_currency",store=True)

    @api.depends('move_type','company_currency_id','currency_id')
    def check_same_currency(self):
        for rec in self:
            if rec.move_type =='in_invoice' and rec.company_currency_id != rec.currency_id:
                rec.write({'y_is_same_currency':True})
            else:
                rec.write({'y_is_same_currency':False})


class AccountMove(models.Model):
    _inherit = "account.move"


    




    @api.onchange('y_boe_id')
    def autocomplete_boe(self):
        bill_val_list = []
        new_lines = self.env['account.move.line']
        if self.y_boe_id:
            for rec in self.y_boe_id:
                existing_bills = self.y_boe_id.y_invoice_ids.filtered(lambda x:x.id != self.y_boe_id.id and x.state == 'posted' and x.move_type == 'in_invoice')
                if existing_bills:
                    raise ValidationError("The BOE '{}' has already generated the bill '{}'.".format(self.y_boe_id.y_bill_of_entry_code,",".join(existing_bills.mapped('name'))))
                
                for boe_lines in rec.y_boe_template_line_ids:
                    if not boe_lines.y_duties_exempted:
                        taxes_ids = boe_lines.y_import_duty_structure_line_boe_ids.mapped('y_taxes_ids').ids
                        #import dut strcuture line
                        for import_lines in boe_lines.y_import_duty_structure_line_boe_ids.filtered(lambda x:x.y_duty_type_id):
                            bill_val_list.append({
                                'product_id':import_lines.y_duty_type_id.id,
                                'account_id':import_lines.y_duty_type_id.property_account_expense_id.id,
                                'price_unit':import_lines.y_assesable_value,
                                'tax_ids':taxes_ids,
                                })

                        #additional lines
                        for additional_lines in boe_lines.y_addtional_quanitity_boe_line_ids:
                            bill_val_list.append({
                                'product_id':additional_lines.y_product_id.id,
                                'account_id':additional_lines.y_product_id.property_account_expense_id.id,
                                'price_unit':additional_lines.y_sum_value,
                                'tax_ids':taxes_ids,

                                })


                        #service lines
                        for service_lines in boe_lines.y_service_import_report_line_ids:
                            bill_val_list.append({
                                'product_id':service_lines.y_product_id.id,
                                'account_id':service_lines.y_product_id.property_account_expense_id.id,
                                'price_unit':service_lines.y_sum_value,
                                'tax_ids':taxes_ids,

                                })



                        for mis_lines in boe_lines.y_boe_miscellaneous_value_line_ids:
                            bill_val_list.append({
                                'product_id':mis_lines.y_product_id.id,
                                'account_id':mis_lines.y_product_id.property_account_expense_id.id,
                                'price_unit':mis_lines.y_sum_value,
                                'tax_ids':taxes_ids,

                                })

                    else:
                        #import duty strcuture line
                        for import_lines in boe_lines.y_import_duty_structure_line_boe_ids.filtered(lambda x:not x.y_duty_type_id):
                            account = False
                            if boe_lines.y_import_duty_structure_id.y_import_duty_structure_ids:
                                account = boe_lines.y_import_duty_structure_id.y_import_duty_structure_ids[0].y_product_exp_account_id.id
                            if not account:
                                raise ValidationError(_("Please map expense account for import duty strcuture lines"))
                            total_assessable_value = boe_lines.y_total_assessable_value
                            bill_val_list.append({
                                'account_id':account,
                                'price_unit':total_assessable_value,
                                'tax_ids':import_lines.y_taxes_ids.ids,

                                })

                            bill_val_list.append({
                                'account_id':account,
                                'price_unit':-total_assessable_value,
                                })


                            
                self.company_id=rec.y_company_id.id if rec.y_company_id else False
                self.invoice_date = rec.y_bill_of_entry_date
                self.partner_id=rec.y_duty_to_pay_vendor_id.id if rec.y_duty_to_pay_vendor_id else False

                if self.y_boe_id and self.currency_id and self.currency_id != self.company_id.currency_id:
                    self.write({'y_manual_rate':self.y_boe_id.y_bill_of_entry_rate})

        if bill_val_list:
            for line in bill_val_list:
                new_line = new_lines.new(line)
                new_lines += new_line

            self.invoice_line_ids = new_lines


    def action_post(self):
        for rec in self:
            if rec.y_boe_id:
                rec.y_boe_id.y_invoice_number = self.id
        return super(AccountMoveNew,self).action_post()  

    def button_draft(self):
        res = super(AccountMoveNew,self).button_draft()
        for rec in self:
            if rec.y_boe_id:
                rec.y_boe_id.y_invoice_number = False
        
        return res
class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        for payment in self:
            if payment.y_purchase_account_payment_id:
                if payment.y_purchase_account_payment_id.y_boe_id:
                    payment.y_purchase_account_payment_id.y_boe_id.write({'y_payment_id':payment.id})
        return super().action_post()

    def action_draft(self):
        for payment in self:
            if payment.y_purchase_account_payment_id:
                if payment.y_purchase_account_payment_id.y_boe_id:
                    payment.y_purchase_account_payment_id.y_boe_id.write({'y_payment_id':False})
        return super().action_draft()



class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    y_boe_ids = fields.Many2many('boe.template',string="BOE",store=True)
