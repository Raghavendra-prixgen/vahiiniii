# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command
from odoo.exceptions import AccessError, UserError, ValidationError
import pytz
from datetime import datetime, timedelta,date
from odoo.tools import SQL

class ProductCategory(models.Model):
    _inherit = 'product.category'

    y_is_bought_out = fields.Boolean("Bought Out")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_valuation_reference = fields.Char(string="Valuation Reference",
                                        copy=False,
                                        compute="_compute_stock_valuation_layer_reference",
                                        store=True)

    y_type_of_transaction = fields.Selection([('incoming', 'Receipt'), 
                                              ('incoming_return', 'Purchase Return'), 
                                              ('outgoing', 'Delivery'), 
                                              ('outgoing_return', 'Sale Return'),
                                              ('internal', 'Internal Transfer'),
                                              ('production', 'Production'),
                                              ('consumption', 'Consumption'),
                                              ('positive_adjustment', 'Positive Adjustment'),
                                              ('negative_adjustment', 'Negative Adjustment'),
                                              ('landed_cost', 'Landed Cost'),
                                              ('revaluation', 'Revaluation'),
                                              ('price_diff','Price Diffrence')],
                                              copy=False,
                                              string='Type of Transaction',
                                              compute="_compute_stock_valuation_layer_code",
                                              store=True)


    y_entry_type = fields.Selection([('purchase_goods','Purchase of Goods'),
                                       ('sale_goods','Sale of Goods'),
                                       ('purchase_services','Purchase of Services'),
                                       ('sale_services','Sale of Services'),
                                       ('purchase_assets','Purchase of Assets'),
                                       ('sale_assets','Sale of Assets'),
                                       ],string="Pur/Sale Entry Type",compute="_compute_product_document_status",store=True)

    y_is_bought_out = fields.Boolean(string="Bought-out",related="product_category_id.y_is_bought_out",store=True)

    @api.depends('move_id.stock_valuation_layer_ids')
    def _compute_stock_valuation_layer_code(self):
        for line in self:
            line.y_type_of_transaction = False
            if line.move_id.stock_valuation_layer_ids:
                stock_valuation_layer_id = line.move_id.stock_valuation_layer_ids[0]
                line.y_type_of_transaction = stock_valuation_layer_id.y_code
            elif line.cogs_origin_id.y_stock_picking_ref:
                if line.cogs_origin_id.y_stock_picking_ref.sale_id:
                    line.y_type_of_transaction = 'outgoing'
            elif line.y_stock_picking_ref and line.display_type == 'product':
                if line.y_stock_picking_ref.purchase_id:
                    line.y_type_of_transaction = 'incoming'



    @api.depends('move_id.stock_valuation_layer_ids','y_stock_picking_ref')
    def _compute_stock_valuation_layer_reference(self):
        for line in self:
            line.y_valuation_reference = False
            if line.move_id.stock_valuation_layer_ids:
                stock_valuation_layer_id = line.move_id.stock_valuation_layer_ids[0]
                line.y_valuation_reference = stock_valuation_layer_id.reference
            elif line.y_stock_picking_ref:
                line.y_valuation_reference = line.y_stock_picking_ref.name
            elif line.cogs_origin_id.y_stock_picking_ref:
                line.y_valuation_reference = line.cogs_origin_id.y_stock_picking_ref.name


    @api.depends('product_id','move_type','account_id','move_id')
    def _compute_product_document_status(self):
        for line in self:
            line.y_entry_type = False
            if line.display_type == 'product' and (line.move_id.is_sale_document(include_receipts=True) or line.move_id.is_purchase_document(include_receipts=True)):
                if line.account_id.account_type == 'asset_fixed':
                    if line.move_id.is_sale_document(include_receipts=True):
                        line.y_entry_type = 'sale_assets'
                    elif line.move_id.is_purchase_document(include_receipts=True):
                        line.y_entry_type = 'purchase_assets'
                else:
                    if line.product_id.type == 'consu' and line.product_id.is_storable:
                        if line.move_id.is_sale_document(include_receipts=True):
                            line.y_entry_type = 'sale_goods'
                        elif line.move_id.is_purchase_document(include_receipts=True):
                            line.y_entry_type = 'purchase_goods'
                    elif (line.product_id and not line.product_id.is_storable) or (not line.product_id and line.account_id):
                        if line.move_id.is_sale_document(include_receipts=True):
                            line.y_entry_type = 'sale_services'
                        elif line.move_id.is_purchase_document(include_receipts=True):
                            line.y_entry_type = 'purchase_services'

