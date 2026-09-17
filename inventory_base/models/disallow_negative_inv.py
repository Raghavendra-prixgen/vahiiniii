# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('product_id', 'quantity')
    def check_negative_qty(self):
        p = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        check_negative_qty = ((config['test_enable'] and self.env.context.get('test_stock_no_negative')) or not config['test_enable'])
        if not check_negative_qty:
            return
        for quant in self:
            if quant.location_id.is_subcontracting_location == False:
                if (
                    float_compare(quant.quantity, 0, precision_digits=p) == -1 and
                    quant.product_id.is_storable and quant.product_id.type == 'consu' and 
                    not quant.product_id.y_allow_negative_stock and 
                    quant.location_id.usage in ['internal', 'transit'] 
                ):
                    msg_add = ''
                    if quant.lot_id:
                        msg_add = _(" lot '%s'") % quant.lot_id.name
                    raise ValidationError(_(
                        "You cannot validate this stock operation because the "
                        "stock level of the product '%s'%s would become negative "
                        "(%s) on the stock location '%s' and negative stock is "
                        "not allowed for this product") % (
                            quant.product_id.name, msg_add, quant.quantity,
                            quant.location_id.complete_name))


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove,self)._action_done(cancel_backorder)
        for move in self:
            if move.raw_material_production_id and move.location_id.is_subcontracting_location == True:
                domain = [('location_id','=',move.location_id.id),('product_id','=',move.product_id.id)]
                if move.lot_ids:
                    domain = [('location_id','=',move.location_id.id),('product_id','=',move.product_id.id),('lot_id','in',move.lot_ids.ids)]
                stock_quants = move.env['stock.quant'].search(domain)
                for stock in stock_quants:
                    if stock:
                        quant_quantity = sum(stock.mapped('quantity'))
                        p = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        if float_compare(quant_quantity, 0, precision_digits=p) == -1:
                            msg_add = ''
                            if stock.lot_id:
                                msg_add = _(" lot '%s'") % stock.lot_id.name
                            raise ValidationError(_(
                                "You cannot validate this stock operation because the "
                                "stock level of the product '%s'%s would become negative "
                                "(%s) on the stock location '%s' and negative stock is "
                                "not allowed for this product.") % (
                                    stock.product_id.name, msg_add, stock.quantity,
                                    stock.location_id.complete_name))
        return res