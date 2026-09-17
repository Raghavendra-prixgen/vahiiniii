# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SaleDiscountLine(models.Model):
    _name = "sale.discount.lines"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description ='sale.discount.lines'
                
    y_sale_discount_id = fields.Many2one('sale.order', string='Order Reference', index=True, copy=False,tracking=True)
    y_state = fields.Selection(related="y_sale_discount_id.state")
    y_name = fields.Text(string='Description')
    y_category = fields.Many2one('item.group',string="Item Group",required=True)
    y_amount = fields.Monetary("Amount",currency_field='y_currency_id')
    y_amount_rounding = fields.Monetary(currency_field='y_currency_id',string="Rouning Amount")
    y_trade_discount_id = fields.Many2one('sale.discount',string=" Trade Discount" ,domain="[('y_discount_type','=','trade')]",store=True)
    y_trade_discounts = fields.Float(string=' Trade Discount (%)', digits=(12,2), store=True,tracking=2)
    y_trade_amount = fields.Float('     Amount', digits=(12,2), default=0.0,store=True,compute="_compute_discounts",tracking=True)
    y_quantity_discount_id = fields.Many2one('sale.discount',string="Quantity Discount",domain="[('y_discount_type','=','quantity')]",store=True)
    y_quantity_discount = fields.Float(string=' Quantity Discount (%)', digits=(12,2),store=True)
    y_quantity_amount = fields.Float(' Amount ', digits=(12,2), default=0.0,store=True,compute="_compute_discounts",tracking=True)
    y_special_discount_id = fields.Many2one('sale.discount',string="Special Discount",domain="[('y_discount_type','=','special')]",store=True)
    y_special_discount = fields.Float(string='Special Discount (%)', digits=(12,2),store=True)
    y_special_amount = fields.Float(' Amount', digits=(12,2), default=0.0,store=True,compute="_compute_discounts",tracking=True)

    y_currency_id = fields.Many2one('res.currency', related='y_sale_discount_id.currency_id', store=True, readonly=True)
    y_base = fields.Monetary(string='Base', store=True,currency_field='y_currency_id')
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tds.")
    y_manual = fields.Boolean(string="Manual")
    y_total_discount_amount = fields.Float("Total Discount Amount",compute="get_total_discount_amount",store=True)

    @api.depends('y_amount','y_trade_discounts','y_quantity_discount','y_special_discount')
    def _compute_discounts(self):
    	for line in self:
            line.y_trade_amount = (line.y_amount * line.y_trade_discounts)/100
            line.y_quantity_amount = ((line.y_amount - line.y_trade_amount) * line.y_quantity_discount)/100
            line.y_special_amount = (((line.y_amount - line.y_trade_amount)-line.y_quantity_amount) * line.y_special_discount)/100

    @api.depends("y_trade_amount","y_quantity_amount","y_special_amount")
    def get_total_discount_amount(self):
        for each_line in self:
            each_line.y_total_discount_amount = each_line.y_trade_amount + each_line.y_quantity_amount + each_line.y_special_amount