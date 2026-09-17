# -*- coding: utf-8 -*-

from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError

class Purchasetoleranceinventry(models.Model):
    _inherit='product.template'

    y_product_sourcing = fields.Boolean(string='Product Sourcing')
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
        
    @api.onchange('product_id', 'order_id.partner_id','order_id.company_id')
    def _onchange_product_ids(self):
        for line in self:
            if line.product_id.product_tmpl_id.y_product_sourcing == True:
                product_ids = self._get_vendor_pricelist_ids(line.partner_id, line.order_id.company_id)
                if not product_ids or line.product_id.id not in product_ids:
                    raise ValidationError(_(""" No valid vendor price list found for this vendor. Create a vendor price list."""))
    
    # @api.onchange('product_id')
    # def _onchange_product_id_list(self):
    #     for line in self:
    #         vendor_price_list = self.env['product.supplierinfo'].search([('partner_id','=',line.partner_id.id),('product_tmpl_id.product_sourcing','=',True)])
    #         res = {}
    #         if len(vendor_price_list):
    #             for rec in vendor_price_list:
    #                 res['domain'] = {'product_id':[('seller_ids.partner_id','=',line.partner_id.id),('product_sourcing','=',True)]}
    #         else:
    #             res['domain'] = {'product_id':[('product_sourcing','=',False),('purchase_ok','=',True)]}
    #         return res


                            
    def _get_vendor_pricelist_ids(self, partner, company):
        product_ids = []
        if partner:
            partner_id = partner.id
            query = """
                SELECT pp.id
                FROM product_product pp
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_supplierinfo psi ON pp.product_tmpl_id = psi.product_tmpl_id
                WHERE psi.partner_id = %s
                AND pt.purchase_ok = TRUE AND pt.y_product_sourcing = TRUE
            """
            self.env.cr.execute(query, (partner_id,))
            product_ids = [row[0] for row in self.env.cr.fetchall()]

        # if not product_ids:
        #     company_id = company.id
        #     query = """
        #         SELECT pp.id
        #         FROM product_product pp
        #         LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        #         WHERE pt.purchase_ok = TRUE AND pt.y_product_sourcing = TRUE
        #         AND (pt.company_id IS NULL OR pt.company_id = CAST(%s AS INTEGER))
        #     """
        #     self.env.cr.execute(query, (company_id,))
        #     product_ids = [row[0] for row in self.env.cr.fetchall()]

        return product_ids
