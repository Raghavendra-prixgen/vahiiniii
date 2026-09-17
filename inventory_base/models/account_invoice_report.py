from odoo import models, fields, api
from odoo.tools import SQL

class AccountInvoiceReport(models.Model): 
    _inherit = 'account.invoice.report'

    y_item_group = fields.Many2one('item.group',string='Item Group')
    y_product_group_1 = fields.Many2one('product.group.1',string='Product Group 1')
    y_product_group_2 = fields.Many2one('product.group.2',string='Product Group 2')
    y_product_group_3 = fields.Many2one('product.group.3',string='Product Group 3')

    def _select(self) -> SQL:
        return SQL("%s, template.y_item_group as y_item_group,template.y_product_group_1 as y_product_group_1,template.y_product_group_2 as y_product_group_2,template.y_product_group_3 as y_product_group_3", super()._select())
