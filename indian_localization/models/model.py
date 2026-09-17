from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner' 

    y_is_transporter = fields.Boolean(string = "Is Transporter")  

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    y_ceiling_limit_for_transporter = fields.Float(string="Celing limit for Transporter")
    y_ceiling_limit = fields.Boolean(string="Ceiling Limit")
    y_ceiling_limit_value = fields.Float(string="Ceiling Limit Value")
    y_is_allow_credit = fields.Boolean(string="Allow Negative",tracking=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def check_back_cash_allow_credit(self,account,current_move_balance):
        domain = [('account_id', '=', account.id), ('parent_state', '=', 'posted')]
        if not self.company_id.sudo().child_ids:
            domain += [('company_id', '=', self.company_id.id)]
        else:
            company_ids = self.company_id.sudo().child_ids.ids + self.company_id.ids
            domain += [('company_id','in',company_ids)]
        balances = {
            account.id: balance
            for account, balance in self.env['account.move.line'].sudo()._read_group(
                domain=domain,
                groupby=['account_id'],
                aggregates=['balance:sum'],
            )
        }
        total_balance = balances.get(account.id, 0)

        if total_balance + current_move_balance < 0:
            raise ValidationError("Negative balance is not allowed for this ledger.")

    def _post(self, soft=True):
        for rec in self:
            if rec.journal_id.type in ('cash','bank') and rec.journal_id.y_is_allow_credit == False and rec.line_ids.filtered(lambda x:x.account_id == rec.journal_id.default_account_id):
                current_move_balance = sum(rec.line_ids.filtered(lambda x:x.account_id == rec.journal_id.default_account_id).mapped('balance'))
                rec.check_back_cash_allow_credit(rec.journal_id.default_account_id,current_move_balance)
            if rec.journal_id.y_ceiling_limit and rec.journal_id:
                if rec.move_type == 'entry':
                    if sum(rec.line_ids.mapped('credit')) > rec.journal_id.y_ceiling_limit_value:
                        raise ValidationError(_('The amount should not exceed ceiling amount - %s %s')%(rec.currency_id.symbol,rec.journal_id.y_ceiling_limit_value))

                if rec.partner_id.y_is_transporter:
                    if rec.amount_total >= rec.journal_id.y_ceiling_limit_for_transporter:
                        raise ValidationError(_("Total value is greater than the the transporter celing limit"))
                if rec.move_type != 'entry':
                    if rec.amount_total >= rec.journal_id.y_ceiling_limit_value:
                        raise ValidationError(_("Total value is greater than the the Customer celing limit"))
                                            
        return super(AccountMove, self)._post(soft)

    @api.depends('partner_id', 'partner_shipping_id', 'company_id')
    def _compute_l10n_in_state_id(self):
        super()._compute_l10n_in_state_id()
        for move in self:
            if move.country_code == 'IN' and move.journal_id.type == 'sale':
                partner_state = move.partner_id.state_id
                country_code = partner_state.country_id.code
                if country_code == 'IN':
                    move.l10n_in_state_id = partner_state
                    

