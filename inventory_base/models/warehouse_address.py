# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id, check_company=True,tracking=True)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    y_warehouse_address_id = fields.Many2one('res.partner',string="Warehouse Address",compute="_compute_warehouse_address",store=True)

    @api.depends('picking_type_id')
    def _compute_warehouse_address(self):
        for order in self:
            order.y_warehouse_address_id = order.picking_type_id.warehouse_id.partner_id.id

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    y_warehouse_address_id = fields.Many2one('res.partner',string="Warehouse Address",compute="_compute_warehouse_address",store=True)

    @api.depends('warehouse_id')
    def _compute_warehouse_address(self):
        for order in self:
            order.y_warehouse_address_id = order.warehouse_id.partner_id.id

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

