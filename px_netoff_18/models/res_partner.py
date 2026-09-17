# -*- coding: utf-8 -*-

from odoo import models, fields, api

class NetOff13Partner(models.Model):
    _inherit = 'res.partner'

    net_off_type = fields.Selection([('rp','Receivable to Payable'),('pr','Payable to Receivable')])