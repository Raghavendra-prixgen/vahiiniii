from odoo import api, fields, models, _

from odoo.exceptions import  UserError, ValidationError, AccessError

class ResCompany(models.Model):
    _inherit='res.company'

    einv_engine = fields.Char(string="Einv Engine")
    Version = fields.Char(string="Schema Version")
    einv_engine_uname = fields.Char(string="Einv Engine Uname")
    einv_engine_pass = fields.Char(string="Einv Engine Pass")
    einv_server = fields.Selection([('sand','sandbox'),('prod','Production')],default='sand', string="Einv Server")
    einv_gst_src = fields.Selection([('jl','Journal'),('wh','Warehouse')],default='jl')



# class ResConfigSettingsIrn(models.TransientModel):
#     _inherit = 'res.config.settings'

#     einv_engine = fields.Char()
#     einv_engine_uname = fields.Char()
#     einv_engine_pass = fields.Char()
#     Version = fields.Char("Schema Version")
#     einv_server = fields.Selection([('sand','sandbox1'),('prod','Production')],default='sand')
#     # einv_gst_src = fields.Selection([('jl','Journal'),('wh','Warehouse')],default='jl')

#     def set_values(self):
#         super(ResConfigSettingsIrn,self).set_values()
#         param = self.env['ir.config_parameter'].sudo()
#         param.set_param('account_irn-odoo15.einv_engine',self.einv_engine)
#         param.set_param('account_irn-odoo15.einv_engine_uname',self.einv_engine_uname)
#         param.set_param('account_irn-odoo15.einv_engine_pass',self.einv_engine_pass)
#         param.set_param('account_irn-odoo15.Version',self.Version)
#         param.set_param('account_irn-odoo15.einv_server',self.einv_server)
#         # param.set_param('account_irn-odoo15.einv_gst_src',self.einv_gst_src)

#     @api.model
#     def get_values(self):
#         res = super(ResConfigSettingsIrn, self).get_values()
#         param = self.env['ir.config_parameter'].sudo()
#         res.update(einv_engine = param.get_param('account_irn-odoo15.einv_engine'))
#         res.update(einv_engine_uname = param.get_param('account_irn-odoo15.einv_engine_uname'))
#         res.update(einv_engine_pass = param.get_param('account_irn-odoo15.einv_engine_pass'))
#         res.update(Version = param.get_param('account_irn-odoo15.Version'))
#         res.update(einv_server = param.get_param('account_irn-odoo15.einv_server'))
#         # res.update(einv_gst_src = param.get_param('account_irn-odoo15.einv_gst_src'))
#         return res