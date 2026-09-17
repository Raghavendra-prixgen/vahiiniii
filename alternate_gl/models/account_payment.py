from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.payment'

    y_alternative_gl = fields.Many2one('alternative.gl',domain="['|',('y_company_id','=',company_id),('y_company_id.child_ids','in',company_id),('y_document_type', '=', 'payment_vendor' if payment_type == 'outbound' else 'payment_customer'),('y_release','=',True)]",string="Alternative GL")
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        domain="[]",
        check_company=True)

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'destination_journal_id','y_alternative_gl')
    def _compute_destination_account_id(self):
        res = super()._compute_destination_account_id()
        for rec in self:
            if rec.y_alternative_gl:
                account = rec.y_alternative_gl.y_gl_lines_ids.filtered(lambda x:x.y_account_on_partner_id == rec.destination_account_id).y_account_to_use_instead_id
                if account:
                    rec.destination_account_id = account.id
                else:
                    empty_account = rec.y_alternative_gl.y_gl_lines_ids.filtered(lambda x: not x.y_account_on_partner_id).y_account_to_use_instead_id
                    if empty_account:
                        rec.destination_account_id = empty_account.id
                    else:
                        raise ValidationError("Alternative GL Not Configured.")
        return res





   