from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    y_is_registered_company = fields.Boolean(string='Is Registered Company', default=True)
    
    