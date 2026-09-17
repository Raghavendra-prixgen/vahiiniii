# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"
    
    y_code = fields.Selection([('incoming', 'Receipt'), ('incoming_return', 'Purchase Return'), ('outgoing', 'Delivery'), ('outgoing_return', 'Sale Return'), 
                             ('internal', 'Internal Transfer'),('production', 'Production'),('consumption', 'Consumption'),
                             ('positive_adjustment', 'Positive Adjustment'),('negative_adjustment', 'Negative Adjustment'),
                             ('landed_cost', 'Landed Cost'),('revaluation', 'Revaluation'),('price_diff','Price Diffrence')], string='Type of Transaction')
    
    @api.model
    def create(self, vals_list):
        res = super(StockValuationLayer, self).create(vals_list)
        if res.stock_move_id and res.stock_move_id.location_id and res.stock_move_id.location_id.usage and res.stock_move_id.location_dest_id and res.stock_move_id.location_dest_id.usage:
            if res.stock_move_id and res.stock_landed_cost_id:
                res.y_code = 'landed_cost'            
            elif res.stock_move_id.location_id.usage == 'supplier' and res.stock_move_id.location_dest_id.usage == 'internal':
                res.y_code = 'incoming'
            elif res.stock_move_id.location_id.usage == 'internal' and res.stock_move_id.location_dest_id.usage == 'supplier':
                res.y_code = 'incoming_return'
            elif res.stock_move_id.location_id.usage == 'internal' and res.stock_move_id.location_dest_id.usage == 'customer':
                res.y_code = 'outgoing'
            elif res.stock_move_id.location_id.usage == 'customer' and res.stock_move_id.location_dest_id.usage == 'internal':
                res.y_code = 'outgoing_return'
            elif res.stock_move_id.location_id.usage == 'production' and res.stock_move_id.location_dest_id.usage == 'internal':
                res.y_code = 'production'
            elif res.stock_move_id.location_id.usage == 'internal' and res.stock_move_id.location_dest_id.usage == 'production':
                res.y_code = 'consumption'
            elif res.stock_move_id.location_id.usage == 'internal' and res.stock_move_id.location_dest_id.usage == 'internal':
                res.y_code = 'internal'
            elif res.stock_move_id.location_id.usage == 'inventory' and res.stock_move_id.location_dest_id.usage == 'internal':
                res.y_code = 'positive_adjustment'
            elif res.stock_move_id.location_id.usage == 'internal' and res.stock_move_id.location_dest_id.usage == 'inventory':
                res.y_code = 'negative_adjustment'

        elif not res.stock_move_id and not res.stock_landed_cost_id:
            res.y_code = 'revaluation'
        elif not res.stock_move_id and res.stock_valuation_layer_id:
            res.y_code = 'price_diff'

            
        return res
    
    def update_operation_type(self):
        for rec in self:
            if rec.stock_move_id and rec.stock_move_id.location_id and rec.stock_move_id.location_id.usage and rec.stock_move_id.location_dest_id and rec.stock_move_id.location_dest_id.usage:
                if rec.stock_move_id and rec.stock_landed_cost_id:
                   rec.y_code = 'landed_cost'
                elif rec.stock_move_id.location_id.usage == 'supplier' and rec.stock_move_id.location_dest_id.usage == 'internal':
                    rec.y_code = 'incoming'
                elif rec.stock_move_id.location_id.usage == 'internal' and rec.stock_move_id.location_dest_id.usage == 'supplier':
                    rec.y_code = 'incoming_return'
                elif rec.stock_move_id.location_id.usage == 'internal' and rec.stock_move_id.location_dest_id.usage == 'customer':
                    rec.y_code = 'outgoing'
                elif rec.stock_move_id.location_id.usage == 'customer' and rec.stock_move_id.location_dest_id.usage == 'internal':
                    rec.y_code = 'outgoing_return'
                elif rec.stock_move_id.location_id.usage == 'production' and rec.stock_move_id.location_dest_id.usage == 'internal':
                    rec.y_code = 'production'
                elif rec.stock_move_id.location_id.usage == 'internal' and rec.stock_move_id.location_dest_id.usage == 'production':
                    rec.y_code = 'consumption'
                elif rec.stock_move_id.location_id.usage == 'internal' and rec.stock_move_id.location_dest_id.usage == 'internal':
                    rec.y_code = 'internal'
                elif rec.stock_move_id.location_id.usage == 'inventory' and rec.stock_move_id.location_dest_id.usage == 'internal':
                    rec.y_code = 'positive_adjustment'
                elif rec.stock_move_id.location_id.usage == 'internal' and rec.stock_move_id.location_dest_id.usage == 'inventory':
                    rec.y_code = 'negative_adjustment'

            elif not rec.stock_move_id and not rec.stock_landed_cost_id:
                rec.y_code = 'revaluation'
            elif not res.stock_move_id and res.stock_valuation_layer_id:
                res.y_code = 'price_diff'

    

