# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrderRevisions(models.Model):
    _name = 'purchase.order.revision'
    _description = "Purchase Order Revisions Line"
    _rec_name = 'y_name'
    y_name = fields.Text(string='Name', store=True, )

    y_partner_id = fields.Many2one('res.partner', string='Vendor',store=True)
    y_partner_ref = fields.Char(string='Vendor Reference',store=True)
    y_date_order = fields.Datetime(string='Order Deadline', store=True)
    y_date_planned = fields.Datetime(string='Expected Arrival', store=True)

    y_origin = fields.Char(string='Source Document', store=True)
    y_user_id = fields.Many2one('res.users', string='Buyer')
    y_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    y_fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')

    y_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')

    y_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')

    y_amount_untaxed = fields.Monetary(currency_field='y_currency_id', string='Untaxed', store=True)
    y_amount_total = fields.Monetary(currency_field='y_currency_id',string='Total', store=True)

    y_purchase_order_revision_line_ids = fields.One2many('purchase.order.revision.line','y_purchase_order_revision_id')

    y_revision_id = fields.Many2one('purchase.order')

    def action_revision(self):
            for rec in self:
                purchase_order = self.env['purchase.order'].search([('id', '=', self.y_revision_id.id)])
                if purchase_order.state in ('draft','sent','to approve'):
                    purchase_order.action_revision()
                    purchase_order.write({
                            'partner_id': rec.y_partner_id.id,
                            'partner_ref': rec.y_partner_ref,
                            'date_order': rec.y_date_order,
                            'date_planned': rec.y_date_planned,
                            'user_id': rec.y_user_id.id,
                            'payment_term_id': rec.y_payment_term_id.id,
                            'fiscal_position_id': rec.y_fiscal_position_id.id,
                            'amount_untaxed': rec.y_amount_untaxed,
                            'amount_total': rec.y_amount_total,

                        })
                    for line in rec.y_purchase_order_revision_line_ids:
                            order_line = self.env['purchase.order.line'].search([
                                ('order_id', '=', purchase_order.id),
                                ('name', '=', line.y_name),
                            ])

                            order_line.write({
                                    'product_qty': line.y_product_qty,
                                    'date_planned': line.y_date_planned,
                                    'discount': line.y_discount,
                                    'taxes_id': [(6, 0, line.y_taxes_id.ids)],
                                    'product_uom': line.y_product_uom.id,
                                    'product_id': line.y_product_id.id,
                                    'price_unit': line.y_price_unit,
                                    'price_subtotal': line.y_price_subtotal,
                                    'price_total': line.y_price_total,
                                })
class PurchaseOrderRevisionsLine(models.Model):
    _name = 'purchase.order.revision.line'
    _description = "Purchase Order Revisions"


    y_name = fields.Text(string='Description', store=True, )
    y_product_qty = fields.Float(string='Quantity',store=True)
    y_date_planned = fields.Datetime(string='Expected Arrival', store=True)
    y_discount = fields.Float(string="Disc.%",store=True)
    y_taxes_id = fields.Many2many('account.tax', string='Taxes')
    y_product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    y_product_id = fields.Many2one('product.product', string='Product')
    y_price_unit = fields.Float(string='Unit Price',store=True)
    y_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    y_price_subtotal = fields.Monetary(currency_field='y_currency_id', string='Tax excl.', store=True)
    y_price_total = fields.Monetary(currency_field='y_currency_id',string='Tax incl.', store=True)
    y_purchase_order_revision_id = fields.Many2one('purchase.order.revision')


class PurchaseOrderBills(models.Model):
    _inherit = 'purchase.order'

    y_revision_ids = fields.One2many('purchase.order.revision','y_revision_id')
    y_revision_count = fields.Integer(default=0,string="Revision Count")


    def buttonconfirm(self):
        res = super(PurchaseOrderBills, self).button_confirm()
        for rec in self:
            rec.action_revision()
        return res

    def action_revision(self):
        for rec in self:
            rec.y_revision_count += 1 
            revision = {
                'y_name': f"{rec.name}-{rec.y_revision_count}",
                'y_partner_id': rec.partner_id.id,
                'y_revision_id':rec.id,
                'y_partner_ref': rec.partner_ref,
                'y_date_order': rec.date_order,
                'y_date_planned': rec.date_planned,
                'y_origin': rec.origin,
                'y_user_id': rec.user_id.id,
                'y_payment_term_id': rec.payment_term_id.id,
                'y_fiscal_position_id': rec.fiscal_position_id.id,
                'y_amount_untaxed': rec.amount_untaxed,
                'y_amount_total': rec.amount_total,
            }
            revision_order = self.env['purchase.order.revision'].create(revision)

            for order_line in rec.order_line:
                revision_line = {
                    'y_name': order_line.name,
                    'y_product_qty': order_line.product_qty,
                    'y_date_planned': order_line.date_planned,
                    'y_discount': order_line.discount,
                    'y_taxes_id': [(6, 0, order_line.taxes_id.ids)],
                    'y_product_uom': order_line.product_uom.id,
                    'y_product_id': order_line.product_id.id,
                    'y_price_unit': order_line.price_unit,
                    'y_price_subtotal': order_line.price_subtotal,
                    'y_price_total': order_line.price_total,
                    'y_purchase_order_revision_id': revision_order.id,  
                }
                self.env['purchase.order.revision.line'].create(revision_line)

    def open_purchase_revision(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Revision',
            'view_mode': 'list,form',
            'res_model': 'purchase.order.revision',  
            'res_id': self.id,  
            'target': 'current',
            'domain': [('y_revision_id', '=', self.id)],
        }
    
     