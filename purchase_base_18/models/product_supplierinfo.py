from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ProductSupplierinfo(models.Model):
    _name = "product.supplierinfo"
    _inherit = ['product.supplierinfo','mail.thread', 'mail.activity.mixin']

    discount = fields.Float(tracking=True)
    partner_id = fields.Many2one(tracking=True)
    product_name = fields.Char(tracking=True)
    min_qty = fields.Float(tracking=True)
    price = fields.Float(tracking=True)
    product_tmpl_id = fields.Many2one(tracking=True)
    product_uom = fields.Many2one(tracking=True)
    active = fields.Boolean(default=True)

    y_product_uom_category_id = fields.Many2one(related='product_tmpl_id.uom_po_id.category_id')
    y_uom_product = fields.Many2one('uom.uom',string="Purchase UOM",tracking=True)

    y_purchase_tol_reqd = fields.Boolean(string='Purchase Tolerance',tracking=True)
    y_ven_pricelist_tolerance = fields.Float(string='Purchase Tolerance %',default=0.0,tracking=True)

    @api.constrains('y_ven_pricelist_tolerance')
    def _check_percentage_limit(self):
        for record in self:
            if record.y_ven_pricelist_tolerance > 100:
                raise UserError("Purchase Tolerance Percentage cannot be more than 100%.")