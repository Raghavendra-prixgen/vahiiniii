# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class Location(models.Model):
    _name = "stock.location"
    _inherit = ['stock.location','mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    usage = fields.Selection(tracking=True)
    location_id = fields.Many2one(tracking=True)
    removal_strategy_id = fields.Many2one(tracking=True)
    valuation_in_account_id = fields.Many2one(tracking=True)
    valuation_out_account_id = fields.Many2one(tracking=True)
    
    @api.onchange('usage')
    def _onchange_usage_new(self):
        for rec in self:
            stock_quant = self.env['stock.quant'].search([('location_id','=',rec._origin.id)])
            quant_quantity = sum(stock_quant.mapped('quantity'))
            if quant_quantity > 0:
                raise ValidationError(_("""Cannot Change Costing Method once transactions are posted. Please contact Administrator to proceed further."""))
            
