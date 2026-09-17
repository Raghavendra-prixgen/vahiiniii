import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_validate(self):
        self.move_id.filtered(lambda p: p.state == 'posted').state = 'draft'
        super().action_validate()