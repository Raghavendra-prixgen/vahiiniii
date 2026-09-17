from odoo import api, fields, models
from datetime import datetime, timedelta

class MaterialRequest(models.Model):
	_inherit = 'material.request'

	y_issues_by = fields.Char(string="Issues By")
	y_requested_by = fields.Char(string="Requested By")
	y_issued_to = fields.Char(string="Issued To")
	y_source_document = fields.Char(string="Source Document")



class MaterialRequestLine(models.Model):
    _inherit = 'material.request.line'

    y_department_id = fields.Many2one('department.stocks',string="Department")
    y_expense_id = fields.Many2one('expense.stocks')

    y_machine_id = fields.Many2one('mrp.workcenter',string="Machine Number")

    
