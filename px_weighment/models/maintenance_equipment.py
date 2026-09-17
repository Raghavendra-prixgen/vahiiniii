from odoo import models, fields, api, _

class Equipments(models.Model):
	_inherit = "maintenance.equipment"
	
	y_weight = fields.Integer(string="Weight")
	y_trolley = fields.Boolean(string="Is a Trolley")

class Fleet(models.Model):
	_inherit = "fleet.vehicle"
	
	y_weight = fields.Integer(string="Weight")
	y_vehicle = fields.Many2one('fleet.vehicle',string = "Vehicle")
	odometer = fields.Float(readonly=True)