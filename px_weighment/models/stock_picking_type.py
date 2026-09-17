# -*- coding: utf-8 -*-
from collections import namedtuple
import json
import time
from itertools import groupby
from odoo import api, fields, models, _

class PickingType(models.Model):
    _inherit = "stock.picking.type"
    _description = "The operation type determines the picking view"
    _order = 'sequence, id'

    y_weighment_type = fields.Many2one('weighment.picking.type',string="Weighment Type")

