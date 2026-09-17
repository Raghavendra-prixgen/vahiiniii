# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountAssets(models.Model):
    _inherit = 'account.asset'

    y_quantity = fields.Float('Quantity',default=1)
    y_equipment_counts = fields.Integer(compute='_compute_equipments_count',string="Equipments Count")

    def _compute_equipments_count(self):
        equipments_data = self.env['maintenance.equipment'].read_group([('y_account_assets_id', 'in', self.ids)], ['y_account_assets_id'], ['y_account_assets_id'])
        mapped_data = dict([(m['y_account_assets_id'][0], m['account_assets_id_count']) for m in equipments_data])
        for asset in self:
            asset.y_equipment_counts = mapped_data.get(asset.id, 0)

    def equipments_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipments',
            'view_mode': 'kanban,list,form',
            'res_model': 'maintenance.equipment',
            'domain': [('y_account_assets_id', '=', self.id)],
            'context': "{'create': False}"
        }