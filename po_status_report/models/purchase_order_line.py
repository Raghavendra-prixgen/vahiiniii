from odoo import fields,models,api, _
from datetime import date, timedelta
from datetime import datetime
from odoo.exceptions import ValidationError

invoice_status = [
    ('upselling', 'Upselling Opportunity'),
    ('invoiced', 'Fully Invoiced'),
    ('to invoice', 'To Invoice'),
    ('no', 'Nothing to Invoice'),
    ('no_bill','Nothing to Bill'),
    ('full','Fully Billed'),
    ('waiting','Waiting Bill')
]


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    y_effective_date = fields.Datetime(related="order_id.effective_date")
    y_status = fields.Char('Transaction Status',store=True,compute='_compute_status_type')
    y_product_categ = fields.Char(related='product_id.categ_id.name',store=True,string="Product Category")
    y_pending_qty = fields.Float(compute="get_y_pending_qty",store=True,string="Pending Qty")
    y_pending_value = fields.Float(compute="get_y_pending_value",store=True,string="Pending Value")
    y_bill_pending_qty = fields.Float(compute="get_bill_pending_qty",store=True,string="Pending Quantity(Bill)")
    y_bill_pending_value = fields.Float(compute="get_bill_pending_value",store=True,string="Pending Value(Bill)")
    y_doc_type_id = fields.Many2one('purchase.doc.type',related="order_id.y_doc_type_id")

    @api.depends('product_qty','qty_received')
    def get_y_pending_qty(self):
        for line in self:
            line.y_pending_qty = 0
            if line.product_id.type != 'service':
                line.y_pending_qty = line.product_qty - line.qty_received 
    
    @api.depends('y_pending_qty','price_unit')
    def get_y_pending_value(self):
        for line in self:
            line.y_pending_value = line.y_pending_qty * line.price_unit

    @api.depends('qty_invoiced','qty_received')
    def get_bill_pending_qty(self):
        for line in self:
            line.y_bill_pending_qty = line.product_qty - line.qty_invoiced
            if line.product_id.type != 'service':
                line.y_bill_pending_qty = line.qty_received - line.qty_invoiced


    @api.depends('y_bill_pending_qty','price_unit')
    def get_bill_pending_value(self):
        for line in self:
            line.y_bill_pending_value = line.y_bill_pending_qty * line.price_unit

    def get_age_date_planned(self):
        for line in self:
            line.age_days = (date.today()-line.date_planned.date()).days

    y_receipt_status = fields.Selection([
        ('pending', 'Not Received'),
        ('partial', 'Partially Received'),
        ('full', 'Fully Received'),
    ], string='Receipt Status', compute='_compute_y_receipt_status', store=True)

    y_invoice_status = fields.Selection(
        selection=invoice_status,
        string="Billing Status",
        compute='_compute_y_invoice_status',
        store=True)

    @api.depends('state','qty_received','product_qty')
    def _compute_y_receipt_status(self):
        for line in self:
            if line.qty_received == 0:
                line.y_receipt_status = 'pending'
            elif line.product_qty == line.qty_received:
                line.y_receipt_status = 'full'
            elif line.product_qty != line.qty_received and line.qty_received >0:
                line.y_receipt_status = 'partial'

    @api.depends('state','qty_received','qty_invoiced')
    def _compute_y_invoice_status(self):
        for line in self:
            if line.product_id.type == 'consu' and line.product_id.is_storable:
                if line.qty_received == 0 and line.qty_invoiced ==0:
                    line.y_invoice_status = 'no_bill'
                elif line.qty_invoiced == line.qty_received and line.qty_received >0 and line.qty_invoiced >0:
                    line.y_invoice_status = 'full'
                elif line.qty_invoiced < line.qty_received:
                    line.y_invoice_status = 'waiting'
            else:
                if line.qty_invoiced == 0:
                    line.y_invoice_status = 'no_bill'
                elif line.product_qty == line.qty_invoiced  and line.qty_invoiced >0:
                    line.y_invoice_status = 'full'
                elif line.qty_invoiced < line.product_qty:
                    line.y_invoice_status = 'waiting'

    @api.depends('qty_received','qty_invoiced','product_qty')
    def _compute_status_type(self):
        for line in self:
            if line.qty_received == line.product_qty == line.qty_invoiced:
                line.y_status = 'Fully Billed'
            if line.product_qty == line.qty_received and line.qty_invoiced == 0:
                line.y_status = 'Waiting Bills'

            if line.product_qty != line.qty_received and line.qty_received > 0 and line.qty_invoiced == 0:
                line.y_status = 'Partially Received'

            if line.product_qty != line.qty_received and line.qty_invoiced > 0 and line.qty_received != line.qty_invoiced:
                line.y_status = 'Partially Received or Billed'
            if line.product_qty != 0 and line.qty_received == 0:
                line.y_status = 'Not Received'
            if line.y_is_short_close == True:
                line.y_status = 'Short Close'

    def purchase_order_view(self):
        return {
                "name": "Purchase Orders",
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "view_mode": 'form',
                "res_id": self.order_id.id,
                }


    def short_close_form_wizard_pol(self):
        po_lines = self.filtered(lambda line: line.y_is_short_close == False and line.product_qty != line.qty_received)
        if po_lines:
            return {
                'name': ("Purchase Short Close Wizard"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.short.close.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('purchase_base_18.view_purchase_short_close_wizard_form').id, 'form')],
                'target': 'new',
                'context':dict(self._context,default_sc_po_lines_ids = po_lines.ids)
            }
        else:
            raise ValidationError("Nothing to short close.")