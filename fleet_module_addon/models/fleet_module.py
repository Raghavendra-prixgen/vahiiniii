from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime, date
from datetime import datetime, timedelta, timezone
import random
import logging
import time
from odoo import api, fields, models, tools, _
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as GD
from odoo.osv import expression
_logger = logging.getLogger(__name__)

class TransportationOrder(models.Model):
    _inherit = 'transportation.order'

    y_transportation_order_invoice_details_ids = fields.One2many('transportation.invoice.details','y_transportation_order_id')

    def check_pod_document(self):
        for rec in self:
            non_pod_document_ids = rec.y_transportation_order_invoice_details_ids.filtered(lambda x:not x.y_pod_document)
            if non_pod_document_ids:
                raise UserError("POD Document Not Available in Indent Lines")

    @api.onchange('y_lr_number')
    def onchange_lr_date_lr_number(self):
        super().onchange_lr_date_lr_number()
        for rec in self:
            rec.y_transportation_order_invoice_details_ids.write({'y_lr_number':rec.y_lr_number})
            
    def create_purchase_order(self):
        incomplete = self.filtered(lambda x: x.y_state != 'posted')
        if incomplete:
            raise UserError("Purchase Orders Allow to create only in Completed State. ")
        super().create_purchase_order()
        
class TransportatioOrderInvoiceDetials(models.Model):
    _name = 'transportation.invoice.details'
    _description = "Transportation Order Invoice Details"

    y_transportation_order_id = fields.Many2one('transportation.order')
    y_transportation_order_intent_line_ids = fields.Many2many('transportation.order.intent.line','to_invoice_details_rel')
    y_account_move_id = fields.Many2one('account.move',string="Invoice")
    y_picking_ids = fields.Many2many('stock.picking',string="Pickings")
    y_lr_number = fields.Char(string="LR Number")
    y_pod_document = fields.Binary(string="POD" ,copy=False)
    y_attachment_filename = fields.Char(string="POD Document Name")
    y_attachment_date = fields.Date(string="POD Date")
    y_indent_weight = fields.Float(string="Weight",compute="_compute_indent_weight")

    def write(self, vals):
        res = super().write(vals)
        update_fields = {}
        for field in ['y_lr_number']:
            if field in vals:
                update_fields[field] = vals[field]

        if update_fields:
            for line in self:
                current_invoice = line.y_account_move_id
                indent_line_ids = line.y_transportation_order_id.y_transportation_order_intent_line_ids.filtered(
                    lambda l: l.y_account_move_id == current_invoice
                )
                indent_line_ids.write(update_fields)

        return res

    @api.depends('y_transportation_order_intent_line_ids')
    def _compute_indent_weight(self):
        for line in self:
            line.y_indent_weight = sum(line.y_transportation_order_intent_line_ids.mapped('y_indent_weight'))

class TransportatioOrderIndentLines(models.Model):
    _inherit = 'transportation.order.intent.line'
    _description = "Transportation Order Indent Line"

    y_purchase_order_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_account_move_id = fields.Many2one('account.move',string="Invoice")

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_fleet_get_pickings(self):
        transportation_order_id = self.env['transportation.order'].browse(self._context.get('record_id'))
        # Cache existing picking IDs
        existing_picking_ids = transportation_order_id.y_transportation_order_intent_line_ids.mapped('y_picking_id').ids
        # Prepare intent line values
        new_intent_lines = []
        for picking in self.mapped('picking_ids'):
            if picking.id not in existing_picking_ids:
                weight = sum(move.product_id.weight * move.product_uom_qty for move in picking.move_ids)

                new_intent_lines.append((0, 0, {
                    'y_transportation_order_id': transportation_order_id.id,
                    'y_purchase_order_id': picking.purchase_id.id,
                    'y_picking_id': picking.id,
                    'from_city': picking.location_id.warehouse_id.partner_id.city,
                    'to_city': picking.location_dest_id.warehouse_id.partner_id.city,
                    'y_other_weight': weight,
                }))

        # Append new lines to the transportation order
        if new_intent_lines:
            transportation_order_id.write({
                'y_transportation_order_intent_line_ids': new_intent_lines
            })


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_fleet_get_pickings(self):
        transportation_order_id = self.env['transportation.order'].browse(self._context.get('record_id'))
        existing_picking_ids = transportation_order_id.y_transportation_order_intent_line_ids.mapped('y_picking_id').ids
        intent_line_vals = []
        for invoice in self:
            for picking in invoice.mapped('invoice_line_ids.y_stock_picking_ref').filtered(lambda x: x.id not in existing_picking_ids):
                weight = sum(move.product_id.weight * move.product_uom_qty for move in picking.move_ids)
                intent_line_vals.append((0, 0, {
                    'y_transportation_order_id': transportation_order_id.id,
                    'y_purchase_order_id': picking.purchase_id.id,
                    'y_picking_id': picking.id,
                    'from_city': picking.location_id.warehouse_id.partner_id.city,
                    'to_city': picking.location_dest_id.warehouse_id.partner_id.city,
                    'y_other_weight': weight,
                    'y_account_move_id': invoice.id,
                }))

        if intent_line_vals:
            transportation_order_id.write({
                'y_transportation_order_intent_line_ids': intent_line_vals
            })

        invoice_ids = transportation_order_id.y_transportation_order_intent_line_ids.mapped('y_account_move_id')
        for invoice in invoice_ids:
            indent_line_ids = transportation_order_id.y_transportation_order_intent_line_ids.filtered(
                lambda line: line.y_account_move_id == invoice
            )
            invoice_detail = transportation_order_id.y_transportation_order_invoice_details_ids.filtered(
                lambda detail: detail.y_account_move_id == invoice
            )
            update_vals = {
                'y_transportation_order_intent_line_ids': [(6, 0, indent_line_ids.ids)],
                'y_picking_ids': [(6, 0, indent_line_ids.mapped('y_picking_id').ids)],
            }
            if invoice_detail:
                invoice_detail.write(update_vals)
            else:
                new_detail_vals = update_vals.copy()
                new_detail_vals['y_account_move_id'] = invoice.id

                transportation_order_id.write({
                    'y_transportation_order_invoice_details_ids': [(0, 0, new_detail_vals)]
                })


class TransportationOrder(models.Model):
    _inherit = "transportation.order"

    def action_send_approval(self):
        super().action_send_approval()
        for rec in self:
            for indent_line in self.y_transportation_order_intent_line_ids:
                indent_line.y_purchase_order_id.write({'y_lr_date':rec.y_lr_date,
                                                'y_lr_number':rec.y_lr_number,
                                                'y_transportation_order_id':rec.id,
                                                })
                
                invoice_ids = indent_line.y_picking_id.sale_id.invoice_ids or indent_line.y_picking_id.purchase_id.invoice_ids
                invoice_ids._compute_transportation_orders()
                invoice_ids._compute_gate_management_orders()

    def get_purchase_orders(self):
        if self.y_state != 'draft':
            raise ValidationError("You can add pickings only in draft state.")
        tree_view = self.env.ref('fleet_module_addon.purchase_order_view_tree_fleet_module')
        domain = [('state', 'in', ('done','purchase')),('y_transportation_order_id','=',False),('picking_ids','not in',self.y_transportation_order_intent_line_ids.y_picking_id.ids),('picking_ids.y_transportation_order_id','=',False)]
        return {
            'name': 'Purchase Orders',
            'view_mode': 'list',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'views': [(tree_view.id, 'list')],
            'context':{'record_id':self.id,'create': False}
        }

    def get_invoices(self):
        if self.y_state != 'draft':
            raise ValidationError("You can add pickings only in draft state.")
        tree_view = self.env.ref('fleet_module_addon.account_move_view_tree_fleet_module')
        domain = [('state', '=', 'posted'),('move_type','=','out_invoice'),('invoice_line_ids.y_stock_picking_ref','not in',self.y_transportation_order_intent_line_ids.y_picking_id.ids),('invoice_line_ids.y_stock_picking_ref','!=',False),('invoice_line_ids.y_stock_picking_ref.y_transportation_order_id','=',False)]
        return {
            'name': 'Invoices',
            'view_mode': 'list',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'views': [(tree_view.id, 'list')],
            'context':{'record_id':self.id,'create': False}
        }