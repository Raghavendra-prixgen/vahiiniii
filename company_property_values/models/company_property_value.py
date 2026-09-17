from odoo import fields, models, api,_,tools
from operator import itemgetter
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from lxml import etree

class CompanyPropertyValuesReport(models.Model):
    _name = 'company.property.values.report'
    _description =  "Company Property Values"
    _rec_name= 'field_id'

    field_id = fields.Many2one('ir.model.fields',string="Field Name")
    record = fields.Char(string="Record")
    rec_id = fields.Integer(string="Record ID")
    company_id = fields.Many2one('res.company',string="Company")
    value = fields.Char(string="Value")
