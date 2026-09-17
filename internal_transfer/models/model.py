from odoo import fields,api, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date

class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_internal_transfer = fields.Boolean(string="Internal Transfer",
        readonly=False, store=True,
        tracking=True,
        compute="_compute_is_internal_transfer")
 
    paired_internal_transfer_payment_id = fields.Many2one('account.payment',
        index='btree_not_null',
        help="When an internal transfer is posted, a paired payment is created. "
        "They are cross referenced through this field", copy=False)

    destination_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Destination Journal',
        domain="[('type', 'in', ('bank','cash')), ('id', '!=', journal_id)]",
        check_company=True,
    )


    @api.depends('partner_id', 'journal_id')
    def _compute_is_internal_transfer(self):
        for payment in self:
            payment.is_internal_transfer = payment.partner_id and payment.partner_id == payment.journal_id.company_id.partner_id

    @api.depends('partner_id', 'company_id','destination_journal_id' ,'payment_type','is_internal_transfer')
    def _compute_available_partner_bank_ids(self):
        super()._compute_available_partner_bank_ids()
        for pay in self:
            if pay.is_internal_transfer:
                pay.available_partner_bank_ids = pay.destination_journal_id.bank_account_id


    @api.depends('is_internal_transfer','journal_id')
    def _compute_partner_id(self):
        for pay in self:
            if pay.is_internal_transfer:
                pay.partner_id = pay.journal_id.company_id.partner_id
            else:
                pay.partner_id = pay.partner_id

    @api.depends('journal_id', 'partner_id', 'partner_type','destination_journal_id','is_internal_transfer')
    def _compute_destination_account_id(self):
        super()._compute_destination_account_id()
        for pay in self:
            if pay.is_internal_transfer:
                pay.destination_account_id = pay.destination_journal_id.company_id.transfer_account_id


    @api.model
    def _get_trigger_fields_to_synchronize(self):
        fields = super()._get_trigger_fields_to_synchronize()
        internal_ref = ('is_internal_transfer',)
        fields += internal_ref
        return fields

    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:
            payment_type = payment.payment_type == 'outbound' and 'inbound' or 'outbound'
            available_payment_method_line_ids = payment.destination_journal_id._get_available_payment_method_lines(payment_type)
            paired_payment = payment.copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment_type,
                'move_id': None,
                'memo': payment.memo,
                'payment_method_line_id':available_payment_method_line_ids[0].id,
                'paired_internal_transfer_payment_id': payment.id,
                'date': payment.date,
            })

            paired_payment.move_id.action_post()
            paired_payment.action_post()
            payment.paired_internal_transfer_payment_id = paired_payment
            body = _("This payment has been created from:") + payment._get_html_link()
            paired_payment.message_post(body=body)
            body = _("A second payment has been created:") + paired_payment._get_html_link()
            payment.message_post(body=body)

            lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            lines.reconcile()

    def action_post(self):
        super().action_post()
        self.filtered(lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id)._create_paired_internal_transfer_payment()

