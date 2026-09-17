from odoo import models, fields

# for ipaddress
class UnauthorizedAccessLog(models.Model):
    _name = 'unauthorized.access.log'
    _description = "Log Entry for Unauthorized Login Attempts"
    _rec_name = 'ip_address'

    user_id = fields.Many2one(
        'res.users',
        string="User Account",
        readonly=True,
        help="User associated with the attempted unauthorized login."
    )

    ip_address = fields.Char(
        string="IP Address",
        readonly=True,
        help="IP address from which the unauthorized login attempt was made."
    )

    attempt_date = fields.Datetime(
        string="Attempt Time",
        default=fields.Datetime.now,
        readonly=True,
        help="Date and time when the unauthorized login attempt occurred."
    )
