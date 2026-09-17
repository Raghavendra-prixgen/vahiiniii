# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    y_is_storable_readonly = fields.Boolean(related="categ_id.y_is_storable",string="Is Storable Readonly")
    y_is_lot_valuated_readonly = fields.Boolean(related="categ_id.y_lot_valuated",string="Is Valuated Readonly")

    @api.constrains('lot_valuated')
    def check_lot_valuated_readonly_categ(self):
        for template in self:
            if template.lot_valuated != template.categ_id.y_lot_valuated:
                raise ValidationError("The valuation based on lot or serial numbers does not match the configuration of the product category.")
 

    @api.constrains('is_storable')
    def check_is_storable_categ(self):
        for template in self:
            if template.is_storable != template.categ_id.y_is_storable:
                raise ValidationError("The track inventory does not match the configuration of the product category.")

    @api.constrains('tracking')
    def check_lot_tracking_categ(self):
        for template in self:
            if template.is_storable:
                if template.tracking != template.categ_id.y_tracking:
                    raise ValidationError("The lot tracking inventory does not match the configuration of the product category.")


    @api.onchange('categ_id')
    def _onchange_categ_tracking(self):
        for product in self:
            if product.categ_id:
                categ_id = product.categ_id
                product.is_storable = categ_id.y_is_storable
                product.tracking = categ_id.y_tracking
                product.lot_valuated = categ_id.y_lot_valuated

class ProductCategory2(models.Model):
    _name = "product.category"
    _inherit = ['product.category','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    y_description = fields.Char('Description')
    y_release = fields.Boolean('Release',tracking=True)
    y_internal_reference_sequence_id = fields.Many2one('ir.sequence',string="Internal Reference Sequence")
    
    parent_id = fields.Many2one(tracking=True)
    name = fields.Char(tracking=True)
    removal_strategy_id = fields.Many2one(tracking=True)
    property_account_creditor_price_difference_categ = fields.Many2one(tracking=True)
    property_valuation = fields.Selection(tracking=True)
    property_stock_journal = fields.Many2one(tracking=True)
    property_stock_account_input_categ_id = fields.Many2one(tracking=True)
    property_stock_account_output_categ_id = fields.Many2one(tracking=True)
    property_stock_valuation_account_id = fields.Many2one(tracking=True)


    y_is_storable = fields.Boolean('Track Inventory',default=False,help='A storable product is a product for which you manage stock.')
    y_tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'By Quantity')],
        string="Tracking", default='none',
        help="Ensure the traceability of a storable product in your warehouse.")
    y_lot_valuated = fields.Boolean(
        "Valuation by Lot/Serial number",
        help="If checked, the valuation will be specific by Lot/Serial number.",
    )

    @api.onchange('property_cost_method')
    def _onchange_property_cost_new(self):
        for rec in self:
            line_ids = self.env['account.move.line'].search([('product_id.categ_id','=',rec._origin.id)])
            if line_ids:
                raise ValidationError(_("""Cannot Change Costing Method once transactions are posted. Please contact Administrator to proceed further."""))
            