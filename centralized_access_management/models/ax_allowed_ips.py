from odoo import models, fields, api
import ipaddress
from odoo.exceptions import ValidationError, AccessDenied
from odoo import _, exceptions


class UserAllowedIPs(models.Model):
    _name = "allowed.ips"
    _description = "User Allowed IP Ranges"

    ip_address = fields.Char("IP Address", required=True)
    access_config_id = fields.Many2one("ax.access.model", string="Access Config", required=True)

    users_ip = fields.Many2one(
        "res.users",
        string="User",
        help="User for whom the IP access range is being configured."
    )

