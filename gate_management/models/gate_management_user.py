#-*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ast import literal_eval
class UserLogin(models.TransientModel):
    """
        Created this as a Transient model as we don't need to save this information anywhere,
        username and password are common fields that are declared here to grant the access to the
        user [ provided he has been registered by the admin ( class declared below)].
        Login function is triggred when the `Login` button is clicked and it has parameters saying
        which model has to used to render the page. Username is also passed in the context so that
        we will be knowing who was there at that point.
    """
    _name = "gate.user.login"
    _description = "gate_user_login"
    _rec_name = 'y_username'

    y_username = fields.Char(string='Username')
    y_password  = fields.Char(string='Password')
   
    def login(self):
        u_name = self.env['gate.user.registration'].search([('y_username', '=', self.y_username)])
        if u_name['y_username'] == self.y_username and u_name['y_password'] == self.y_password:
            action = self.env["ir.actions.actions"]._for_xml_id('gate_management.action_gate_management_type_kanban')
            action_context = literal_eval(action.get('context'))
            context = {
               'default_y_username': u_name.id,
               'default_y_warehouse_id':u_name.y_warehouse_id.id,
               'default_y_user_id' : u_name.id,
            }
            context = {**action_context, **context}
            action['context'] = context
            action['view_id'] = self.env.ref('gate_management.gate_management_type_kanban_view').id
            return action
        else:
            raise ValidationError("Incorrect username or password!!")   

class UserRegistration(models.Model):
    """
        Class used to register the users at the gate, 
        `username` and `password` are used to register the user and also _sql_constraints 
        are added to avoid the duplicate values [ say avoid users with same username ].
        Also _rec_name is given to display the username of the registered person[ It is displayed in the breadcrumbs at top].
    """
    _name = "gate.user.registration"
    _description = "gate_user_registration"
    _rec_name = 'y_username'

    y_username = fields.Char(string='Username')   
    y_password  = fields.Char(string='Password')
    y_warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse',required=True)
    y_is_head_security = fields.Boolean(string='Is a Head Security')
    y_user_id = fields.Many2one('gate.user.registration',string='User')

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(y_username)',
         "Username already exists"),
    ]


    @api.constrains('y_password','y_username')
    def check_user_access(self):
        default_reg = self.env['gate.user.registration']
        if len(default_reg) > 0:
            default_login = self.env.context.get('default_y_user_id')
            if not self.env['gate.user.registration'].search([('id','=',default_login)]).y_is_head_security:
                raise ValidationError("You don't have access") 

    
    @api.constrains("y_is_head_security")
    def update_record(self):
        login_user_ids = self.env['gate.user.registration'].search([('id','=',self.y_user_id.id)])
        if not self.y_is_head_security:
            if not self.env['gate.user.registration'].search([('id','=',self.y_user_id.id)]).y_is_head_security:
                raise ValidationError("You don't have access")
