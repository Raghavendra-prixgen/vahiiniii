# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class ProductProcurementGroup(models.Model):
    _name = "product.procurement.group"
    _description = "Product Payment Group"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")
    y_is_critical = fields.Boolean(string="Is Critical")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")

class ProductProduct(models.Model):
    _inherit = "product.product"

    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group",copy=False)

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    @api.onchange('product_id', 'request_id.y_procurement_group_id')
    def _onchange_product_id_for_procurement_group(self):
        for line in self:
            if line.request_id.y_procurement_group_id and line.product_id:
                if line.product_id.y_procurement_group_id != line.request_id.y_procurement_group_id:
                    raise ValidationError(_("""The product procurement group does not match with the request procurement group."""))

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'order_id.y_procurement_group_id')
    def _onchange_product_id_for_procurement_group(self):
        for line in self:
            if line.order_id.y_procurement_group_id and line.product_id:
                if line.product_id.y_procurement_group_id != line.order_id.y_procurement_group_id:
                    raise ValidationError(_("""The product procurement group does not match with the purchase procurement group."""))