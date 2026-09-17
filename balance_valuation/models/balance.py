from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError,ValidationError


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"  

    y_account_valuation_balance = fields.Float(compute='_compute_account_valuation_balance',store=True,string="Balance")
    y_diffrence = fields.Float(compute="_compute_account_valuation_diffrence",store=True,string="Diffrence")
    y_ledger_id = fields.Many2one('account.account',compute="_compute_account_valuation_balance",store=True,string="Ledger")
    
    @api.depends('account_move_id')
    def _compute_account_valuation_balance(self, forced_quantity=None):
        for valuation in self:
            valuation.y_account_valuation_balance = 0
            account_move_line_id = valuation.account_move_id.line_ids.filtered(lambda x:x.account_id == valuation.product_id.categ_id.property_stock_valuation_account_id)
            if len(account_move_line_id) == 1:
                valuation.y_ledger_id = account_move_line_id[0].account_id.id
                valuation.y_account_valuation_balance = sum(account_move_line_id.mapped('balance'))

    @api.depends('account_move_id')
    def _compute_account_valuation_diffrence(self):
        for valuation in self:
            valuation.y_diffrence = valuation.value - valuation.y_account_valuation_balance
            
            

