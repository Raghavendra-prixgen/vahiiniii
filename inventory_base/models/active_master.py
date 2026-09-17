# -*- coding: utf-8 -*-

from odoo import models, api, fields,_

class StockStorageCategoryCapacity(models.Model):
    _inherit = 'stock.storage.category.capacity'

    active = fields.Boolean(default=True)

class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    active = fields.Boolean(default=True)

class BarcodeNomenclature(models.Model):
    _inherit = 'barcode.nomenclature'

    active = fields.Boolean(default=True)