# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo import tools
import datetime
from odoo.exceptions import UserError, ValidationError

class TdsReportView(models.Model):
    _name = "tds.report.view"
    _auto = False
    _description = 'Tds Report View'
        
    y_posting_date = fields.Date(string='Posting Date')
    y_bill_date = fields.Date(string='Bill Date')
    y_company_pan = fields.Char(string="PAN of the Deductor",related="y_company_id.partner_id.l10n_in_pan")
    y_vendor_bill_id = fields.Many2one('account.move',string='Vendor Bill No')
    y_vendor_ref = fields.Char(string='Vendor Ref')
    y_party_code = fields.Char(string='Party Code')
    y_partner_id = fields.Many2one('res.partner',string='Vendor Name')
    y_pan_no = fields.Char(string="PAN of the Deductee")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_product_code = fields.Char(string='Product Code')     
    y_account_id = fields.Many2one('account.account',string='Account')
    y_qty = fields.Char(string='Quantity')
    y_unit_price = fields.Float(string='Unit Price')
    
    y_base_amount = fields.Float(string='Base Amount')
    y_tds_tax_name = fields.Char(string='Tax')
    y_tds_percent = fields.Float(string='TDS %')
    y_tds_amount = fields.Float(string='TDS Amount') 
    y_l10n_in_section_id = fields.Many2one('l10n_in.section.alert',string="Section")
    
    y_company_id = fields.Many2one('res.company',string="Company")  
              

    def init(self):
        tools.drop_view_if_exists(self._cr, 'tds_report_view')
        self._cr.execute("""
            CREATE OR REPLACE VIEW tds_report_view AS (
                SELECT
                    line.company_id AS y_company_id,
                    row_number() OVER () AS id,
                    move.date AS y_posting_date,
                    move.invoice_date AS y_bill_date,
                    move.id AS y_vendor_bill_id,
                    move.ref AS y_vendor_ref,
                    partner.ref AS y_party_code,
                    partner.id AS y_partner_id,
                    partner.l10n_in_pan AS y_pan_no,
                    line.product_id AS y_product_id,
                    product.default_code AS y_product_code,
                    line.account_id AS y_account_id,
                    line.quantity AS y_qty,
                    line.price_unit AS y_unit_price,
                    CASE 
                        WHEN move.move_type IN ('entry', 'in_refund') THEN line.amount_currency
                        ELSE ROUND(line.quantity * line.price_unit, 2) 
                    END AS y_base_amount,
                    tax.name->>'en_US' AS y_tds_tax_name,
                    tax.amount AS y_tds_percent,
                    section.id AS y_l10n_in_section_id,
                    CASE 
                        WHEN move.move_type IN ('entry', 'in_refund') THEN ROUND(line.amount_currency * -(tax.amount) / 100, 2)
                        ELSE ROUND((line.quantity * line.price_unit) * -(tax.amount) / 100, 2) 
                    END AS y_tds_amount
                FROM 
                    account_move AS move
                    LEFT JOIN account_move_line AS line ON move.id = line.move_id
                    LEFT JOIN res_partner AS partner ON partner.id = line.partner_id
                    LEFT JOIN res_company AS company ON company.id = line.company_id
                    LEFT JOIN product_product AS product ON product.id = line.product_id
                    LEFT JOIN product_template AS pro_tem ON pro_tem.id = product.product_tmpl_id
                    LEFT JOIN account_move_line_account_tax_rel AS arl ON line.id = arl.account_move_line_id
                    LEFT JOIN account_tax AS tax ON tax.id = arl.account_tax_id
                    LEFT JOIN account_tax_group AS tax_group ON tax_group.id = tax.tax_group_id
                    LEFT JOIN l10n_in_section_alert as section ON section.id = tax.l10n_in_section_id
                WHERE 
                        move.state = 'posted' 
                        AND move.move_type IN ('in_invoice', 'entry')
                GROUP BY 
                    move.id, line.id, tax.id, tax.amount, move.ref, partner.ref, partner.id, product.default_code,section.id
                )""")
        

class TdsRegister(models.TransientModel):
    _name = "tds.register.report.tree"
    _description = "Tds Register Report"

    y_date_start = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    y_date_end = fields.Date(string="End Date", required=True, default=fields.Date.today)
    y_company_id = fields.Many2one('res.company',required=True,string="Company")

    @api.constrains('date_start')
    def _code_constrains(self):
        if self.y_date_start > self.y_date_end:
            raise ValidationError(_("'Start Date' must be before 'End Date'"))

    def get_summary_tree(self):
        self.ensure_one()
        company_id = self.y_company_id
        if self.y_company_id.sudo().parent_id:
            company_id = self.y_company_id.sudo().parent_id
        tax_group_id = self.env['account.tax.group'].search([('name','=','TDS'),('company_id','=',company_id.id)]).id
        if not tax_group_id:
            raise ValidationError("TDS Tax Group Not Configured.")
        start_date = self.y_date_start
        end_date = self.y_date_end
        
        if not self.sudo().y_company_id.child_ids:
            company_clause = "AND move.company_id = {}".format(self.y_company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id).ids
            if len(access_company_ids) == 1:
                company_clause = "AND move.company_id = {}".format(access_company_ids[0])
            else:
                company_clause = "AND move.company_id in {}".format(tuple(access_company_ids))
        

        params = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        tools.drop_view_if_exists(self._cr, 'tds_report_view')
        query = """
                CREATE OR REPLACE VIEW tds_report_view AS (
                    SELECT
                        line.company_id AS y_company_id,
                        row_number() OVER () AS id,
                        move.date AS y_posting_date,
                        move.invoice_date AS y_bill_date,
                        move.id AS y_vendor_bill_id,
                        move.ref AS y_vendor_ref,
                        partner.ref AS y_party_code,
                        partner.id AS y_partner_id,
                        partner.l10n_in_pan AS y_pan_no,
                        line.product_id AS y_product_id,
                        product.default_code AS y_product_code,
                        line.account_id AS y_account_id,
                        line.quantity AS y_qty,
                        line.price_unit AS y_unit_price,
                        CASE 
                            WHEN move.move_type IN ('entry', 'in_refund') THEN line.amount_currency
                            ELSE ROUND(line.quantity * line.price_unit, 2) 
                        END AS y_base_amount,
                        tax.amount AS y_tds_percent,
                        tax.name->>'en_US' AS y_tds_tax_name,
                        section.id AS y_l10n_in_section_id,
                        CASE 
                            WHEN move.move_type IN ('entry', 'in_refund') THEN ROUND(line.amount_currency * -(tax.amount) / 100, 2)
                            ELSE ROUND((line.quantity * line.price_unit) * -(tax.amount) / 100, 2) 
                        END AS y_tds_amount
                    FROM 
                        account_move AS move
                        LEFT JOIN account_move_line AS line ON move.id = line.move_id
                        LEFT JOIN res_partner AS partner ON partner.id = line.partner_id
                        LEFT JOIN res_company AS company ON company.id = line.company_id
                        LEFT JOIN product_product AS product ON product.id = line.product_id
                        LEFT JOIN product_template AS pro_tem ON pro_tem.id = product.product_tmpl_id
                        LEFT JOIN account_move_line_account_tax_rel AS arl ON line.id = arl.account_move_line_id
                        LEFT JOIN advance_tax_account_move_rel as adv_arl ON adv_arl.account_move_line_id = line.id
                        LEFT JOIN account_tax AS tax ON tax.id = arl.account_tax_id OR tax.id = adv_arl.account_tax_id
                        LEFT JOIN account_tax_group AS tax_group ON tax_group.id = tax.tax_group_id
                        LEFT JOIN l10n_in_section_alert as section ON section.id = tax.l10n_in_section_id
                    WHERE 
                        tax_group.id = {} 
                        AND move.state = 'posted' 
                        AND move.move_type IN ('in_invoice', 'entry') 
                        AND move.date BETWEEN '{}' AND '{}'
                        {}
                    GROUP BY 
                        move.id, line.id, tax.id, tax.amount, move.ref, partner.ref, partner.id, product.default_code,section.id
                    )""".format(tax_group_id,start_date, end_date,company_clause)

        
        # print('\n'*3)
        # print(query)
        # print('\n'*3)
        self._cr.execute(query)
        tree_view_id = self.env.ref('tds_register_report.tds_report_view_tree').id

        return {
               'name': _("TDS Register Report ({} To {})".format(start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'))),
                'res_model': 'tds.report.view',
                'type': 'ir.actions.act_window',
                'view_mode': 'list',
                'view_id':self.env.ref('tds_register_report.tds_report_view_tree').id,
                'views':[[tree_view_id,'list']],
                }
    
    
            
