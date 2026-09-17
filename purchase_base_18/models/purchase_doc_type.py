# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchaseDocType(models.Model):
    _name = 'purchase.doc.type'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Purchase Order Document Type'
    _rec_name = 'y_name'

    active = fields.Boolean(default=True)
    y_name = fields.Char(tracking=True,string='Name')
    y_description = fields.Char(tracking=True,string='Description')
    y_sequence_id = fields.Many2one('ir.sequence',tracking=True,string='Sequence')
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1,tracking=True)

    @api.constrains('y_name','y_company_id')
    def check_document_y_name(self):
        for rec in self:
            docs = rec.env['purchase.doc.type'].search([('y_name','=',rec.y_name),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""name already exists!"""))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    y_doc_type_id = fields.Many2one('purchase.doc.type', string="Document Type",copy=False,tracking=True)
    y_quotation_number = fields.Char(copy=False,string="RFQ Ref")
    y_purchase_request_number = fields.Char(copy=False,string="Purchase Request Ref",store=True)
    parent_company_id = fields.Many2one(related="company_id.parent_id")
        
    @api.onchange('partner_id')
    def get_document_type(self):
        for rec in self:
            if rec.partner_id:
                purchase_doc_type_id = rec.partner_id.sudo().with_company(rec.company_id).y_purchase_doc_type_id
                if not purchase_doc_type_id and rec.company_id.sudo().parent_id:
                    purchase_doc_type_id = rec.partner_id.sudo().with_company(rec.company_id.sudo().parent_id).y_purchase_doc_type_id
                rec.y_doc_type_id = purchase_doc_type_id.id
            else:
                rec.y_doc_type_id = False

    def button_confirm(self):
        for rec in self:
            if not rec.y_doc_type_id:
                raise ValidationError(_("""Mapping Document type is required to confirm a Purchase Quotation"""))
        return super(PurchaseOrder, self).button_confirm()

    def action_purchase_order_sequence(self):
        for order in self:
            order.y_quotation_number = order.name
            order.name = order.y_doc_type_id.y_sequence_id.next_by_id()

    def button_approve(self,force=False):
        for rec in self:
            if not rec.y_doc_type_id:
                raise ValidationError(_("""Mapping Document type is required to confirm a Purchase Quotation"""))
            self.action_purchase_order_sequence()
        return super(PurchaseOrder, self).button_approve(force)
    
    # def button_draft(self):
    #     if self.state in ('purchase','done','cancel'):
    #         raise ValidationError(_("""Once a purchase order has been posted or cancel, it cannot be reverted back to draft status."""))
    #     super(PurchaseOrder, self).button_draft()

class ResPartnerNew(models.Model):
    _inherit = "res.partner"

    y_purchase_doc_type_id = fields.Many2one('purchase.doc.type', string="Document Type",company_dependent=True)
    parent_company_id = fields.Many2one(related="company_id.parent_id")