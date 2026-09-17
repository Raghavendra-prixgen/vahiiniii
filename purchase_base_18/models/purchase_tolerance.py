from odoo import fields, models,api,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class Purchasetoleranceinventry(models.Model):
    _inherit='product.template'

    y_purchase_tolerance = fields.Float(string=' Purchase Tolerance %',default=0.0,tracking=True)
    y_purchase_tol_reqd = fields.Boolean(string='Purchase Tolerance',tracking=True)

    @api.constrains('y_purchase_tolerance')
    def _check_percentage_limit(self):
        for record in self:
            if record.y_purchase_tolerance > 100:
                raise UserError("Purchase Tolerance Percentage cannot be more than 100%.")

class Purchasetolerancevariants(models.Model):
    _inherit='product.product'

    y_purchase_tolerance = fields.Float(string='Purchase Tolerance',default=0.0,tracking=True)

    @api.constrains('y_purchase_tolerance')
    def _check_percentage_limit(self):
        for record in self:
            if record.y_purchase_tolerance > 100:
                raise UserError("Purchase Tolerance Percentage cannot be more than 100%.")

class Validatepurchasetolerance(models.Model):
    _inherit="stock.picking"
   
    def button_validate(self):
        for picking in self:
            if not picking.move_ids and not picking.move_line_ids:
                raise UserError(_('Please add some items to move.'))
           
            if picking.move_ids_without_package and picking.picking_type_id.code!='internal':
                for line in picking.move_ids_without_package:
                    if line.quantity > line.product_uom_qty:
                        pricelist = line.product_id.seller_ids.filtered(lambda x:x.partner_id == picking.partner_id and x.company_id == picking.company_id)
                        if len(pricelist) > 1:
                            raise UserError(_('Vendor has {} configured multiple price list'.format(line.product_id.seller_ids.partner_id.name)))
                        if line.product_id.y_purchase_tol_reqd == True or pricelist.y_purchase_tol_reqd == True: 
                            if picking.partner_id.id in line.product_id.seller_ids.partner_id.ids and pricelist.y_purchase_tol_reqd == True:
                                if (line.quantity - line.product_uom_qty) > ((line.product_uom_qty / 100) * pricelist.y_ven_pricelist_tolerance):
                                    raise UserError(_('GRN quantity is greater than PO quantity for {}. You can do {}%, of extra GRN over the PO quantity.'.format(line.product_id.name,pricelist.y_ven_pricelist_tolerance)))
                            elif (line.quantity - line.product_uom_qty) > ((line.product_uom_qty / 100) * line.product_id.y_purchase_tolerance) and line.product_id.y_purchase_tol_reqd == True:
                                    raise UserError(_('GRN quantity is greater than PO quantity for {}. You can do {}%, of extra GRN over the PO quantity.'.format(line.product_id.name,line.product_id.y_purchase_tolerance)))
                            
        return super(Validatepurchasetolerance,self).button_validate()


