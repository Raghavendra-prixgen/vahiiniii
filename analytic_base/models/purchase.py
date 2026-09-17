# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_round, float_compare
# import logging
# _logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    def _validate_analytic_distribution(self):
        for line in self.filtered(lambda l: not l.display_type):
            #enforce analytic validation
            line.with_context(validate_analytic = True)._validate_distribution(**{
                'product': line.product_id.id,
                'business_domain': 'purchase_order',
                'company_id': line.company_id.id,
            })
    
    @api.depends('product_id', 'order_id.partner_id','order_id.picking_type_id.warehouse_id')
    def _compute_analytic_distribution(self):
        for line in self:
            if not line.display_type:
                distribution = False
                if line.order_id.mrp_production_count:
                    src_mos = line.move_dest_ids.group_id.mrp_production_ids | line.move_ids.move_dest_ids.group_id.mrp_production_ids
                    if src_mos:
                        distribution = src_mos[0].analytic_distribution
                
                else:
                    distribution = self.env['account.analytic.distribution.model']._get_distribution({
                        "product_id": line.product_id.id,
                        "product_categ_id": line.product_id.categ_id.id,
                        "partner_id": line.order_id.partner_id.id,
                        "partner_category_id": line.order_id.partner_id.category_id.ids,
                        "company_id": line.company_id.id,
                        "warehouse_id": line.order_id.picking_type_id.warehouse_id.id,
                        # "user_ids": self.env.user.id,
                    })
                
                line.analytic_distribution = distribution or line.analytic_distribution