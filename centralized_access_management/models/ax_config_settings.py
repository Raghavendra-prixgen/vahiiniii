from odoo import models, fields, api
import ipaddress
from odoo.exceptions import ValidationError, AccessDenied

# ip address
class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"


    unauthorized_notification_enabled = fields.Boolean(
        string="Notify on Unauthorized Login Attempts",
        help="Toggle this option to receive email notifications whenever an unauthorized login attempt is detected."
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            unauthorized_notification_enabled=self.env["ir.config_parameter"]
            .sudo()
            .get_param("unauthorized_notification_enabled", default=False)
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "unauthorized_notification_enabled", self.unauthorized_notification_enabled
        )







