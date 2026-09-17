# -*- coding: utf-8 -*-

from odoo import models, fields, api

class NetOffSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    net_off_account_journal_id = fields.Many2one(
        'account.journal',
        config_parameter='net_off_account_journal_id',
        string="Net Off Journal"
    )