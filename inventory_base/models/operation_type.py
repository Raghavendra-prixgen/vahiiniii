from odoo import models, fields, api, exceptions, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    y_is_valuation = fields.Boolean("Valuation Posted ")
    y_valuation_value = fields.Float("Valuation Value")
    y_operation_type = fields.Selection([('incoming', 'Receipt'), ('incoming_return', 'Purchase Return'), ('outgoing', 'Delivery'), ('outgoing_return', 'Sale Return'), 
                             ('internal', 'Internal Transfer'),('production', 'Production'),('consumption', 'Consumption'),
                             ('positive_adjustment', 'Positive Adjustment'),('negative_adjustment', 'Negative Adjustment'),
                             ('transit_pos', 'Positive Transit'),('in_transit_neg', 'Negative Transit')], string='Type of Transaction')
    
    @api.model
    def create(self, vals_list):
        res = super(StockMove, self).create(vals_list)
        res.update_operation_type()
        return res
    
    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        res.update_valuation()
        return res

    def update_valuation(self):
        for each in self:
            valuation_ids = each.stock_valuation_layer_ids.filtered(lambda x:not x.stock_landed_cost_id)
            if valuation_ids:
                each.y_is_valuation = True
                each.y_valuation_value = sum(valuation_ids.mapped('value'))

    def update_operation_type(self):
        for rec in self:
            if rec and rec.location_id and rec.location_id.usage and rec.location_dest_id and rec.location_dest_id.usage:
                if rec.location_id.usage == 'supplier' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'incoming'
                elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'supplier':
                    rec.y_operation_type = 'incoming_return'
                elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'customer':
                    rec.y_operation_type = 'outgoing'
                elif rec.location_id.usage == 'customer' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'outgoing_return'
                elif rec.location_id.usage == 'production' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'production'
                elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'production':
                    rec.y_operation_type = 'consumption'
                elif rec.location_id.usage == 'y_operation_type' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'internal'
                elif rec.location_id.usage == 'inventory' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'positive_adjustment'
                elif rec.location_id.usage == 'internal' and rec.location_dest_id.usage == 'inventory':
                    rec.y_operation_type = 'negative_adjustment'
                elif rec.location_id.usage =='internal' and rec.location_dest_id.usage == 'transit':
                    rec.y_operation_type = 'in_transit_neg'
                elif rec.location_id.usage =='transit' and rec.location_dest_id.usage == 'internal':
                    rec.y_operation_type = 'transit_pos'
