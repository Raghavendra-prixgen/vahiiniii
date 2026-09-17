# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_round, float_compare
# import logging
# _logger = logging.getLogger(__name__)
# class NonMatchingDistribution(Exception):
#     pass


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'
    
    business_unit = fields.Boolean()

    @api.onchange('business_unit','default_applicability','applicability_ids.applicability')
    def _onchange_business_unit(self):        
        if self.business_unit and self.default_applicability != 'mandatory':
            self.default_applicability = 'mandatory'
        
        if self.business_unit:
            for line in self.applicability_ids:
                if line.applicability != 'mandatory':
                    line.applicability = 'mandatory'


    def write(self, vals):
        res =  super().write(vals)
        self._onchange_business_unit()
        return res

    @api.model_create_multi
    def create(self, vals):
        res =  super().create(vals)
        for rec in res:
            rec._onchange_business_unit()
        return res


class AccountAnalyticApplicability(models.Model):
    _inherit = 'account.analytic.applicability'

    business_domain = fields.Selection(
        selection_add=[
            ('stock_move_and_line', 'Inventory'),
            ('mrp','Manufacturing'),
            ('payment', 'Payment'),
        ],
        ondelete={
            'stock_move_and_line': 'cascade',
            'mrp': 'cascade',
            'payment': 'cascade',
        },
    )


    def write(self, vals):
        res =  super().write(vals)
        self.analytic_plan_id._onchange_business_unit()
        return res

    @api.model_create_multi
    def create(self, vals):
        res =  super().create(vals)
        for rec in res:
            rec.analytic_plan_id._onchange_business_unit()
        return res


class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    # user_ids = fields.Many2many('res.users', string='User')

    # def _check_score(self, key, value):
    #     self.ensure_one()
    #     if key == 'company_id':
    #         if not self.company_id or value == self.company_id.id:
    #             return 1 if self.company_id else 0.5
    #         raise NonMatchingDistribution
    #     if not self[key]:
    #         return 0
    #     if value and ((self[key].id in value) if isinstance(value, (list, tuple))
    #                   else (value.startswith(self[key])) if key.endswith('_prefix')
    #                   else (value in self[key].ids) if key.endswith('_ids')
    #                   else (value == self[key].id)
    #                   ):
    #         return 1
    #     return 0

    # @api.model
    # def _get_distribution(self, vals):
    #     """ Returns the distribution model that has the most fields that corresponds to the vals given
    #         This method should be called to prefill analytic distribution field on several models """
    #     domain = []
    #     for fname, value in vals.items():
    #         domain += self._create_domain(fname, value) or []
    #     best_score = 0
    #     res = {}
    #     fnames = set(self._get_fields_to_check())
    #     # _logger.info("{}".format(domain))
    #     for rec in self.search(domain):
    #         # try:
    #         score = sum(rec._check_score(key, vals.get(key)) for key in fnames)
    #         if score > best_score:
    #             res = rec.analytic_distribution
    #             best_score = score
    #         # except NonMatchingDistribution:
    #         #     continue
    #     return res