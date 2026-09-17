import calendar
from collections import defaultdict, OrderedDict
from datetime import timedelta
from odoo import _, api, fields, models

class Logforrulesproducttemplate(models.Model):
    _name = "product.template"
    _inherit = ['product.template','mail.thread', 'mail.activity.mixin']

    invoice_policy = fields.Selection(tracking=True)
    list_price = fields.Float(tracking=True)
    standard_price = fields.Float(tracking=True)
    barcode = fields.Char(tracking=True)
    categ_id = fields.Many2one(tracking=True)

    @api.onchange('uom_id','uom_po_id')
    def _onchange_y_uom_id(self):
        if self.weight_uom_name == self.uom_id.y_weight_uom:
            if self.uom_id.y_weight_uom == 'kg':
                self.weight = 1.0
            elif self.uom_id.y_weight_uom == 'lb':
                self.weight = 1.0


class Logforrulespricelist(models.Model):
    _name = "product.pricelist"
    _inherit = ['product.pricelist','mail.thread', 'mail.activity.mixin']

    name = fields.Char(translate=True)
    currency_id = fields.Many2one(tracking=True)
    company_id = fields.Many2one(tracking=True)

    
class Logforrulesdeliverycarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = ['delivery.carrier','mail.thread', 'mail.activity.mixin']

    name = fields.Char(translate=True)
    delivery_type = fields.Selection(tracking=True)
    company_id = fields.Many2one(tracking=True)
    free_over = fields.Boolean(tracking=True)
    product_id = fields.Many2one(tracking=True)
    margin = fields.Float(tracking=True)
    fixed_price = fields.Float(tracking=True)

class Logforrulesuom(models.Model):
    _name = "uom.uom"
    _inherit = ['uom.uom','mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    category_id = fields.Many2one(tracking=True)
    uom_type = fields.Selection(tracking=True)
    rounding = fields.Float(tracking=True)
    active = fields.Boolean(tracking=True)


    y_weight_uom = fields.Selection([
        ('kg', 'Kilograms'),
        ('lb', 'Pounds'),
    ], string='Weight Unit of Measure', default=False,company_dependent=True)




class Logforrulesuomcategory(models.Model):
    _name = "uom.category"
    _inherit = ['uom.category','mail.thread', 'mail.activity.mixin']

    name = fields.Char(translate=True)


class Logforrulesuomcategory(models.Model):
    _name = "mail.activity.type"
    _inherit = ['mail.activity.type','mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True)
    category = fields.Selection(tracking=True)
    default_user_id = fields.Many2one(tracking=True)
    default_note = fields.Html(tracking=True)
    res_model = fields.Selection(tracking=True)
    summary = fields.Char(tracking=True)
    icon = fields.Char(tracking=True)
    decoration_type = fields.Selection(tracking=True)    
    chaining_type = fields.Selection(tracking=True)
    delay_count = fields.Integer(tracking=True)
    delay_unit = fields.Selection(tracking=True)
    delay_label = fields.Char(tracking=True)
    delay_from = fields.Selection(tracking=True)
