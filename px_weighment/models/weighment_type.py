# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class WeighmentPickingType(models.Model):
    _name = "weighment.picking.type"
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Weighment Picking Type"
    _rec_name = "y_name"
   
    active = fields.Boolean(default=True)
    y_name = fields.Char(string="Weighment Type",required=True,tracking=True)
    y_description = fields.Char(string="Description")

    y_count_picking_ready = fields.Integer(compute='_compute_picking_count_weighment',string='To Weigh')
    y_count_picking_closed = fields.Integer(compute='_compute_count_picking_closed', string='Closed')
    y_order_type = fields.Selection([('sales','Sales'),('purchase','Purchase'),('manufacturing','Manufacturing')],string="Order Type",tracking=True)

    def _compute_picking_count_weighment(self):
        # TDE TODO count picking can be done using previous two
        domains = {'y_count_picking_ready': [('y_state', '=', 'open')]}
        for field in domains:
            data = self.env['weighment.picking'].read_group(domains[field] +
                [('y_weighment_type', 'in', self.ids)],
                ['y_weighment_type'], ['y_weighment_type'])
            count = {
                x['y_weighment_type'][0]: x['y_weighment_type_count']
                for x in data if x['y_weighment_type']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def _compute_count_picking_closed(self):
        # TDE TODO count picking can be done using previous two
        domains = {'y_count_picking_closed': [('y_state', '=', 'close')]}
        for field in domains:
            data = self.env['weighment.picking'].read_group(domains[field] +
                [('y_weighment_type', 'in', self.ids)],
                ['y_weighment_type'], ['y_weighment_type'])
            count = {
                x['y_weighment_type'][0]: x['y_weighment_type_count']
                for x in data if x['y_weighment_type']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action


    def get_weighment_picking_action_picking_type(self):
        return self._get_action('px_weighment.weighment_picking_action_picking_type')


    def get_action_weighment_picking_list_ready(self):
        return self._get_action('px_weighment.action_weighment_picking_list_ready')

    def get_action_weighment_picking_list_closed(self):
        return self._get_action('px_weighment.action_weighment_picking_list_closed')