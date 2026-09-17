from odoo import models, fields, api, _,exceptions
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = "res.company"

    y_factory_number = fields.Char(string= "Factories Act. Regd. No.")
    y_company_status = fields.Selection([
                                        ('Pulic',"Public Limited Co."),
                                        ('private',"Private Limited Co."),
                                        ('other',"Others"),
                                        ('gov',"Goverment"),
                                        ('inv_pro',"Individual/Proprietary"),
                                        ('reg',"Register Trust"),
                                        ('partnership',"Partnership"),
                                        ('society',"Society/Co-op Society")],string="Company Status")
    y_msme_code = fields.Char(string="MSME Code")
    y_is_indian_company = fields.Boolean(string="Is Company",compute="compute_indian_company")
    y_ccc_no = fields.Char(string="CCC No")
    y_ce_range = fields.Char(string="CE Range")
    y_ecc_number = fields.Char(string="ECC No.")
    y_ce_division = fields.Char(string="CE Division")
    y_tan_no = fields.Char(string="TAN No")
    y_tcan_no = fields.Char(string="T.C.A.N No.")
    y_circle_no = fields.Integer(string="Circle No")
    y_assignes_officer = fields.Char(string="Assignes Officer")
    y_ward_number = fields.Char(string="Ward Number")
        

    @api.onchange('country_id')
    def compute_indian_company(self):
        for rec in self:
            rec.y_is_indian_company = False
            if self.country_id.currency_id.name == 'INR':
                rec.y_is_indian_company = True
                
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    y_provident_fund = fields.Char(string="PF No.",store=True)
    y_universal_account_number = fields.Char(string="PF UAN",store=True)
    y_esi_number = fields.Char(string="ESIC No.",store=True)
    y_pan_no = fields.Char(string="PAN No.",store=True)

class Partner(models.Model):
    _inherit = 'res.partner'

    y_is_indian_company = fields.Boolean(string="Is Indian Company",compute="check_company_id")
    l10n_in_pan = fields.Char(compute='_get_pan_no',store=True,inverse='_set_pan_no')

    @api.depends('company_id')
    def check_company_id(self):
        for rec in self:
            if self.env.company.country_id.name == 'India':
                rec.y_is_indian_company = True
            else:
                rec.y_is_indian_company = False


    @api.constrains('l10n_in_pan')
    def _check_pan_number(self):
        for rec in self:
            if rec.l10n_in_pan and len(rec.l10n_in_pan) != 10:
                raise ValidationError(_("The PAN number must be 10 alphanumeric character"))
        return True
    

    @api.constrains('vat')
    def _check_pan_vat(self):
        for rec in self:
            if rec.vat and len(rec.vat) != 15:
                raise ValidationError(_("The GST number must be 15 alphanumeric character"))
        return True


    # to set the limit of pan no
    @api.depends('vat')
    def _get_pan_no(self):
        for r in self:
            if r.vat:
                r.l10n_in_pan = r.vat[2:12]


    # pan num to editable
    def _set_pan_no(self):
        for r in self:
            r.l10n_in_pan = r.l10n_in_pan
            
    @api.onchange('vat','state_id')
    def validate_vat(self):
        if self.state_id.country_id.currency_id.name == 'INR' and self.vat:
            vat = self.vat
            sc = self.env['res.country.state'].search([('id','=',self.state_id.id)]).l10n_in_tin
            if vat[:2] != sc:
                raise ValidationError(_("GST Code Not Matched"))




    
