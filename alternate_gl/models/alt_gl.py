from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

doc_type_options = [('payment_vendor','Send'),
        ('payment_customer','Receive')]


class AlternativeGL(models.Model):
    _name = 'alternative.gl'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Alternative GL'
    _rec_name = 'y_name'
    
    active = fields.Boolean(default=True)
    y_name = fields.Char(string="Name")
    y_description = fields.Char(string="Description")
    y_document_type = fields.Selection(doc_type_options,string="Transaction Type",tracking=True)
    y_alt_id = fields.Integer(compute='_get_alt_id',tracking=True,string="Alternative")
    y_gl_lines_ids = fields.One2many('alternative.gl.line','y_gl_id',string="Alternative GL Lines")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    y_release = fields.Boolean(string="Release",tracking=True)

    @api.constrains('y_document_type','active','y_company_id','y_document_type','y_name')
    def _check_duplicate(self):
        domain = [('y_name','=',self.y_name),('y_release','=',self.y_release),('y_document_type','=',self.y_document_type),('y_company_id','=',self.y_company_id.id)]
        existing_ids = self.env['alternative.gl'].search(domain)
        if len(existing_ids) > 1:
            raise UserError (_("Oops, looks like we've got a duplicate record!"))

    @api.depends('y_document_type')
    def _get_alt_id(self):
        for rec in self:
            if rec.y_document_type:
                rec.y_alt_id = 1 if rec.y_document_type in ('out_invoice', 'out_refund') else 2
            else:
                rec.y_alt_id = False

class AlternativeGLLine(models.Model):
    _name = 'alternative.gl.line'
    _description = 'Alternative GL Line'

    y_gl_id = fields.Many2one('alternative.gl',string="Alternative GL")

    y_account_on_partner_id = fields.Many2one('account.account',string="Account On Partner/Master")
    y_account_to_use_instead_id = fields.Many2one('account.account',string="Account To Use Instead")

    @api.constrains('y_gl_id','y_account_on_partner_id','y_account_to_use_instead_id')
    def _check_duplicate(self):
        for line in self:
            duplicate_ids = line.y_gl_id.y_gl_lines_ids.filtered(lambda x:x.y_account_on_partner_id == line.y_account_on_partner_id and x.y_account_to_use_instead_id == line.y_account_to_use_instead_id)
            if len(duplicate_ids) > 1:
                raise UserError (_("Oops, looks like we've got a duplicate record!"))