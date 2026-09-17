# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccessModels(models.Model):
    _name = 'access.model'
    _description = 'Access Model'
    
    ir_model_id = fields.Many2one('ir.model', 'Model')
    y_ir_model_ids = fields.Many2many('ir.model',string="Models")

    user_id = fields.Many2one('res.users')
    y_user_ids = fields.Many2many('res.users',string="Users")

    y_remove_create = fields.Boolean('Remove Create')
    y_remove_edit = fields.Boolean('Remove Edit')
    y_remove_delete = fields.Boolean('Remove Delete')


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def cur_user_has_group_js(self, group_id):
        return self.env.user.has_group(group_id)
