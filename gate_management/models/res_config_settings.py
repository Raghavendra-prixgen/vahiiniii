#-*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    y_inward_sequence = fields.Many2one("ir.sequence", string="Inward Sequence")
    y_outward_sequence = fields.Many2one("ir.sequence", string="Outward Sequence")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            y_inward_sequence = int(params.get_param('gate_management.y_inward_sequence')) or False,
            y_outward_sequence = int(params.get_param('gate_management.y_outward_sequence')) or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('gate_management.y_inward_sequence',self.y_inward_sequence.id)
        self.env['ir.config_parameter'].sudo().set_param('gate_management.y_outward_sequence',self.y_outward_sequence.id)

