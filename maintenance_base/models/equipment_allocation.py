# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EquipmentAllocation(models.Model):
    _name = 'equipment.allocation'
    _description = 'Equipment Allocation'
    _rec_name = 'y_name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    y_name = fields.Char(string="Reference", tracking=True, default='New')
    y_active = fields.Boolean(string="Active", default=True, tracking=True)
    y_equipment_id = fields.Many2one('maintenance.equipment', string="Equipment", required=True, tracking=True,
                                     domain="[('y_type', '=', 'parent')]")
    # y_qty = fields.Float(string="Quantity", default=1.0, required=True)
    y_company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company,
                                   tracking=True)
    y_line_ids = fields.One2many('equipment.allocation.line', 'y_allocation_id', string="Equipment", copy=True,
                                 tracking=True)
    y_note = fields.Html(string="Notes", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('y_name', 'New') == 'New':
                vals['y_name'] = self.env['ir.sequence'].next_by_code('equipment.allocation') or 'New'
        return super().create(vals_list)
    
    # @api.constrains('y_qty')
    # def _check_qty(self):
    #     for rec in self:
    #         if rec.y_qty <= 0:
    #             raise ValidationError(_("Quantity should be greater than zero."))


class EquipmentAllocationLine(models.Model):
    _name = 'equipment.allocation.line'
    _description = 'Equipment Allocation Line'
    _order = 'y_sequence,id'
    _rec_name = 'y_equipment_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    y_sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    y_allocation_id = fields.Many2one('equipment.allocation', string="Allocation", required=True, ondelete='cascade',
                                      tracking=True)
    y_equipment_id = fields.Many2one('maintenance.equipment', string="Equipment", required=True, tracking=True,
                                     domain="[('y_type', '=', 'child')]")
    y_qty = fields.Float(string="Quantity", default=1.0, required=True, tracking=True)
    y_company_id = fields.Many2one(related='y_allocation_id.y_company_id', store=True, string="Company", tracking=True)

    _sql_constraints = [
        (
            'unique_equipment_per_allocation',
            'unique(y_allocation_id, y_equipment_id)',
            'The same equipment cannot be added more than once in an allocation.'
        )
    ]

    @api.constrains('y_equipment_id')
    def _check_unique_child_equipment(self):
        for rec in self:
            duplicate = self.search([('id', '!=', rec.id), ('y_equipment_id', '=', rec.y_equipment_id.id), ('y_company_id', '=', rec.y_company_id.id)], limit=1)

            if duplicate:
                raise ValidationError(_("Equipment '%(child)s' is already allocated in Allocation '%(allocation)s' under Parent Equipment '%(parent)s'."
                ) % {'child': rec.y_equipment_id.display_name, 'allocation': duplicate.y_allocation_id.y_name, 'parent': duplicate.y_allocation_id.y_equipment_id.display_name, })