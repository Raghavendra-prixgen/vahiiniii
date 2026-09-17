# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class GenerateEquipmentWiz(models.Model):
    _name = 'generate.asset.equipment'
    _description = 'generate equiments based on the assets'

    y_asset_id = fields.Many2one('account.asset',required=True,string="Asset")
    y_category_id = fields.Many2one('maintenance.equipment.category',string="Equipment Category")
    y_number_of_equiments = fields.Float('Number of Equipments')

    @api.onchange('y_asset_id')
    def update_number_of_equipements(self):
        if self.y_asset_id:
            self.y_number_of_equiments = self.y_asset_id.y_quantity

    def generate_equipments(self):
        if self.y_asset_id and self.y_number_of_equiments > 0.0:
            equipments_count =self.env['maintenance.equipment'].search_count([('y_account_assets_id', '=', self.y_asset_id.id)])
            if (equipments_count + self.y_number_of_equiments) > self.y_asset_id.y_quantity:
                raise UserError(_("Number of Equipments should not be greater than quantities of assets"))
            else:
                for each in range(int(self.y_number_of_equiments)):
                    self.env['maintenance.equipment'].create({
                            'name': self.y_asset_id.name,
                            'category_id': self.y_category_id.id,
                            'account_assets_id': self.y_asset_id.id,
                            'cost':self.y_asset_id.value_residual/self.y_asset_id.y_quantity,
                        })
                return True

