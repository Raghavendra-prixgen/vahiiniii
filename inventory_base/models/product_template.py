# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def default_get(self, fields):
        result = super(ProductTemplate, self).default_get(fields)
        if result.get('categ_id') and not self.env['product.category'].search([('id','=',result.get('categ_id')),('y_release','!=',False)]):
                del result['categ_id']
        return result

    categ_id = fields.Many2one(default=False,domain=[('y_release', '=', True)])

    y_allow_negative_stock = fields.Boolean(string='Allow Negative Stock',help="If this option is not active on this product nor on its "
        "product category and that this product is a stockable product, "
        "then the validation of the related stock moves will be blocked if "
        "the stock level becomes negative with the stock move.")

    y_internal_reference_sequence = fields.Boolean(compute='compute_internal_reference',string="Internal Reference Sequence",store=True)
    default_code = fields.Char('Internal Reference', compute=False,inverse='_set_default_code', store=True,tracking=True)

    def _prepare_variant_values(self, combination):
        res = super()._prepare_variant_values(combination)
        res['default_code'] = self.default_code
        return res

    @api.depends('categ_id')
    def compute_internal_reference(self):
        for line in self:
            if line.categ_id.y_internal_reference_sequence_id:
                line.y_internal_reference_sequence = True
            else:
                line.y_internal_reference_sequence = False

    @api.model
    def create(self,vals):
        sequence = self.env['product.category'].browse(vals.get('categ_id')).y_internal_reference_sequence_id
        if sequence:
            vals['default_code'] = sequence.next_by_id()
        
        return super(ProductTemplate,self).create(vals)

    @api.onchange('categ_id')
    def _validate_categ_changer(self):
        for product in self:
            stock_quant = self.env['stock.quant'].search([('product_id.product_tmpl_id', '=',product._origin.id),('location_id.usage','=','internal'),('inventory_quantity_auto_apply','>',0)])
            quant_quantity = sum(stock_quant.mapped('inventory_quantity_auto_apply'))
            if self.categ_id and not self.env.user.has_group('inventory_base.group_prod_categ_change'):
                raise ValidationError(_("""You do not have access to change the Product Category"""))
            if quant_quantity > 0:
                    raise ValidationError(_("""Cannot Change Product category once transactions are posted. Please contact Administrator to proceed further."""))
                
    @api.onchange('tracking')
    def _onchange_tracking_new(self):
        for product in self:
            product_lot = self.env['stock.lot'].search([('product_id.product_tmpl_id', '=',product._origin.id)])
            if product_lot:
                raise ValidationError(_("""Cannot Change Tracking once transactions are posted. Please contact Administrator to proceed further."""))
    