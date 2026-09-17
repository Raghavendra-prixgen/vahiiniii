# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_round, float_compare
# import logging
# _logger = logging.getLogger(__name__)

class MrpProduction(models.Model):
    _name = 'mrp.production'
    _inherit = ['mrp.production','analytic.mixin']


    def button_unbuild(self):
        res = super().button_unbuild()
        if res.get('context'):
            res.get('context')['default_analytic_distribution'] = self.analytic_distribution
        return res


    def _action_done(self):
        for move in self:
            move._validate_analytic_distribution()
        return super(MrpProduction, self)._action_done()

    @api.depends('mrp_production_source_count','sale_order_count','picking_type_id')
    def _compute_analytic_distribution(self):
        for mo in self:
            distribution = False
            
            if mo.sale_order_count:
                if mo.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.order_line.filtered(lambda sol: sol.product_id.id == mo.product_id.id):
                    distribution = mo.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.order_line.filtered(lambda sol: sol.product_id.id == mo.product_id.id)[0].analytic_distribution
            
            elif mo.mrp_production_source_count:
                mrp_production_sources = (mo.procurement_group_id.mrp_production_ids.move_dest_ids | mo.procurement_group_id.stock_move_ids.move_dest_ids).group_id.mrp_production_ids.filtered(lambda p: p.origin != mo.origin) - mo
                if mrp_production_sources:
                    distribution = mrp_production_sources[0].analytic_distribution
            
            elif mo.bom_id.type == 'subcontract':
                move_ids = (mo.procurement_group_id.stock_move_ids.move_dest_ids - mo.procurement_group_id.stock_move_ids)
                if move_ids:
                    distribution = move_ids[0].analytic_distribution
            
            else:
                distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": mo.product_id.id,
                    "product_categ_id": mo.product_id.categ_id.id,
                    "company_id": mo.company_id.id,
                    "warehouse_id": mo.picking_type_id.warehouse_id.id,
                    # "user_ids": self.env.user.id,
                })
            
            mo.analytic_distribution = distribution or mo.analytic_distribution

    
    def _validate_analytic_distribution(self):
        for line in self:
            #enforce analytic validation
            line.with_context(validate_analytic = True)._validate_distribution(**{
                'product': line.product_id.id,
                'business_domain': 'mrp',
                'company_id': line.company_id.id,
            })



class MrpUnbuild(models.Model):
    _name = "mrp.unbuild"
    _inherit = ['mrp.unbuild','analytic.mixin']





