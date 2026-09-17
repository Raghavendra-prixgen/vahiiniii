from odoo import api, fields, models




class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    y_department_id = fields.Many2one('department.stocks',string="Department")
    y_maintenance_equipment_id = fields.Many2one('maintenance.equipment',string="Machine")
