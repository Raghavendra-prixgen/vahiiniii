from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class EquipmentBackorderConfirmationLine(models.TransientModel):
    _name = 'eq.backorder.confirmation.line'
    _description = ' Equipment Backorder Confirmation Line'

    equipment_backorder_confirmation_id = fields.Many2one('eq.backorder.confirmation', 'Immediate Transfer')
    equipment_delivery_id = fields.Many2one('equipment.request.delivery', 'Equipment Delivery')
    equipment_receipt_id = fields.Many2one('equipment.request.receipt', 'Equipment Receipt')
    to_backorder = fields.Boolean('To Backorder')
    equipment_delivery_line_id = fields.Many2one('equipment.request.delivery.line')
    equipment_receipt_line_id = fields.Many2one('equipment.request.receipt.line')
    qty_done = fields.Float(string="Done")


class EquipmentBackorderConfirmation(models.TransientModel):
    _name = 'eq.backorder.confirmation'
    _description = 'Backorder Confirmation'

    equipment_delivery_ids = fields.Many2many('equipment.request.delivery')
    equipment_receipt_ids = fields.Many2many('equipment.request.receipt', string='Equipment Receipts')

    equipment_request_line_ids = fields.Many2many('equipment.request.delivery.line')
    equipment_request_receipt_line_ids = fields.Many2many('equipment.request.receipt.line')
    show_transfers = fields.Boolean()
    equipment_backorder_confirmation_line_ids = fields.One2many(
        'eq.backorder.confirmation.line',
        'equipment_backorder_confirmation_id',
        string=" Equipment Backorder Confirmation Lines")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'equipment_backorder_confirmation_line_ids' in fields and res.get('equipment_delivery_ids'):
            print()
            res['equipment_backorder_confirmation_line_ids'] = [
                (0, 0, {'to_backorder': True, 'equipment_delivery_id': pick_id})
                for pick_id in res['equipment_delivery_ids'][0][2]
            ]

        if 'equipment_backorder_confirmation_line_ids' in fields and res.get('equipment_receipt_ids'):
            res['equipment_backorder_confirmation_line_ids'] = [
                (0, 0, {'to_backorder': True, 'equipment_receipt_id': pick_id})
                for pick_id in res['equipment_receipt_ids'][0][2]
            ]

        return res

    # onclick of process it will create new back order
    def process(self):
        if self.equipment_delivery_ids:
            for equipment_dr in self.equipment_delivery_ids:
                delivery_vals = {
                    'name': self.env['ir.sequence'].next_by_code('equipment.request.delivery') or 'New',
                    'partner_shipping_id': equipment_dr.partner_shipping_id.id,
                    'backorder_id': equipment_dr.id,
                    'scheduled_date': equipment_dr.scheduled_date,
                    'origin': 'Backorder of' + ' - ' + equipment_dr.name,
                    'deadline': equipment_dr.deadline,
                    'maintenance_related_id': equipment_dr.maintenance_related_id.id
                }
                equipment_dr_val_obj = self.env['equipment.request.delivery'].create(delivery_vals)
                equipment_dr_val = []
                for line_delivery_lines in equipment_dr.equipment_request_line_ids:
                    if line_delivery_lines.display_type not in ('line_section', 'line_note'):
                        equipment_dr_val.append({
                            'request_id': equipment_dr_val_obj.id,
                            'equipment_id': line_delivery_lines.equipment_id.id,
                            'maintenance_request_id': line_delivery_lines.maintenance_request_id.id,
                            'name': line_delivery_lines.name,

                            'equipment_delivery_line_id': line_delivery_lines.equipment_delivery_line_id.id,
                            'quantity': line_delivery_lines.quantity - line_delivery_lines.done,
                        })
                    else:
                        equipment_dr_val.append({
                            'request_id': equipment_dr_val_obj.id,
                            'name': line_delivery_lines.name,
                            'display_type': line_delivery_lines.display_type,
                            'equipment_delivery_line_id': line_delivery_lines.equipment_delivery_line_id.id,
                        })

                equipment_dr_val_line = self.env['equipment.request.delivery.line'].create(equipment_dr_val)
                for delivery_lines in equipment_dr.equipment_request_line_ids:
                    if delivery_lines.quantity != delivery_lines.done:
                        delivery_lines.quantity = delivery_lines.done

                equipment_dr.validate_delivery_to_receipt()
        elif self.equipment_receipt_ids:
            for equipment_dr in self.equipment_receipt_ids:
                receipt_vals = {
                    'name': self.env['ir.sequence'].next_by_code('equipment.request.receipt') or 'New',
                    'received_from_id': equipment_dr.received_from_id.id,
                    'backorder_id': equipment_dr.id,
                    'scheduled_date': equipment_dr.scheduled_date,
                    'origin': 'Backorder of' + ' - ' + equipment_dr.name,
                    'deadline': equipment_dr.deadline,
                    'receipt_to_delivery_id': equipment_dr.receipt_to_delivery_id.id,
                    'maintenance_related_receipt_id': equipment_dr.maintenance_related_receipt_id.id,

                }
                equipment_dr_val_obj = self.env['equipment.request.receipt'].create(receipt_vals)
                equipment_dr_val = []

                for line_receipt_lines in equipment_dr.equipment_request_receipt_line_ids:
                    if line_receipt_lines.display_type not in ('line_section', 'line_note'):

                        equipment_dr_val.append({
                            'request_id': equipment_dr_val_obj.id,
                            'equipment_id': line_receipt_lines.equipment_id.id,
                            'maintenance_request_id': line_receipt_lines.maintenance_request_id.id,

                            'equipment_receipt_line_id': line_receipt_lines.equipment_receipt_line_id.id,
                            'quantity': line_receipt_lines.quantity - line_receipt_lines.done,
                        })

                    else:
                        equipment_dr_val.append({
                            'request_id': equipment_dr_val_obj.id,
                            'name': line_receipt_lines.name,
                            'display_type': line_receipt_lines.display_type,
                            'equipment_receipt_line_id': line_receipt_lines.equipment_receipt_line_id.id,
                        })

                equipment_dr_val_line = self.env['equipment.request.receipt.line'].create(equipment_dr_val)
                for receipt_lines in equipment_dr.equipment_request_receipt_line_ids:
                    if receipt_lines.quantity != receipt_lines.done:
                        receipt_lines.quantity = receipt_lines.done

                equipment_dr.validate_receipt_to_equipment()

    # this is for cancel backorder
    def process_cancel_backorder(self):
        if self.equipment_delivery_ids:
            for equipment_dr in self.equipment_delivery_ids:
                for delivery_lines in equipment_dr.equipment_request_line_ids:
                    if delivery_lines.quantity != delivery_lines.done:
                        delivery_lines.quantity = delivery_lines.done
                        equipment_dr.validate_delivery_to_receipt()
        elif self.equipment_receipt_ids:
            for equipment_dr in self.equipment_receipt_ids:
                for receipt_lines in equipment_dr.equipment_request_receipt_line_ids:
                    if receipt_lines.quantity != receipt_lines.done:
                        receipt_lines.quantity = receipt_lines.done
                        equipment_dr.validate_receipt_to_equipment()

    def action_cancel(self):
        if self.equipment_delivery_ids:
            for equipment_dr in self.equipment_delivery_ids:
                for delivery_lines in equipment_dr.equipment_request_line_ids:
                    if delivery_lines.quantity != delivery_lines.done:
                        equipment_dr.state = 'draft'
        elif self.equipment_receipt_ids:
            for equipment_dr in self.equipment_receipt_ids:
                for receipt_lines in equipment_dr.equipment_request_receipt_line_ids:
                    if receipt_lines.quantity != receipt_lines.done:
                        equipment_dr.state = 'draft'
