from odoo import models, fields, api, _

class ProductTemplate(models.Model):
	_inherit = "product.template"

	y_tolerance = fields.Float(string="Weighment Tolerance")


