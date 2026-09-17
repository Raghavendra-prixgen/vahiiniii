# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    y_destination_route = fields.Many2many('stock.route', string="Destination Route", domain="[('y_po_lines','=',True)]")

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.with_context(skipp_default_picking=True).button_approve(force=False)
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return res

    def _create_picking(self):
        res = super(PurchaseOrder, self)._create_picking()
        if self._context.get('skipp_default_picking'):
            self.purchase_route_button_confirm()
        else:
            StockPicking = self.env['stock.picking']
            for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
                if any(product.type == 'consu' for product in order.order_line.product_id):
                    order = order.with_company(order.company_id)
                    pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    if not pickings:
                        res = order._prepare_picking()
                        picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                        pickings = picking
                    else:
                        picking = pickings[0]
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    # Get following pickings (created by push rules) to confirm them as well.
                    forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                    (pickings | forward_pickings).action_confirm()
                    picking.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': picking, 'origin': order},
                        subtype_xmlid='mail.mt_note',
                    )
        return res


    def purchase_route_button_confirm(self):
        pickings = []
        for line in self.order_line:
            for route in line.y_destination_route:
                for rule in route.rule_ids:
                    vals = {
                            'partner_id': line.order_id.partner_id.id,
                            'location_id': rule.location_src_id and rule.location_src_id.id or False,
                            'location_dest_id': rule.location_dest_id and rule.location_dest_id.id or False,
                            'picking_type_id': rule.picking_type_id.id,
                            'origin': self.name,
                            'purchase_id': self.id,
                        }
                    picking = self.env['stock.picking'].create(vals)
                    
                    move_vals = {
                            'name': picking.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_qty,
                            'picking_id': picking.id,
                            'location_id': rule.location_src_id and rule.location_src_id.id or False,
                            'location_dest_id': rule.location_dest_id and rule.location_dest_id.id or False,
                            'product_uom': line.product_id.uom_id.id,
                            'purchase_line_id': line.id,
                        }
                    stock_move = self.env['stock.move'].create(move_vals)
                    picking.action_confirm()
                    pickings.append(picking.id)
        self.picking_ids = pickings
        
class StockLocationRoute(models.Model):
    _inherit = "stock.route"
    
    y_po_lines = fields.Boolean(string='Purchase Order Lines')
    

