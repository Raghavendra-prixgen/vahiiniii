from odoo import fields, models, api,_,tools
from operator import itemgetter
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from lxml import etree

class ResUser(models.Model):
    _inherit = 'res.users'

    y_inventory_aging_domain = fields.Char(string="Inventory Aging Domain")
    y_inventory_value_aging_domain = fields.Char(string="Inventory Value Aging Domain")