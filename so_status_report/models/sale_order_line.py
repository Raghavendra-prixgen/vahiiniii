from odoo import fields,models,api, _
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    y_status = fields.Char('Document Status',store=True,compute='_compute_status_type')
    y_currency_id = fields.Many2one('res.currency',' Currency',related="order_id.currency_id")
    y_partner_id = fields.Many2one('res.partner',' Partner',related="order_id.partner_id",store=True)
    y_client_order_ref = fields.Char('Customer Reference')
    y_product_catag_id=fields.Many2one('product.category',related="product_id.categ_id",store=True)
    y_order_date = fields.Datetime(related="order_id.date_order", string="Order Confirm Date",store=True)
    y_so_expected_date = fields.Datetime(related="order_id.expected_date",string=" Expected date")
    y_so_effective_date = fields.Datetime(related="order_id.effective_date",string=" Effective date")
    y_doc_type_id = fields.Many2one('sale.doc.type',related="order_id.y_doc_type_id")

    y_remaining_qty = fields.Float("Pending Qty",compute="qty_remaining",store=True)
    y_pending_order_value = fields.Float(compute='compute_value',string='Pending Value',store=True)
    y_invoice_pending_qty = fields.Float(compute="get_invoice_pending_qty",store=True,string="Pending Quantity(Invoice)")
    y_invoice_pending_value = fields.Float(compute="get_invoice_pending_value",store=True,string="Pending Value(Invoice)")

    def sale_order_view(self):
        return {
                "name": "Sale Order",
                "type": "ir.actions.act_window",
                "res_model": "sale.order",
                "view_mode": 'form',
                "res_id": self.order_id.id,
                }
                
    @api.depends('qty_delivered','product_uom_qty')
    def qty_remaining(self):
        for each in self:
            each.y_remaining_qty = 0
            if each.product_id.type != 'service':
                each.y_remaining_qty = each.product_uom_qty - each.qty_delivered

    @api.depends('y_remaining_qty','price_unit')
    def compute_value(self):
        for l in self:
            l.y_pending_order_value = l.price_unit * l.y_remaining_qty

    @api.depends('qty_invoiced','qty_delivered')
    def get_invoice_pending_qty(self):
        for line in self:
            line.y_invoice_pending_qty = line.product_uom_qty - line.qty_invoiced
            if line.product_id.type != 'service':
                line.y_invoice_pending_qty = line.qty_delivered - line.qty_invoiced

    @api.depends('y_invoice_pending_qty','price_unit')
    def get_invoice_pending_value(self):
        for line in self:
            line.y_invoice_pending_value = line.y_invoice_pending_qty * line.price_unit


    @api.depends('qty_delivered','qty_invoiced','product_uom_qty')
    def _compute_status_type(self):
        for line in self:
            if line.qty_delivered == line.product_uom_qty == line.qty_invoiced:
                line.y_status = 'Fully Invoiced'
            if line.product_uom_qty == line.qty_delivered and line.qty_invoiced == 0:
                line.y_status = 'Waiting for Invoice'

            if line.product_uom_qty != line.qty_delivered and line.qty_delivered > 0 and line.qty_invoiced == 0:
                line.y_status = 'Partially Delivered'

            if line.product_uom_qty != line.qty_delivered and line.qty_invoiced > 0 and line.qty_delivered != line.qty_invoiced:
                line.y_status = 'Partially Delivered or Invoiced'
                
            if line.product_uom_qty != line.qty_delivered and line.qty_invoiced > 0 and line.qty_delivered == line.qty_invoiced:
                line.y_status = 'Partially Invoiced'
                
            if line.product_uom_qty != 0 and line.qty_delivered == 0:
                line.y_status = 'Not Delivered'
                
            if line.y_is_short_close == True:
                line.y_status = "Short Close"
                
    # @api.depends('qty_delivered','qty_invoiced','product_uom_qty')
    # def _compute_status_type(self):
    #     for line in self:
    #         if line.qty_delivered != line.product_uom_qty:
    #             line.y_status = 'Pending Order'
    #         if line.qty_delivered != line.qty_invoiced:
    #             line.y_status = 'Pending for Invoice'
    #         if line.state == 'cancel':
    #             line.y_status = 'Cancel'
    #         if line.qty_delivered == line.product_uom_qty == line.qty_invoiced:
    #             line.y_status = "Fully Invoiced"
    #         if line.y_is_short_close == True:
    #             line.y_status = "Short Close"
                

    def short_close_form_wizard_sol(self):
        eligible_lines = self.filtered(lambda line: line.y_is_short_close == False and line.product_uom_qty != line.qty_delivered)
        if eligible_lines:
            return {
                'name': "SaleOrder Short Close Wizard",
                'type': 'ir.actions.act_window',
                'res_model': 'saleorder.short.close.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('sale_base_18.view_saleorder_short_close_wizard_form').id, 'form')],
                'target': 'new',
                'context': dict(self._context,default_y_sc_so_lines_ids=eligible_lines.ids)
            }
        else:
            raise ValidationError("Nothing to short close.")
        

