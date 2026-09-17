from odoo import models, fields, api, _
from datetime import date,datetime
import time

class StockLocationNew(models.Model):
	_inherit = "stock.location"

	y_location_category = fields.Selection([('production','Production'),('inventory','Inventory'),('maintenance','Maintenance')], string='Location Category', copy=False)
