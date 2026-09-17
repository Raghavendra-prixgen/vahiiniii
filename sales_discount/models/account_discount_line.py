from odoo import api, fields, models, _

class AccountDiscountLine(models.Model):
    _name = "account.discount.line"
    _description = "account.discount.line"

   
    y_invoice_categ_dis_id = fields.Many2one('account.move', string='Order Reference', ondelete='cascade', index=True, copy=False)

    y_name = fields.Text(string='Description')
    y_category = fields.Many2one('item.group',string="Category")
    y_amount = fields.Monetary(currency_field='y_currency_id',string="Amount",store=True)
    y_amount_rounding = fields.Monetary(currency_field='y_currency_id',string="Rounding Amount")
    y_trade_discount_id = fields.Many2one('sale.discount',string="Trade Discount",domain="[('y_discount_type','=','trade')]")
    y_trade_discounts = fields.Float(string='Trade TDiscount (%)', default=0.0)
    y_trade_amount = fields.Float('Trade Discount Amount', digits=(12,2), default=0.0,store=True,compute="_compute_discounts")
    y_quantity_discount_id = fields.Many2one('sale.discount',string="Quantity Discount",domain="[('y_discount_type','=','quantity')]")
    y_quantity_discount = fields.Float(string='Quantity Discount (%)', digits=(12,3), default=0.0)
    y_quantity_amount = fields.Float(' Quantity Discount Amount', digits=(12,2), default=0.0,store=True,compute="_compute_discounts")
    y_special_discount_id = fields.Many2one('sale.discount',string="Special Discount",domain="[('y_discount_type','=','special')]")
    y_special_discount = fields.Float(string='Special Discount (%)', digits=(12,3), default=0.0)
    y_special_amount = fields.Float('Special Discount Amount ' , digits=(12,2), default=0.0,store=True,compute="_compute_discounts")
    y_currency_id = fields.Many2one('res.currency', related='y_invoice_categ_dis_id.currency_id', store=True, readonly=True)

    y_base = fields.Monetary(string='Base', store=True,currency_field='y_currency_id')
    y_total_discount_amount = fields.Float("Total Discount Amount" ,compute ="_compute_discounts",store=True,digits=(12,2))
    y_sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tds.")
    y_manual = fields.Boolean(string="Manual")

    @api.depends('y_amount','y_trade_discounts','y_quantity_discount','y_special_discount')
    def _compute_discounts(self):
        for line in self:
            line.y_trade_amount = (line.y_amount * line.y_trade_discounts)/100
            line.y_quantity_amount = ((line.y_amount - line.y_trade_amount) * line.y_quantity_discount)/100
            line.y_special_amount = (((line.y_amount - line.y_trade_amount)-line.y_quantity_amount) * line.y_special_discount)/100
            line.y_total_discount_amount = line.y_trade_amount + line.y_special_amount + line.y_quantity_amount
