# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductWeight(models.Model):
    _inherit = "product.template"

    y_toggle_button = fields.Boolean('Weight Calibration',default=False,store=True)    



                    







   