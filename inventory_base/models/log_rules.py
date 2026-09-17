import calendar
from collections import defaultdict, OrderedDict
from datetime import timedelta
from odoo import _, api, fields, models

class Logrules(models.Model):
    _name = "stock.rule"
    _inherit = ['stock.rule','mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    action = fields.Selection(tracking=True)
    picking_type_id = fields.Many2one(tracking=True)
    location_src_id = fields.Many2one(tracking=True)
    location_dest_id = fields.Many2one(tracking=True)
    auto = fields.Selection(tracking=True)
    procure_method = fields.Selection(tracking=True)
    route_id = fields.Many2one(tracking=True)
    warehouse_id = fields.Many2one(tracking=True)
    sequence = fields.Integer(tracking=True)
    group_propagation_option = fields.Selection(tracking=True)
    propagate_cancel = fields.Boolean(tracking=True)
    propagate_warehouse_id = fields.Many2one(tracking=True)
    group_id = fields.Many2one(tracking=True)
    partner_address_id = fields.Many2one(tracking=True)
    delay = fields.Integer(tracking=True)
