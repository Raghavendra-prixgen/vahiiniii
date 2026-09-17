from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EquipmentRequest(models.Model):
    _name = 'equipment.request'
    _description = 'Equipment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", tracking=True)
    partner_shipping_id = fields.Many2one('res.partner', string="Delivery Address", tracking=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now, tracking=True)
    origin = fields.Char(string="Source Document", tracking=True)
    equipment_request_line_ids = fields.One2many('equipment.request.line', 'request_id', tracking=True)
    requested_by = fields.Many2one('res.users')
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'To Approve'), ('approved', 'Approved'), ('closed', 'Closed')],
        default='draft', tracking=True)

    maintenance_related_id = fields.Many2one('maintenance.request')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('equipment.request')
        return super(EquipmentRequest, self).create(vals)


class EquipmentRequestsLine(models.Model):
    _name = "equipment.request.line"
    _description = "Equipment Request Line"

    request_id = fields.Many2one('equipment.request')
    equipment_id = fields.Many2one('maintenance.equipment', required=True, string="Equipment")
    quantity = fields.Float(string="Demand")
    done = fields.Float(string="Done", store=True)
