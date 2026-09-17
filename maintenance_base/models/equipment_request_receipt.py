from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EquipmentRequestReceipt(models.Model):
    _name = 'equipment.request.receipt'
    _description = 'Maintenance Request Receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", tracking=True)
    received_from_id = fields.Many2one('res.partner', string="Receive From", tracking=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", default=fields.Datetime.now, tracking=True)
    origin = fields.Char(string="Source Document", tracking=True)
    deadline = fields.Datetime(string="Deadline", tracking=True)
    backorder_id = fields.Many2one('equipment.request.receipt')
    company_id = fields.Many2one('res.company', string="Company")
    is_backorder = fields.Boolean()
    equipment_request_receipt_line_ids = fields.One2many('equipment.request.receipt.line', 'request_id', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        copy=False, index=True, readonly=True, store=True, tracking=True)

    receipt_to_delivery_id = fields.Many2one('equipment.request.delivery')
    maintenance_related_receipt_id = fields.Many2one('equipment.request.receipt', string="Backorder")

    y_remarks = fields.Html(string="Remarks")

    def _action_generate_backorder_wizard(self, show_transfers=False):
        view = self.env.ref('maintenance_base.view_eq_backorder_confirmation1')
        self.is_backorder = True
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'eq.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_show_transfers=show_transfers,
                            default_equipment_receipt_ids=[(4, p.id) for p in self]),
        }

    # def _action_generate_immediate_wizard(self):
    #     view = self.env.ref('maintenance_base.equipment_view_immediate_transfer')
    #     self.is_backorder = True
    #
    #     return {
    #         'name': _('Immediate Transfer'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'equipment.immediate.dr',
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',
    #         'context': dict(self.env.context, default_equipment_rl_ids=[(4, p.id) for p in self]),
    #     }

    def delivery_equipment(self):
        return {
            'name': 'Delivery',
            'res_model': 'equipment.request.delivery',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'domain': [('id', '=', self.receipt_to_delivery_id.id)],
        }

    def validate_receipt_to_equipment(self):
        for line in self.equipment_request_receipt_line_ids:
            if line.quantity < line.done:
                raise ValidationError(_("You cannot Validate more Done qty than the Demand"))
        for rec in self:
            if sum(rec.equipment_request_receipt_line_ids.mapped('done')) == 0:
                raise ValidationError(_("Quantity must be greater than zero before validating."))
                # return rec._action_generate_immediate_wizard()
            else:
                for receipt_lines in rec.equipment_request_receipt_line_ids:
                    if receipt_lines.quantity != receipt_lines.done:
                        return rec._action_generate_backorder_wizard(show_transfers=self._should_show_transfers())
                    else:
                        if not rec.backorder_id and not rec.is_backorder == False:
                            receipt_lines.quantity = receipt_lines.done
                        elif not rec.backorder_id and rec.is_backorder == False:
                            receipt_lines.quantity = receipt_lines.done
                        else:
                            if rec.backorder_id and rec.is_backorder == False:
                                receipt_lines.quantity = receipt_lines.done
        for line in rec.equipment_request_receipt_line_ids:

            if line.y_child_equipment_id:
                line.y_child_equipment_id.quantity += line.done
            else:
                line.equipment_id.quantity += line.done

        if sum(rec.equipment_request_receipt_line_ids.mapped('done')) == sum(
                rec.equipment_request_receipt_line_ids.mapped('quantity')):
            rec.state = 'done'

    def _should_show_transfers(self):
        """Whether the different transfers should be displayed on the pre action done wizards."""
        return len(self) > 1


class EquipmentRequestsReceiptLine(models.Model):
    _name = "equipment.request.receipt.line"
    _description = "Equipment Request Line"

    request_id = fields.Many2one('equipment.request.receipt')
    maintenance_request_id = fields.Many2one('maintenance.request')
    equipment_id = fields.Many2one('maintenance.equipment', required=True, string="Equipment")
    equipment_receipt_line_id = fields.Many2one('equipment.request.receipt.line')
    company_id = fields.Many2one('res.company', related="request_id.company_id", store=True)
    quantity = fields.Float(string="Demand")
    done = fields.Float(string="Done")

    name = fields.Char(string="Name")

    sequence = fields.Integer(string="Sequence", default=10)

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    y_child_equipment_id = fields.Many2one('maintenance.equipment', string="Child Equipments")
    y_allowed_child_equipment_ids = fields.Many2many('maintenance.equipment',
                                                     compute='_compute_allowed_child_equipment_ids')

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
        for rec in self:
            rec.y_allowed_child_equipment_ids = False

            if not rec.maintenance_request_id or not rec.maintenance_request_id.equipment_id:
                continue

            allocation = self.env['equipment.allocation'].search([
                ('y_equipment_id', '=', rec.maintenance_request_id.equipment_id.id)
            ], order='id desc', limit=1)

            rec.y_allowed_child_equipment_ids = allocation.y_line_ids.mapped('y_equipment_id')


class MainteanceRequests(models.Model):
    _inherit = "maintenance.request"

    equipment_request_receipt_line_ids = fields.One2many('equipment.request.receipt.line', 'maintenance_request_id')

    y_color = fields.Integer(string="Color", related="stage_id.y_color")

    def receipt_equipment(self):
        return {
            'name': 'Receipt',
            'res_model': 'equipment.request.receipt',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.equipment_request_receipt_line_ids.request_id.ids)],
        }
