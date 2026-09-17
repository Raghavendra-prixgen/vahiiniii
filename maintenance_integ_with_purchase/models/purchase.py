# -*- coding: utf-8 -*-

from odoo import models, fields, api, _



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    y_maintenance_request = fields.Many2many('maintenance.request',string="Maintenance Request",domain=[('stage_id.job_work','=', True)])

    y_is_maintenance_request = fields.Boolean(
        related='y_doc_type_id.y_is_maintenance_request',
        store=False,
    )

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        res = super(PurchaseOrder,self)._onchange_requisition_id()
        self.y_maintenance_request = self.requisition_id.y_maintenance_request.ids

        return res

    def button_confirm(self):
        res = super(PurchaseOrder,self).button_confirm()
        if self.y_maintenance_request:
            for line in self.order_line:
                for each in self.y_maintenance_request:
                    if line.product_id.type == "service":
                        each.write({'y_purchase_order':self.id,'y_vendor':[(6, 0, self.partner_id.ids)]})
                    elif line.product_id.type == "consu" or line.product_id.type == "product":
                        each.write({'y_material_purchase_order':self.id,'y_vendor':[(6, 0, self.partner_id.ids)]})

        return res

class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"
    
    y_maintenance_request = fields.Many2many('maintenance.request',string="Maintenance Request",domain=[('stage_id.job_work','=', True)])