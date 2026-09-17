from odoo import api, fields, models

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    y_gst = fields.Char(string="GST")
    y_project_place = fields.Char(string="Project Place")
   