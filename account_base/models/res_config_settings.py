#-*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    y_enable_custom_sequence = fields.Boolean(string="Enable Custom Sequence")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            y_enable_custom_sequence = bool(params.get_param('account_base.y_enable_custom_sequence')) or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('account_base.y_enable_custom_sequence',self.y_enable_custom_sequence)

