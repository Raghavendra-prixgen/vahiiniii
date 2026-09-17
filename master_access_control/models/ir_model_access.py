# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'
    
    @api.model
    def check(self, model, mode='read', raise_exception=True):
        result = super(IrModelAccess, self).check(model, mode, raise_exception=raise_exception)
        if self.env.user.has_groups('master_access_control.group_access_models'):
            # ('read', 'write', 'create', 'unlink')
            if model == 'access.model':
                return result
            if self.env.user:
                if not self.env.context.get('access_models'):
                    model_id = self.env['ir.model'].sudo().with_context(access_models=True).search([('model','=','access.model')])
                    if model_id.exists():
                        access_model_ids = self.env['access.model'].sudo().with_context(access_models=True).search([('user_id','=',self.env.user.id)])
                        multi_access_model_ids = self.env['access.model'].sudo().with_context(access_models=True).search([('y_user_ids','in',self.env.user.ids)])

                        models_value = multi_access_model_ids.mapped('y_ir_model_ids').mapped('model')
                        if multi_access_model_ids and model:
                            models = multi_access_model_ids.mapped('ir_model_id.model')
                            if model in models_value:
                                access_model_id = multi_access_model_ids.mapped('y_ir_model_ids').filtered(lambda x:x.model == model)
                                for access_model_id in multi_access_model_ids:
                                    if access_model_id:
                                        if access_model_id.y_remove_create:
                                            if mode == 'create':
                                                return False
                                        if access_model_id.y_remove_edit:
                                            if mode == 'write':
                                                return False
                                        if access_model_id.y_remove_delete:
                                            if mode == 'unlink':
                                                return False
        return result