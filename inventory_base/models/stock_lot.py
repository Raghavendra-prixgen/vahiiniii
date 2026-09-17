# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StockLot(models.Model):
    _inherit = "stock.lot"

    def write(self, vals):
        if 'standard_price' in vals:
            for lot in self:
                old_cost = lot.with_company(lot.env.company).standard_price
                new_cost = vals.get('standard_price')
                lot.message_post(body="Company: {} - Cost : {} ---> {}".format(lot.env.company.name,old_cost,new_cost))
        return super().write(vals)

