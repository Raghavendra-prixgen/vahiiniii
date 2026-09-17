from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EquipmentRequest(models.Model):
    _name = 'equipment.request.delivery'
    _description = 'Maintenance Request Delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda self: _('New'), string="Name", tracking=True)
    company_id = fields.Many2one('res.company', string="Company")
    partner_shipping_id = fields.Many2one('res.partner', string="Delivery Address", tracking=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now, tracking=True)
    origin = fields.Char(string="Source Document", tracking=True)
    deadline = fields.Datetime(string="Deadline", tracking=True)
    equipment_request_line_ids = fields.One2many('equipment.request.delivery.line', 'request_id', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        copy=False, index=True, readonly=True, store=True, tracking=True)

    delivery_to_receipt_id = fields.Many2one('equipment.request.receipt')

    y_remarks = fields.Html(string="Remarks")

    def _prepare_receipt_line_vals(self, line):
        return {
            'equipment_id': line.equipment_id.id,
            'quantity': line.quantity,
            'name': line.name,
            'maintenance_request_id': line.maintenance_request_id.id,
            'y_child_equipment_id': line.y_child_equipment_id.id if line.y_child_equipment_id else False,
        }

    def validate_delivery_to_receipt(self):
        vals = {
            'name': self.env['ir.sequence'].next_by_code('equipment.request.receipt'),
            'scheduled_date': self.scheduled_date,
            'received_from_id': self.partner_shipping_id.id,
            'origin': self.name,
            'receipt_to_delivery_id': self.id,
            'company_id': self.company_id.id,
        }

        equipment_request = self.env['equipment.request.receipt'].create(vals)

        for line in self.equipment_request_line_ids:

            # Skip validations for section/note lines
            if line.display_type in ('line_section', 'line_note'):
                equipment_request.write({
                    'equipment_request_receipt_line_ids': [(0, 0, {
                        'name': line.name,
                        'display_type': line.display_type,
                        'maintenance_request_id': line.maintenance_request_id.id,
                    })]
                })
                continue

            maintenance_equipment = line.maintenance_request_id.equipment_id

            # Child Equipment Validation
            if line.y_child_equipment_id:

                allocation = self.env['equipment.allocation'].search([
                    ('y_equipment_id', '=', line.maintenance_request_id.y_parent_equipment_id.id)
                ], order='id desc', limit=1)

                allocation_lines = allocation.y_line_ids.filtered(
                    lambda l: l.y_equipment_id == line.y_child_equipment_id
                )

                if not allocation_lines:
                    raise ValidationError(_(
                        "Child Equipment '%s' is not allocated in the Maintenance Request."
                    ) % line.y_child_equipment_id.display_name)

                allocated_qty = sum(allocation_lines.mapped('y_qty'))

                delivered_qty = sum(
                    self.equipment_request_line_ids.filtered(
                        lambda l:
                        l.display_type not in ('line_section', 'line_note')
                        and l.maintenance_request_id == line.maintenance_request_id
                        and l.y_child_equipment_id == line.y_child_equipment_id
                    ).mapped('quantity')
                )

                if delivered_qty > allocated_qty:
                    raise ValidationError(_(
                        "Total quantity %s for Child Equipment '%s' cannot exceed allocated quantity %s."
                    ) % (
                                              delivered_qty,
                                              line.y_child_equipment_id.display_name,
                                              allocated_qty
                                          ))

                equipment_to_validate = line.y_child_equipment_id

            else:
                equipment_to_validate = maintenance_equipment

            # Stock Validation
            if equipment_to_validate.quantity < line.quantity:
                raise ValidationError(_(
                    "Available quantity for Equipment '%s' is %s, but requested quantity is %s."
                ) % (
                                          equipment_to_validate.display_name,
                                          equipment_to_validate.quantity,
                                          line.quantity
                                      ))

            # Create Receipt Line
            equipment_request.write({
                'equipment_request_receipt_line_ids': [
                    (0, 0, self._prepare_receipt_line_vals(line))
                ]
            })

            # Reduce Stock
            equipment_to_validate.quantity -= line.quantity

        self.state = 'done'

    def receipt_equipment(self):
        return {
            'name': 'Receipt',
            'res_model': 'equipment.request.receipt',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'domain': [('receipt_to_delivery_id', '=', self.id)],
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('equipment.request.delivery')
        return super(EquipmentRequest, self).create(vals)


class EquipmentRequestsLine(models.Model):
    _name = "equipment.request.delivery.line"
    _description = "Equipment Request Line"

    company_id = fields.Many2one('res.company', related="request_id.company_id", store=True)
    request_id = fields.Many2one('equipment.request.delivery')
    equipment_delivery_line_id = fields.Many2one('equipment.request.delivery')
    maintenance_request_id = fields.Many2one('maintenance.request', domain="[('company_id','=',company_id)]")
    equipment_id = fields.Many2one('maintenance.equipment', string="Equipment",compute="_compute_equipment_id",store=True)
    quantity = fields.Float(string="Quantity")
    name = fields.Char(string="Name")

    sequence = fields.Integer(string="Sequence", default=10)

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    y_child_equipment_id = fields.Many2one('maintenance.equipment', string="Child Equipment")
    y_allowed_child_equipment_ids = fields.Many2many('maintenance.equipment',
                                                     compute='_compute_allowed_child_equipment_ids')

    @api.depends('maintenance_request_id', 'y_child_equipment_id')
    def _compute_equipment_id(self):
        for rec in self:
            rec.equipment_id = False

            if not rec.maintenance_request_id:
                continue

            equipment = rec.maintenance_request_id.equipment_id

            if not equipment:
                continue

            if equipment.y_type == 'parent':
                rec.equipment_id = equipment
            else:
                rec.equipment_id = rec.maintenance_request_id.y_parent_equipment_id
                self._compute_allowed_child_equipment_ids()


    @api.onchange('equipment_id', 'y_child_equipment_id')
    def onchange_equipment(self):
        for rec in self:

            if rec.y_child_equipment_id:
                parent_name = rec.equipment_id.name or ''
                child_name = rec.y_child_equipment_id.name or ''

                rec.write({
                    'name': f"{parent_name} - {child_name}",
                })

            elif rec.equipment_id:
                rec.write({
                    'name': rec.equipment_id.name,
                })

    @api.depends('maintenance_request_id')
    def _compute_allowed_child_equipment_ids(self):
        Allocation = self.env['equipment.allocation']

        for rec in self:
            rec.y_allowed_child_equipment_ids = False

            if not rec.maintenance_request_id:
                continue

            # Get the parent equipment
            if rec.maintenance_request_id.equipment_id.y_type == 'parent':
                parent_equipment = rec.maintenance_request_id.equipment_id
            else:
                parent_equipment = rec.maintenance_request_id.y_parent_equipment_id

            if not parent_equipment:
                continue

            allocation = Allocation.search(
                [('y_equipment_id', '=', parent_equipment.id)],
                order='id desc',
                limit=1
            )

            rec.y_allowed_child_equipment_ids = allocation.y_line_ids.mapped('y_equipment_id')
            print('allocation---------------',allocation)
            print('rec.y_allowed_child_equipment_ids---------------',rec.y_allowed_child_equipment_ids)

    @api.constrains('quantity', 'y_child_equipment_id', 'maintenance_request_id')
    def check_validations(self):
        for line in self:

            if line.display_type in ('line_section', 'line_note'):
                continue

            if line.quantity <= 0:
                raise ValidationError(_("Quantity should be greater than Zero"))

            # Child Equipment Validation
            if line.y_child_equipment_id:

                allocation = self.env['equipment.allocation'].search([
                    ('y_equipment_id', '=', line.maintenance_request_id.y_parent_equipment_id.id)
                ], order='id desc', limit=1)

                allocation_lines = allocation.y_line_ids.filtered(
                    lambda l: l.y_equipment_id == line.y_child_equipment_id
                )

                if not allocation_lines:
                    raise ValidationError(_(
                        "Child Equipment '%s' is not allocated in Maintenance Request '%s'."
                    ) % (
                                              line.y_child_equipment_id.display_name,
                                              line.maintenance_request_id.display_name
                                          ))

                allocated_qty = sum(allocation_lines.mapped('y_qty'))

                total_qty = sum(
                    line.request_id.equipment_request_line_ids.filtered(
                        lambda l:
                        l.id != line.id
                        and l.display_type not in ('line_section', 'line_note')
                        and l.maintenance_request_id == line.maintenance_request_id
                        and l.y_child_equipment_id == line.y_child_equipment_id
                    ).mapped('quantity')
                ) + line.quantity

                if total_qty > allocated_qty:
                    raise ValidationError(_(
                        "Total quantity (%s) for Child Equipment '%s' "
                        "cannot exceed allocated quantity (%s)."
                    ) % (
                                              total_qty,
                                              line.y_child_equipment_id.display_name,
                                              allocated_qty
                                          ))

                if line.y_child_equipment_id.quantity < line.quantity:
                    raise ValidationError(_(
                        "Available quantity for Child Equipment '%s' is %s."
                    ) % (
                                              line.y_child_equipment_id.display_name,
                                              line.y_child_equipment_id.quantity
                                          ))

            # Parent Equipment Validation
            else:

                if not line.equipment_id:
                    continue

                if line.equipment_id.quantity < line.quantity:
                    raise ValidationError(_(
                        "Available quantity for Equipment '%s' is %s."
                    ) % (
                                              line.equipment_id.display_name,
                                              line.equipment_id.quantity
                                          ))

class MaintenanceRequests(models.Model):
    _inherit = "maintenance.request"

    equipment_request_delivery_line_ids = fields.One2many('equipment.request.delivery.line', 'maintenance_request_id')

    def delivery_equipment(self):
        return {
            'name': 'Delivery',
            'res_model': 'equipment.request.delivery',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.equipment_request_delivery_line_ids.request_id.ids)],
            'context': {
                'default_origin': self.name
            }
        }
