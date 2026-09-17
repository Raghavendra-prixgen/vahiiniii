# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        domain = ['|',('name', 'ilike', value),('code','ilike',value)]
        return domain


class ResPartner(models.Model):
    _inherit = 'res.partner'

    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def _onchange_incoterm_id(self):
        if self.partner_id:
            self.incoterm_id = self.partner_id.incoterm_id.id
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
        else:
            self.incoterm_id = False

