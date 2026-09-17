from datetime import datetime, timedelta
from odoo import api, models, fields, _, exceptions
from dateutil.relativedelta import relativedelta
from time import strptime
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
                raise ValidationError("You can't add line a picking if it has a sale or purchase reference.")
        return res

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        for line in self:
            if not line.lot_id and not line.lot_name and line.product_id.lot_valuated:
                raise UserError(_("Product '{}' Lot/Serial number is mandatory for product valuated by lot".format(line.product_id.display_name)))
        return super()._action_done()






