# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order'

    y_purchase_weigh_lines_ids = fields.One2many('weighment.product', 'y_purchase_line_id', string="Weighment", readonly=True, copy=False)

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	y_is_order_completed = fields.Boolean(string="Order Completed",invisible=True,store=True,compute="onchange_order_completed")
	y_is_final_display = fields.Boolean(string="Final Display",default=False)
	
	@api.depends('order_line.qty_received','order_line.product_qty')
	def onchange_order_completed(self):
		for purchase in self:
			line_vals = [True if line.product_qty != line.qty_received else False for line in purchase.order_line] 
			if all(line_vals) and True in line_vals:
				purchase.y_is_order_completed = True
			else:
				purchase.y_is_order_completed = False
			

