# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    stock_lot_ids = fields.One2many('stock.lot','product_id')

class StockQuantInherit(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('inventory_quantity')
    def inventory_quantity_approval(self):
        if not self.env.user.has_group('inventory_base.group_inventory_adjustment_access'):
            raise UserError(_('You are Not Authorised Person to Update the Quantity'))

class prixgen_stock_picking(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def sale_product_lot(self):
        if self.product_id:
            product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty > 0)
            zero_product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty <= 0)
            if product_lots_ids:
                product_lots_ids.write({'y_show_lot':True})
            if zero_product_lots_ids:
                zero_product_lots_ids.write({'y_show_lot':False})

class prixgen_purchase_stock_picking(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def purchase_product_lot(self):
        if self.product_id:
            product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty > 0)
            zero_product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty <= 0)
            if product_lots_ids:
                product_lots_ids.write({'y_show_lot':True})
            if zero_product_lots_ids:
                zero_product_lots_ids.write({'y_show_lot':False})


class prixgen_stock_picking_move(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('product_id')
    def stock_product_lot(self):
        if self.product_id:
            product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty > 0)
            zero_product_lots_ids = self.product_id.stock_lot_ids.filtered(lambda x:x.product_qty <= 0)
            if product_lots_ids:
                product_lots_ids.write({'y_show_lot':True})
            if zero_product_lots_ids:
                zero_product_lots_ids.write({'y_show_lot':False})

    y_serial_no = fields.Char(string='#',compute="_compute_sl")

    @api.depends('product_id')
    def _compute_sl(self):
        var = 1
        for rec in self:
            if rec.y_serial_no == False:
                rec.y_serial_no = ord(chr(var + int(rec.y_serial_no)))
                var += 1
            else:
                rec.y_serial_no = False

class StockProductionLot(models.Model):
    _inherit="stock.lot"

    y_show_lot=fields.Boolean('Show Lot',default=False)
    name = fields.Char(tracking=True)
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    y_serial_no = fields.Char(string='#',compute="_compute_sl")

    def _compute_picked(self):
        super(StockMove, self)._compute_picked()
        for move in self.filtered(lambda m: m.is_subcontract):
            if move.state == 'done' or any(ml.picked for ml in move.move_line_ids):
                move.picked = True
            elif move.move_line_ids:
                move.picked = False

    @api.depends('product_id')
    def _compute_sl(self):
        var = 1
        for rec in self:
            if rec.y_serial_no == False:
                rec.y_serial_no = ord(chr(var + int(rec.y_serial_no)))
                var += 1
            else:
                rec.y_serial_no = False


