# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import pdb
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from datetime import datetime, timedelta,date


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_salesperson = fields.Boolean(string="Is salesperson", store=True)

    


class CrmLead(models.Model):
    _inherit = "crm.lead"

    user_id = fields.Many2one(
        'res.users', string='Salesperson', default=lambda self: self.env.user,
        domain="[]",
        check_company=True, index=True, tracking=True)
