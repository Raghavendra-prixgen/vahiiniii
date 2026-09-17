# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line'

    y_sale_weigh_lines_ids = fields.One2many('weighment.product', 'y_sale_line_id', string="Weighment", readonly=True, copy=False)

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	y_is_order_completed = fields.Boolean(string="Order Completed",invisible=True,store=True,compute="onchange_order_completed")
	y_is_final_display = fields.Boolean(string="Final Display",default=False)

	@api.depends('order_line.qty_delivered','order_line.product_uom_qty')
	def onchange_order_completed(self):
		for sale in self:
			line_vals = [True if line.product_uom_qty != line.qty_delivered else False for line in sale.order_line] 
			if all(line_vals) and True in line_vals:
				sale.y_is_order_completed = True
			else:
				sale.y_is_order_completed = False