from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, tools, _
import datetime
from datetime import date, datetime, timedelta
import calendar


class ConcessionCode(models.Model):
    _name = "concession.code"
    _description = "concession code"
    _order = 'y_name desc, id desc'
    _rec_name = 'y_name'


    y_name = fields.Char(string="Code", required=True)

class TdsSetion(models.Model):
    _name = "tds.section"
    _description = "TDS Section"

    name = fields.Char(string="Name")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)



class NatureOfDeduction(models.Model):
    _name = "nature.of.deduction"
    _description = "Nature of deduction"

    name = fields.Char(string="Name")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)


    

class AccountTaxInherit(models.Model):
    _inherit = 'account.tax'

    y_tax_code = fields.Many2one('tax.code', string="Tax Code")


    @api.depends('y_tax_code')
    def _compute_display_name(self):
        super()._compute_display_name()
        for tax in self:
            if tax.y_tax_code:
                tax.display_name = f"[{tax.y_tax_code.y_name}] {tax.display_name}"





class TDSMaster(models.Model):
    _name = "tds.master"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "TDS Master"
    _rec_name = 'y_section_id'


    y_tax_type = fields.Selection(selection=[
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            
            ],string='Tax Type',copy=False)
    y_turnover = fields.Float(string="TurnOver")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)
    y_product_ids = fields.Many2many('product.product',string="Products",domain="[('type', '=', 'service')]")
    y_account_ids = fields.Many2many('account.account',string="Accounts",check_company=True)
    y_nature_of_deduction_id = fields.Many2one('nature.of.deduction',string="Nature of deduction")
    y_section_id = fields.Many2one('tds.section',string="Section")
    y_recipent_type = fields.Selection(selection=[
            ('P', 'Individual'),
            ('C', 'Company'),
            ('A', 'Association'),
            ('F', 'Firm'),
            ('H', 'HUF'),
            ('T', 'Trust'),
            ],string='Recipent type',copy=False)


    y_concession_code_id = fields.Many2one('concession.code',string="Concession Code")
    y_tax_code = fields.Many2one('tax.code', string="Tax Code")
    y_tax_ids = fields.Many2many('account.tax','account_tax_with_pan',string="TDS with PAN")
    y_without_pan_tax_ids = fields.Many2many('account.tax','account_tax_without_pan',string="TDS without PAN")
    y_effective_date = fields.Date(string="Effective Date")
    y_contract_value = fields.Float(string="Per Contract Value")
    y_threshold_value = fields.Float(string="Threshold Value")
    y_concession_tax_ids = fields.Many2many('account.tax','concession_tax_ids',string='Concession Tax')
    y_per_transcation = fields.Float(string="Per Transaction")
    y_aggregate_limit = fields.Float(string="Aggregate Limit")






class TDSAccountMove(models.Model):
    _inherit = "account.move"

    def calcluate_tds(self):
        for rec in self:
            total_sum_of_posted_bill = 0
            if rec.partner_id.y_wtax_applicable:
                if not rec.invoice_date:
                    raise UserError(_("The invoice date is required to simulate TDS"))
                for line in rec.invoice_line_ids:
                    tds_lines_obj = rec.partner_id.y_tds_lines.filtered(lambda x:x.y_start_date and x.y_end_date and x.y_start_date <= rec.invoice_date and x.y_end_date >= rec.invoice_date )
                    if tds_lines_obj:
                        if line.account_id in tds_lines_obj.y_account_ids:
                            tds_master_obj = tds_lines_obj.y_tds_master_id
                            if line.move_id.amount_total >= tds_master_obj.y_contract_value:
                                if tds_master_obj.y_concession_tax_ids:
                                    line.tax_ids = [(4, tax.id) for tax in tds_master_obj.y_concession_tax_ids]
                                else:
                                    if line.move_id.partner_id.l10n_in_pan:
                                        line.tax_ids = [(4, tax.id) for tax in tds_lines_obj.y_tds_tax_ids]

                                    else:
                                        line.tax_ids = [(4, tax.id) for tax in tds_master_obj.y_without_pan_tax_ids]

                            elif tds_master_obj.y_threshold_value:
                                start_pre_year = date.today().strftime("%Y-%m-%d")
                                end_year = date.today().strftime("%Y-%m-%d")
                                if rec.invoice_line_ids.filtered(lambda line: line.product_id.type in ('consu') and  line.product_id.is_storable or line.product_id.type in ('consu') and not line.product_id.is_storable) and rec.company_id.currency_id.name == 'INR' and rec.currency_id.name=='INR':
                                    fiscalyear_month = rec.company_id.fiscalyear_last_month
                                    fiscalyear_last_day = rec.company_id.fiscalyear_last_day
                                    start_month = int(fiscalyear_month) + 1
                                    if rec.invoice_date:
                                        if rec.invoice_date.month <= 3:
                                            year = rec.invoice_date.year
                                            start_year = year - 1
                                            next_day = calendar.monthrange(start_year, start_month)[1]
                                            pre_first_day = next_day - (next_day - 1)
                                            start_pre_year = f"{start_year}-{start_month}-{pre_first_day}"
                                            end_year = f"{year}-{fiscalyear_month}-{fiscalyear_last_day}"
                                        else:
                                            year = rec.invoice_date.year
                                            end_pre_year = year + 1
                                            next_day = calendar.monthrange(end_pre_year, start_month)[1]
                                            pre_first_day = next_day - (next_day - 1)
                                            start_pre_year = f"{year}-{start_month}-{pre_first_day}"
                                            end_year = f"{end_pre_year}-{fiscalyear_month}-{fiscalyear_last_day}"

                                   
                                    object_start_pre_year = datetime.strptime(start_pre_year, '%Y-%m-%d').date()
                                    object_end_year = datetime.strptime(end_year, '%Y-%m-%d').date()
                                

                                    self.env.cr.execute("""
                                        SELECT
                                            SUM(ail.price_subtotal)
                                        FROM
                                            account_move_line ail
                                        JOIN
                                            account_move am ON am.id = ail.move_id
                                        JOIN
                                            product_product pp ON ail.product_id = pp.id
                                        JOIN
                                            product_template pt ON pp.product_tmpl_id = pt.id
                                        JOIN 
                                            res_currency rc ON rc.id = ail.currency_id
                                        WHERE
                                            am.move_type = 'in_invoice'
                                            AND am.partner_id = %s
                                            AND am.state = 'posted'
                                            AND am.date BETWEEN %s AND %s
                                            AND (pt.type = 'consu' AND pt.is_storable OR pt.type = 'consu' AND not pt.is_storable)
                                            AND rc.name = 'INR'
                                    """, (rec.partner_id.id, object_start_pre_year, object_end_year))
                                    total_sum = self.env.cr.fetchone()[0] or 0.0

                                    self.env.cr.execute("""
                                        SELECT
                                            SUM(ail.price_subtotal)
                                        FROM
                                            account_move_line ail
                                        JOIN
                                            account_move am ON am.id = ail.move_id
                                        JOIN
                                            product_product pp ON ail.product_id = pp.id
                                        JOIN
                                            product_template pt ON pp.product_tmpl_id = pt.id
                                        JOIN 
                                            res_currency rc ON rc.id = ail.currency_id
                                        WHERE
                                            am.move_type = 'in_refund'
                                            AND am.partner_id = %s
                                            AND am.state = 'posted'
                                            AND am.date BETWEEN %s AND %s
                                            AND (pt.type = 'consu' AND pt.is_storable OR pt.type = 'consu' AND not pt.is_storable)
                                            
                                            AND rc.name = 'INR'
                                    """, (rec.partner_id.id, object_start_pre_year, object_end_year))
                                    total_credit_sum = self.env.cr.fetchone()[0] or 0.0

                                    total_move_sum = total_sum - total_credit_sum

                                    if rec.move_type == 'in_invoice':
                                        total_sum_of_posted_bill = total_move_sum + sum(rec.invoice_line_ids.filtered(lambda line: line.product_id.type in ('consu') and  line.product_id.is_storable or line.product_id.type in ('consu') and not line.product_id.is_storable).mapped('price_subtotal'))

                                    if rec.move_type == 'in_refund':
                                        total_sum_of_posted_bill = total_move_sum - sum(rec.invoice_line_ids.filtered(lambda line: line.product_id.type in ('consu') and  line.product_id.is_storable or line.product_id.type in ('consu') and not line.product_id.is_storable).mapped('price_subtotal'))

                                if total_sum_of_posted_bill >= tds_master_obj.y_threshold_value:

                                    if tds_master_obj.y_concession_tax_ids:
                                        line.tax_ids = [(4, tax.id) for tax in tds_master_obj.y_concession_tax_ids]
                                    else:
                                        if line.move_id.partner_id.l10n_in_pan:
                                            line.tax_ids = [(4, tax.id) for tax in tds_lines_obj.y_tds_tax_ids]

                                        else:
                                            line.tax_ids = [(4, tax.id) for tax in tds_master_obj.y_without_pan_tax_ids]




class TdsLines(models.Model):
    _name = "tds.lines"
    _description = "TDS Lines"


    y_partner_id = fields.Many2one('res.partner',string="Partner")
    y_start_date = fields.Date(string="Start Date")
    y_end_date = fields.Date(string="End Date")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)


    y_nature_of_deduction_id = fields.Many2one('nature.of.deduction',string="Nature of deduction")
    y_section_id = fields.Many2one('tds.section',string="Section")
    y_tax_code = fields.Many2one('tax.code', string="Tax Code")   # <-- add this
    y_recipent_type = fields.Selection(selection=[
            ('P', 'Individual'),
            ('C', 'Company'),
            ('A', 'Association'),
            ('F', 'Firm'),
            ('H', 'HUF'),
            ('T', 'Trust'),
            ],string='Recipent type',copy=False,related="y_partner_id.y_recipent_type")
    y_is_concession_applicable = fields.Boolean(string="Concession")
    y_tds_tax_ids = fields.Many2many('account.tax',string="TDS Tax")
    y_tds_master_id = fields.Many2one('tds.master',string='TDS Master')
    y_product_ids = fields.Many2many('product.product',string="Products",related="y_tds_master_id.y_product_ids")
    y_account_ids = fields.Many2many('account.account',string="Accounts",related="y_tds_master_id.y_account_ids")


    @api.onchange('y_nature_of_deduction_id','y_section_id','y_recipent_type','y_is_concession_applicable')
    def onchange_tds_items(self):
        for rec in self:
            if rec.y_is_concession_applicable == True:
                rec.y_tds_tax_ids = False
            elif rec.y_nature_of_deduction_id and rec.y_section_id and rec.y_recipent_type and not rec.y_is_concession_applicable:
                tds_master_obj = self.env['tds.master'].search([('y_nature_of_deduction_id','=',rec.y_nature_of_deduction_id.id),('y_section_id','=',rec.y_section_id.id),('y_recipent_type','=',rec.y_recipent_type)])
                if tds_master_obj:
                    rec.y_tds_master_id = tds_master_obj.id

                    rec.y_tds_tax_ids = [(4, tax.id) for tax in tds_master_obj.y_tax_ids]


    @api.onchange('y_tax_code')
    def _onchange_y_tax_code(self):
        self.y_tds_tax_ids = self.y_tax_code.y_tax_ids if self.y_tax_code else False

    @api.onchange('y_tds_tax_ids')
    def _onchange_y_tds_tax_ids(self):
        if self.y_tds_tax_ids and self.y_tds_tax_ids.y_tax_code:
            self.y_tax_code = self.y_tds_tax_ids.y_tax_code



class ResPartner(models.Model):
    _inherit = "res.partner"

    y_wtax_applicable = fields.Boolean(string="W-Tax applicable")
    y_tds_lines = fields.One2many('tds.lines','y_partner_id',string="Tds Lines")
    y_recipent_type = fields.Selection(selection=[
            ('P', 'Individual'),
            ('C', 'Company'),
            ('A', 'Association'),
            ('F', 'Firm'),
            ('H', 'HUF'),
            ('T', 'Trust'),
            ],string='Recipent type',copy=False,compute="compute_pan_no")

    @api.depends('l10n_in_pan')
    def compute_pan_no(self):
        for rec in self:
            if rec.l10n_in_pan:
                rec.y_recipent_type = rec.l10n_in_pan[3]
            else:
                rec.y_recipent_type = False





















                        
                      


