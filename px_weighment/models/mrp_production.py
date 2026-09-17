# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _

class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	y_is_order_completed = fields.Boolean(string="Order Completed",store=True,compute="onchange_order_completed")
	y_is_final_display = fields.Boolean(string="Final Display",default=False)
	
	@api.depends('move_raw_ids.quantity','move_raw_ids.product_uom_qty')
	def onchange_order_completed(self):
		for production in self:
			move_vals = [True if move.product_uom_qty != move.quantity else False for move in production.move_raw_ids] 
			if all(move_vals) and True in move_vals:
				production.y_is_order_completed = True
			else:
				production.y_is_order_completed = False

		
	