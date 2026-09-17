# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountAssets(models.Model):
    _inherit = 'maintenance.equipment'

    y_account_assets_id = fields.Many2one('account.asset',string="Assets")
    y_cost = fields.Float('Cost',tracking=True) 

    def button_generate_equipements(self):
        action = {
            'name': _("Generate Equipments"),
            'type': 'ir.actions.act_window',
            'res_model': 'generate.asset.equipment',
            'target': 'new',
            'context': {'create': False},
            'view_mode': 'form',
        }
        return action
        
    def update_cost(self):
        if not self.y_account_assets_id:
            raise UserError(_("No Asset Found"))
        if self.y_account_assets_id and self.y_account_assets_id.y_quantity > 0.0:
            self.y_cost = self.y_account_assets_id.book_value / self.y_account_assets_id.y_quantity
