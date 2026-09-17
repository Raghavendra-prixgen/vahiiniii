
from odoo import models, fields, api



class InvoiceMarginReportLine(models.Model):
    _name = 'invoice.margin.report.line'
    _description = 'Invoice Margin Report'
    _auto = True  # Avoid automatic creation of database tables

    y_invoice_id = fields.Many2one('account.move', string="Invoice Id", readonly=True)
    y_partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    y_product_id = fields.Many2one('product.product', string="Product", readonly=True)
    y_account_id = fields.Many2one('account.account', string="Account", readonly=True)

    y_product_group_1 = fields.Many2one('product.group.1',string='Product Group 1')
    y_product_group_2 = fields.Many2one('product.group.2',string='Product Group 2')
    y_product_group_3 = fields.Many2one('product.group.3',string='Product Group 3')
    # y_family_desc_id = fields.Many2one('family.desc',string='Family Desc')
    # y_group_desc_id = fields.Many2one('group.desc',string='Group Desc')
    # y_subgroup_desc_id = fields.Many2one('subgroup.desc',string='Subgroup Desc')
    # y_gsr_type_id = fields.Many2one('gsr.type',string='Type')
    # y_producer_name_id = fields.Many2one('producer.name',string='Producer Name')
    # y_manufacturer_name_id = fields.Many2one('manufacturer.name',string='Manufacturer Name')
    y_currency_id = fields.Many2one('res.currency',string='Currency')
    y_location_id = fields.Many2one('stock.location',string='Location')
    y_lot_ids = fields.Many2many('stock.lot',string='Lot/Serial Number')
    y_invoice_currency_rate = fields.Float(string='Currency Rate')
    y_lr_number = fields.Char(string='LR Number')
    y_lr_date = fields.Date(string='LR Date')
    y_lot_create_date = fields.Date(string='Lot Create Date')

    y_product_code = fields.Char(string="Product Code", store=True)
    y_product_name = fields.Char(related="y_product_id.product_tmpl_id.name",string="Product Name")
    y_invoice_name = fields.Char(related="y_invoice_id.name",string="Invoice #")

    y_product_categ_id = fields.Many2one('product.category', string="Product Category", readonly=True)
    y_partner_categ_id = fields.Many2one('partner.category', string="Partner Category", readonly=True)
    y_invoice_date = fields.Date(string="Invoice Date")
    y_payment_term_id = fields.Many2one('account.payment.term', string="Payment Term", readonly=True)
    y_delivery_terms = fields.Selection([('self pickup','Self Pickup'),('dd','DD'),('dd_paid','DD Paid'),('to pay','To Pay'),('cif','CIF')], string="Delivery Term", readonly=True)
    y_invoiced_amount = fields.Float(string="Invoiced Amount", readonly=True,store=True)
    y_invoiced_qty = fields.Float(string="Invoiced Qty", readonly=True,store=True)
    y_cogs = fields.Float(string='COGS',readonly=True,store=True)
    y_unit_price = fields.Float(string='Price/Unit',readonly=True,store=True)
    y_transportation_cost = fields.Float(string='Transport Cost',readonly=True,store=True)
    y_return_amount = fields.Float(string="Return Amount", readonly=True, store=True)
    y_return_qty = fields.Float(string="Return Qty", readonly=True, store=True)
    
    y_margin = fields.Float(string='GM-1',readonly=True,store=True)
    y_margin_percentage = fields.Float(string='GM-1(%)',readonly=True,store=True)

    y_margin_2 = fields.Float(string='GM-2',readonly=True,store=True)
    y_margin2_percentage = fields.Float(string='GM-2(%)',readonly=True,store=True)

    y_sales_person_id = fields.Many2one('res.users',string="Salesperson",readonly=True)
    y_company_id = fields.Many2one('res.company',string="Company",readonly=True)
    y_weight = fields.Float(string="Weight",readonly=True)


    # y_product_type_id = fields.Many2one('product.type',string="Product Type",related="y_product_id.product_tmpl_id.y_product_type_id",store=True)
    # y_product_group_id = fields.Many2one('product.group',string="Product Group",related="y_product_id.product_tmpl_id.y_product_group_id",store=True)
    # y_processing_method_id = fields.Many2one('processing.method',string="Processing Method",related="y_product_id.product_tmpl_id.y_processing_method_id",store=True)
    # y_product_features = fields.Char(string="Product Features",related="y_product_id.product_tmpl_id.y_product_features",store=True)
    # y_colour_code = fields.Char(string="Colour Code",related="y_product_id.product_tmpl_id.y_colour_code",store=True)
    #




