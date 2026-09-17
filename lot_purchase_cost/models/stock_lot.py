# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StockLot(models.Model):
    _inherit = "stock.lot"

    purchase_cost_per_unit = fields.Float(string="Purchase Cost Per Unit",digits='Product Price',compute='_compute_purchase_cost_per_unit_svl', compute_sudo=True)

    @api.depends('stock_valuation_layer_ids', 'product_id.lot_valuated')
    @api.depends_context('company')
    def _compute_purchase_cost_per_unit_svl(self):
        self.purchase_cost_per_unit = 0
        lots = self.filtered(lambda l: l.product_id.lot_valuated)
        if not lots:
            return
        company_id = self.env.company
        domain = [
            *self.env['stock.valuation.layer']._check_company_domain(company_id),
            ('lot_id', 'in', lots.ids),
            ('y_code','in',('incoming','incoming_return','landed_cost')),
        ]
        groups = self.env['stock.valuation.layer']._read_group(
            domain,
            groupby=['lot_id'],
            aggregates=['value:sum', 'quantity:sum'],
        )
        # Browse all lots and compute lots' quantities_dict in batch.
        group_mapping = {lot: aggregates for lot, *aggregates in groups}
        for lot in lots:
            value_sum, quantity_sum = group_mapping.get(lot._origin, (0, 0))
            avg_cost = value_sum / quantity_sum if quantity_sum else 0
            lot.purchase_cost_per_unit = avg_cost
