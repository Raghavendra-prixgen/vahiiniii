from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, tools, _
import datetime
from datetime import date, datetime, timedelta
import calendar


class TaxCode(models.Model):
    _name = "tax.code"
    _description = "Tax Code"
    _rec_name = "y_name"
    _order = "y_name"

    y_name = fields.Char(string="Tax Code", required=True)
    y_company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    

    y_tax_ids = fields.One2many('account.tax', 'y_tax_code', string="Taxes")