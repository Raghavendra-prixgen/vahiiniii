from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round as round

class SaleDiscount(models.Model):
    _name = "sale.discount"
    _inherit = ['mail.thread']
    _description = "Sale Discount"
    _rec_name = 'y_name'

    _sql_constraints = [
        ('uniq_company_discount_type', 'UNIQUE(y_discount_type,y_company_id)', "Oops, looks like we've got a duplicate record")
    ]

    active = fields.Boolean(default=True)
    y_name = fields.Char(string="Discount Name",tracking=True)
    y_discount_type = fields.Selection([('quantity', 'Quantity Discount'),('special', 'Special Discount'),('trade','Trade Discount')],string="Discount Type",tracking=True)
    y_account_id = fields.Many2one('account.account', string='Account Debit', required=True, domain=[('deprecated', '=', False)],tracking=True)
    y_refund_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string='Account Credit', ondelete='restrict',tracking=True)
    y_company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company,domain="[('parent_id','=',False)]",tracking=True)
    