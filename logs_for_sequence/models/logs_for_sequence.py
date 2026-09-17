from odoo import _, api, fields, models

class LogrulesSequence(models.Model):
    _name = "ir.sequence"
    _inherit = ['ir.sequence','mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    code = fields.Char(tracking=True)
    implementation = fields.Selection(tracking=True)
    active = fields.Boolean(tracking=True)
    prefix = fields.Char(tracking=True)
    suffix = fields.Char(tracking=True)
    number_next = fields.Integer(tracking=True)
    number_next_actual = fields.Integer(tracking=True)
    number_increment = fields.Integer(tracking=True)
    padding = fields.Integer(tracking=True)
    company_id = fields.Many2one(tracking=True)
    use_date_range = fields.Boolean(tracking=True)


   