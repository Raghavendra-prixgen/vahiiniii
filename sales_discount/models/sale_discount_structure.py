from odoo import fields,models,api, _

class datastructurez(models.Model):
    _name = 'discount.structure'
    _description = "discount.structure"
    _inherit = ['mail.thread']
    _rec_name = 'y_price_id'

    y_item_group_id = fields.Many2one('item.group', string="Item Group",tracking=True)
    y_state = fields.Selection([('draft','Draft'),('confirm','Confirm'),],string="State",tracking=True)
    y_price_id = fields.Many2one('price.group', string = "Price Group",tracking=True)
    y_doc_type_id = fields.Many2one('sale.doc.type',string="Document Type",tracking=True)
    y_trade_discounts = fields.Float(string="Trade Discount%",tracking=True)
    y_qty_disc = fields.Float(string="Qty Discount%",tracking=True)
    y_spec_discount = fields.Float(string="Special Discount%",tracking=True)
    y_start_date = fields.Date(string="Start Date",tracking=True)
    y_end_date = fields.Date(string="End Date",tracking=True)

    def action_draft(self):
        self.y_state = "draft"

    def action_confirm(self):
        self.y_state = "confirm"

class pricegroup(models.Model):
    _name = "price.group"
    _description = "price.group"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Price Group")
    
class supportfield(models.Model):
    _inherit = 'res.partner'
    
    y_price_group_id = fields.Many2one('price.group', string = "Price Group")