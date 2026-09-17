from odoo import models, fields, api,_
from ast import literal_eval


class GateManagementType(models.Model):
    _name='gate.management.type'
    _description ='gate.management.type'

    y_name = fields.Char(string="Name", required=True)
    y_color = fields.Integer(string='Color Index', help="The color of the channel")
    y_entry_type = fields.Selection(string='Entry Type', selection=[('in', 'Inward'),('out','Outward')])
    y_count_draft = fields.Integer(compute='_compute_draft_count')
    y_count_processed = fields.Integer(compute='_compute_processed_count')
    y_count_returnable=fields.Integer(compute='_compute_returnable_count')
    y_user_id = fields.Many2one('gate.user.registration',string='User')

    def _action_y_entry_type(self,action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        context = dict(literal_eval(action.get('context')))
        action['context'] = context
        action['target'] = 'main'
        return action

    def get_action_inward_entry(self):
        return self._action_y_entry_type('gate_management.action_window_inwards')

    def get_action_outward_entry(self):
        return self._action_y_entry_type('gate_management.action_window_outwards')

    def get_action_reg_entry(self):
        return self._action_y_entry_type('gate_management.action_window_reg')

    def create_registration(self):
        ctx = self._context.copy()
        curr_id =self.env.context.get('default_y_username')
        ctx['default_y_user_id'] = curr_id  
        return {
            'name': _('Registration'),
            'type': 'ir.actions.act_window',
            'res_model': 'gate.user.registration',
            'view_mode': 'list',
            'view_id': self.env.ref('gate_management.gate_management_registration_view').id,
            'context': ctx,
        }
            

    # filter inward entries draft
    def _action_draft(self,action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        action_context = literal_eval(action.get('context'))
        context = {
            'search_default_draft': 1,
        }
        context = {**action_context, **context}
        action['context'] = context
        action['target'] = 'main'
        return action

    # filter  entries processed
    def _action_processed(self,action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        action_context = literal_eval(action.get('context'))
        context = {
            'search_default_processed': 1,
        }
        context = {**action_context, **context}
        action['context'] = context
        action['target'] = 'main'
        return action

    def get_outward_entry_returnable(self):
        action = self.env["ir.actions.actions"]._for_xml_id('gate_management.action_window_returnable')
        action_context = literal_eval(action.get('context'))
        context = {
            'search_default_returnable': 1,
        }
        context = {**action_context, **context}
        action['context'] = context
        action['target'] = 'main'
        return action

    def get_inward_entry_processed(self):
        return self._action_processed('gate_management.action_window_inwards')

    def get_outward_entry_processed(self):
        return self._action_processed('gate_management.action_window_outwards')

    def get_inward_entry_draft(self):
        return self._action_draft('gate_management.action_window_inwards')

    def get_outward_entry_draft(self):
        return self._action_draft('gate_management.action_window_outwards')


    def action_create_new(self):
        ctx = self._context.copy()
        ctx = self._context.copy()
        if self.y_entry_type == 'in':
            action = self.env["ir.actions.actions"]._for_xml_id('gate_management.action_window_inwards_create_new')
        elif self.y_entry_type == 'out':
            action = self.env["ir.actions.actions"]._for_xml_id('gate_management.action_window_outwards_create_new')

        ctx = eval(action['context'])
        user_id = self.y_user_id.id
        if not user_id:
            user_id = self._context.get('default_y_user_id')
        ctx.update({'default_y_username':user_id,'default_y_warehouse_id':self._context.get('default_y_warehouse_id')})
        action['context'] = ctx
        return action


    @api.depends('y_entry_type')
    def _compute_draft_count(self):
        # calculate count of entry type 
        for each in self:
            each.y_count_draft = self.env['gate.management'].search_count([('y_entry_type','=',each.y_entry_type),('y_state',"=",'draft')])


    @api.depends('y_entry_type')
    def _compute_processed_count(self):
        # calculate count of entry type 
        for each in self:
            each.y_count_processed = self.env['gate.management'].search_count([('y_entry_type','=',each.y_entry_type),('y_state',"=",'processed')])


    @api.depends('y_entry_type')
    def _compute_returnable_count(self):
        # calculate count of entry type 
        for each in self:
            each.y_count_returnable = self.env['gate.management'].search_count([('y_entry_type','=','out'),('y_is_returnable',"=",True)])