from datetime import datetime, timedelta

from odoo import api, models, fields, _, exceptions
from dateutil.relativedelta import relativedelta
from time import strptime
from odoo.exceptions import ValidationError



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    y_joining_date = fields.Date(string='Joining Date')
    y_epf_uan_no = fields.Char(string='EPF UAN Number', size=12)
    y_esi_number = fields.Char(string='ESI Number')
    y_age = fields.Char(string='Age', size=3, compute='_compute_age')
    y_caste = fields.Char(string='Caste')
    y_handicap = fields.Boolean(string='Handicap')
    y_height = fields.Float(string='Height')
    y_weight = fields.Float(string='Weight')
    y_personal_mark_of_identification = fields.Char(string='Personal Mark of Identification')
    
    y_esi_applicable = fields.Boolean(string='ESI Applicable')
    y_vpf_applicable = fields.Boolean(string='VPF Applicable')
    y_vpf_amount = fields.Float(string='VPF Amount')
    
    
    y_pan_no= fields.Char(string='PAN No',store=True)
    
    y_date_of_relieving = fields.Date(string='Date of Relieving')
    y_date_of_resignation = fields.Date(string='Date of Resignation')
    
    
    y_street = fields.Char(string='Alternative Address')
    y_street2 = fields.Char(string='Street2')
    y_city = fields.Char(string='City')
    y_country = fields.Many2one('res.country',string='Country')
    y_state = fields.Many2one('res.country.state',string='State')
    y_zip = fields.Char(string='Zip')
    
    
    y_righteye = fields.Char(string='Right Eye',size=6)
    y_lefteye = fields.Char(string='Left Eye',size=6)
    y_total_no_of_dependents = fields.Integer(string='Total No. Of Dependents')
    
    y_registeration_number = fields.Char(string='Registration Number')
    y_driving_license = fields.Char(string='Driving License')
    
    
    
   

    @api.constrains('y_pan_no')
    def _check_pan_number(self):
        for rec in self:
            if rec.y_pan_no and len(rec.y_pan_no) > 10:
                raise models.ValidationError(_("Pan number cannot be more than 10 digits..."))
            return True
  

    @api.depends('birthday')
    def _compute_age(self):
        for rec in self:
            rec.y_age = ''
            if rec.birthday:
                dt = rec.birthday
                d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                d2 = datetime.today()
                rd = relativedelta(d2, d1)
                rec.y_age = str(rd.years) + ' years' 


    @api.constrains('y_epf_uan_no')
    def _check_number(self):
        if self.y_epf_uan_no and len(str(abs(int(self.y_epf_uan_no))))<12:
            raise ValidationError(_("EPF UAN No. should be not be more than 12 digits"))

    @api.constrains("y_joining_date","birthday")
    def _check_period(self):
        for rec in self:
            if rec.y_joining_date < rec.birthday:
                raise ValidationError('Sorry, Joining date must be greater than birthdate')


    @api.constrains('y_age')
    def _check_age(self):
        if self.y_age and len(str(abs(int(self.y_age))))>3:
            raise ValidationError(_("Age must be in 3 digits"))

