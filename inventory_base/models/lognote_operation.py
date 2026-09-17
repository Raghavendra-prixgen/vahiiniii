# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import SUPERUSER_ID, _, api, fields, models

class PickingType(models.Model):
    _name = "stock.picking.type"
    _inherit = ['stock.picking.type','mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(tracking=True)
    sequence_code = fields.Char(tracking=True)
    sequence_id = fields.Many2one(tracking=True)
    default_location_src_id = fields.Many2one(tracking=True)
    default_location_dest_id = fields.Many2one(tracking=True)
    code = fields.Selection(tracking=True)
    use_create_lots = fields.Boolean(tracking=True)
    use_existing_lots = fields.Boolean(tracking=True)
    return_picking_type_id = fields.Many2one(tracking=True)
    show_operations = fields.Boolean(tracking=True)
    show_reserved = fields.Boolean(tracking=True)
    reservation_method = fields.Selection(tracking=True)
