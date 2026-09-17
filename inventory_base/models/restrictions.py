# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    def unlink(self):
        for move in self:
            if (move.purchase_line_id or move.sale_line_id) and move.picking_id.state in ('waiting','confirmed','assigned'):
                raise ValidationError("You can't delete a move if it has a sale or purchase reference.")
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for move in res:
            check_create = False
            if move.picking_id.move_ids_without_package.filtered(lambda x:x.id != move.id).mapped('purchase_line_id') and not move.purchase_line_id:
                check_create = True

            elif move.picking_id.move_ids_without_package.filtered(lambda x:x.id != move.id).mapped('sale_line_id') and not move.sale_line_id:
                check_create = True
            if check_create:
                raise ValidationError("You can't add a line if it has a sale or purchase reference.")
        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    y_warehouse_address_id = fields.Many2one('res.partner',string="Warehouse Address",compute="_compute_warehouse_address",store=True)

    @api.depends('location_id','location_dest_id')
    def _compute_warehouse_address(self):
        for order in self:
            order.y_warehouse_address_id = False
            if order.location_id.usage == 'internal':
                order.y_warehouse_address_id = order.location_id.warehouse_id.partner_id.id
            elif order.location_dest_id.usage == 'internal':
                order.y_warehouse_address_id = order.location_dest_id.warehouse_id.partner_id.id



class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_return(self):
        for line in self.product_return_moves:
            return_move = line.move_id
            done_quantity = sum(return_move.returned_move_ids.filtered(lambda move:move.state == 'done').mapped('quantity'))
            non_done_quantity = sum(return_move.returned_move_ids.filtered(lambda move:move.state not in ('done','cancel')).mapped('product_uom_qty'))
            return_quantity = done_quantity + non_done_quantity + line.quantity
            if return_move.quantity < return_quantity:
                raise UserError(_("You cannot return more than the delivered quantity "
                                  "for product %s.") % (return_move.product_id.display_name))
        return super()._create_return()

