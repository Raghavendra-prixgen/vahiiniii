# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MaintenanceRequestInherit(models.Model):
    _inherit = "maintenance.request"

    y_purchase_order = fields.Many2one('purchase.order',string='Service Purchase Order')
    y_material_purchase_order = fields.Many2one('purchase.order',string='Material Purchase Order')
    y_vendor = fields.Many2many('res.partner',string="Vendor")

    @api.onchange('stage_id')
    def onchange_stage_id_for_purchase(self):
        if self.y_purchase_order and self.stage_id:
            if self.stage_id.done:
                for each in self.y_purchase_order.order_line:
                    each.write({'qty_received':1})
        elif self.y_material_purchase_order and self.stage_id:
            if self.stage_id.done:
                for each in self.y_material_purchase_order.order_line:
                    each.write({'qty_received':1})




class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    y_hsn_code = fields.Char(
        string="HSN Code",
        store=True,
    )

    y_uom_id = fields.Many2one(
        'uom.uom',
        string="UOM",
    )


class PurchaseDocType(models.Model):
    _inherit = 'purchase.doc.type'

    y_is_maintenance_request = fields.Boolean(
        string="Is Maintenance Request",
        help="If checked, purchase orders/agreements using this document "
             "type will require the Maintenance Request field to be filled.",
    )

