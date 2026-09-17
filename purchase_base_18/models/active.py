# -*- coding: utf-8 -*-

from odoo import models, api, fields,_

class ProductCategory(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean(default=True)

class UomCategory(models.Model):
    _inherit = 'uom.category'

    active = fields.Boolean(default=True)