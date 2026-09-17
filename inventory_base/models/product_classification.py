
from odoo import models, fields, api, _
from datetime import date,datetime
import time

class ProductClassfication(models.Model):
    _name= "product.classification"
    _description = "Product Classification"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Code")
    y_description = fields.Char(string="Description")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company)


class ProductTemplateNew(models.Model):
    _inherit = "product.template"

    y_product_classification_id = fields.Many2one('product.classification',string="Classification")

class ProductProductNew(models.Model):
    _inherit = "product.product"

    y_product_classification_id = fields.Many2one('product.classification',string="Classification")



