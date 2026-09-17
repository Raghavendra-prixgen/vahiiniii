# -*- coding: utf-8 -*-
from collections import namedtuple
import json
import time
from itertools import groupby
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class Picking(models.Model):
    _inherit = "stock.picking"
    _order = "name desc"

    y_weighment_id = fields.Many2one('weighment.picking',string='Attach Weighment No')
    y_weighment_ids = fields.Many2many('weighment.picking','weighment_picking_stock_rel',string="Weighments",compute="_compute_weighment_pickings")

    def _compute_weighment_pickings(self):
        for picking in self:
            picking.y_weighment_ids = False
            if picking.purchase_id:
                query = """SELECT weigh.y_weigh_product_id,purchase.id
                            FROM weighment_product weigh
                            LEFT JOIN purchase_order_line line ON line.id = weigh.y_purchase_line_id
                            LEFT JOIN purchase_order purchase ON purchase.id = line.order_id or weigh.y_purchase_id = purchase.id
                            WHERE (weigh.y_purchase_line_id is not null or weigh.y_purchase_id is not null) and purchase.id = {}""".format(picking.purchase_id.id)
                self.env.cr.execute(query)
                weighment_ids = [row[0] for row in self.env.cr.fetchall()]
                if weighment_ids:
                    picking.y_weighment_ids = [(6,0,weighment_ids)]

    @api.onchange('y_weighment_id')
    def onchange_y_weighment(self):
        for record in self:
            # If no weighment is selected, exit the method
            if not record.y_weighment_id:
                return
            # Iterate through move lines in the picking
            for move in record.move_ids_without_package:
                # Find matching weighment product lines with the same purchase line
                if move.purchase_line_id:
                    matching_weighment_lines = record.y_weighment_id.y_weighment_product_lines.filtered(
                        lambda l: l.y_purchase_line_id == move.purchase_line_id and
                          l.y_product_id == move.product_id)
                if move.sale_line_id:
                    matching_weighment_lines = record.y_weighment_id.y_weighment_product_lines.filtered(
                        lambda l: l.y_sale_line_id == move.sale_line_id and
                          l.y_product_id == move.product_id)

                # If matching weighment lines are found
                if matching_weighment_lines:
                    # Update the move line quantity with the weighment line quantity
                    move.quantity = sum(matching_weighment_lines.mapped('y_product_quantity'))
                else:
                    raise ValidationError(_('Selected Weighment is not matching'))

class StockMove(models.Model):
    _inherit = "stock.move"

    y_stock_line_id = fields.One2many('weighment.product', 'y_deliver_line_id', string="Stock Move", readonly=True, copy=False)