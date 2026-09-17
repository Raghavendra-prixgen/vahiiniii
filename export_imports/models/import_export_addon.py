# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command,_
from odoo.tools import float_round, float_compare
import math
from odoo.exceptions import UserError, AccessError,ValidationError

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    y_pacakging_sequence = fields.Many2one('ir.sequence',string="Sequence")

class ContainerType(models.Model):
    _name = "container.type"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Container Type")


class StockPackaging(models.Model):
    _inherit = 'stock.quant.package'

    def get_packaging_id(self):
        if self._context.get('ref_package_id'):
            packaging_list = self.env['packaging.list'].browse(self._context.get('ref_package_id'))
            return packaging_list.id

       
    y_package_sale_order = fields.Many2many('sale.order',string="Sale Order")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_product_uom_id = fields.Many2one(related="y_product_id.uom_id")
    y_sale_origin_id = fields.Many2one('sale.order',string="Sale Order")
    y_default_code = fields.Char(related="y_product_id.default_code",string="Product Code")
    y_product_description = fields.Char(string="Description")
    y_net_weight = fields.Float(string="Net Weight")
    y_gross_weight = fields.Float(string="Gross Weight",compute="_compute_gross_weight_stock_quant_packge")
    y_package_customer = fields.Many2one('res.partner',string="Ship To Name")
    y_customer_ref = fields.Char(string="Ship To Code")
    y_customer_po = fields.Char(string="Customer Po")
    y_seq_name = fields.Char('Document Number', readonly=True,copy=False)
    y_packing_list_id = fields.Many2one('packaging.list',string="Packaging list",default=get_packaging_id)
    y_quantity = fields.Float(string="Quantity")
    y_packing_stock_id = fields.Many2one('stock.quant.package',string="Packaging list")
    y_display_type = fields.Selection([('line_section', "Section"),
                                       ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    y_stock_move_line_id = fields.Many2one('stock.move.line')

    @api.onchange('y_packing_stock_id')
    def get_shippment_track(self):
        for rec in self:
            if rec.y_packing_stock_id:
                rec.shipping_weight = rec.y_packing_stock_id.shipping_weight

    @api.depends('y_net_weight','y_packing_stock_id')
    def _compute_gross_weight_stock_quant_packge(self):
        for line in self:
            line.y_gross_weight = sum(line.y_packing_list_id.y_packaging_list_ids.filtered(lambda x:x.y_packing_stock_id == line.y_packing_stock_id).mapped('y_net_weight')) + line.y_packing_stock_id.shipping_weight


class PackagingDetailss(models.Model):
    _name = "packaging.list"
    _description = "Packaging List"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "y_document_number"

    y_document_number = fields.Char(string="Document Number",tracking=True)
    y_container_number = fields.Char(string="Container No",tracking=True)
    y_container_seal_number = fields.Char(string="Container Seal No",tracking=True)
    y_gst_reg_no = fields.Char(string="GST Reg No",tracking=True)
    y_container_type = fields.Many2one('container.type',string="Container Type")
    y_warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse")
    y_state = fields.Selection([('open','Open'),('posted','Posted')], string='States', copy=False,store=True,tracking=True,default='open')
    y_partner_id = fields.Many2one('res.partner',string="Ship To",tracking=True)
    y_ship_to_code = fields.Char(related="y_partner_id.ref",string="Ship To Code")
    y_net_weight = fields.Float(string="Net Weight",compute="get_net_weight",store=True)
    y_gross_weight = fields.Float(string="Gross Weight",compute="get_gross_weight",store=True)
    y_sale_order_ids = fields.Many2many('sale.order',string="Sale order",copy=False)
    y_marks_and_no = fields.Char(string="Marks & No")
    y_number_of_package = fields.Integer(string="No of Package",compute="get_count_of_lines")
    y_created_user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)
    y_invoice_ref_id = fields.Many2one('account.move',string="Invoice Ref")
    y_is_invoiced = fields.Boolean(string="Is Invoiced",default=False)
    y_posted_before = fields.Boolean(default=False,string="Posted Before")
    y_packaging_list_ids = fields.One2many('stock.quant.package','y_packing_list_id',string="Package List Lines")
    y_packaging_list_line_ids = fields.One2many('packaging.list.line','y_packaging_list_id',string="Packaging List Lines")
     
    def unlink(self):
        for rec in self:
            if rec.y_state != 'open' or rec.y_posted_before == True:
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super(PackagingDetailss, self).unlink()

    @api.onchange('y_invoice_ref_id')
    def check_is_invocied_ornot(self):
        for rec in self:
            if rec.y_invoice_ref_id:
                rec.y_is_invoiced = True

    @api.depends('y_packaging_list_line_ids')
    def get_count_of_lines(self):
        for rec in self:
            rec.y_number_of_package = len(rec.y_packaging_list_line_ids.mapped('y_stock_quanat_packaing_id')) or False

    @api.depends('y_packaging_list_line_ids.y_net_weight')
    def get_net_weight(self):
        for rec in self:
            rec.y_net_weight = sum(self.y_packaging_list_line_ids.mapped('y_net_weight')) or 0

    @api.depends('y_packaging_list_line_ids.y_gross_weight')
    def get_gross_weight(self):
        for rec in self:
            if rec.y_packaging_list_line_ids:
                packing_stock_ids = set([(line.y_stock_quanat_packaing_id.id, line.y_gross_weight) for line in rec.y_packaging_list_line_ids])
                tot_gross_weight = sum([stock[1] for stock in packing_stock_ids])
                rec.y_gross_weight = tot_gross_weight
            else:
                rec.y_gross_weight = 0.0      

    def view_package(self):
        action = {
            'name': _("Packages"),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant.package',
            'context': {'create': False},
            'view_mode': 'kanban,list,form',
            'domain': [('id','in',self.y_packaging_list_line_ids.y_stock_quanat_packaing_id.ids)],

        }
        return action  

    def get_details(self):
        tree_view_id = self.env.ref('export_imports.sale_order_inherit_tree_view').id
        if self.y_partner_id:
            return {
                'name': 'Order to Invoice',
                'view_mode': 'list',
                'views': [[tree_view_id, 'list']],
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('partner_shipping_id','=',self.y_partner_id.id),('invoice_status','in',('no','to invoice')),('state','=','sale')],
                "context":{'ref_pack_id':self.id,'create':False,'edit':False},
                }


    @api.onchange('y_warehouse_id')
    def fetch_gst_number(self):
        for rec in self:
            if rec.y_warehouse_id.partner_id.vat:
                rec.y_gst_reg_no = rec.y_warehouse_id.partner_id.vat
            
    @api.model
    def create(self,vals):
        res = super(PackagingDetailss,self).create(vals)
        if not res.y_warehouse_id.y_pacakging_sequence:
            raise ValidationError("'{}' Packaging sequence not configured".format(res.y_warehouse_id.name))
        res.write({'y_document_number':res.y_warehouse_id.y_pacakging_sequence.next_by_id()})
        return res

    def button_validate(self):
        for rec in self:
            rec.write({'y_state':'posted','y_posted_before':True})

    def button_reset_to_draft(self):
        for rec in self:
            rec.y_state = 'open'

class PackagingListLine(models.Model):
    _name = "packaging.list.line"
    _description = "Packaging List Line"


    y_name = fields.Char('Document Number', readonly=True,copy=False)
    y_packaging_list_id = fields.Many2one('packaging.list',string="Packing list")
    y_stock_quanat_packaing_id = fields.Many2one('stock.quant.package',string="Packaging list")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_product_uom_id = fields.Many2one(related="y_product_id.uom_id")
    y_default_code = fields.Char(related="y_product_id.default_code",string="Product Code")
    y_product_description = fields.Char(string="Description")
    y_sale_origin_id = fields.Many2one('sale.order',string="Sale Order")
    y_package_customer_id = fields.Many2one('res.partner',string="Ship To Name")
    y_customer_ref = fields.Char(string="Ship To Code")
    y_display_type = fields.Selection([('line_section', "Section"),('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    y_package_type_id = fields.Many2one('stock.package.type')
    y_net_weight = fields.Float(string="Net Weight")
    y_gross_weight = fields.Float(string="Gross Weight",compute="_compute_gross_weight_stock_quant_packge")
    y_shipping_weight = fields.Float()
    y_quantity = fields.Float(string="Quantity")
    y_customer_po = fields.Char(string="Customer Po")
    y_stock_move_line_id = fields.Many2one('stock.move.line')

    @api.onchange('y_stock_quanat_packaing_id')
    def get_shippment_track(self):
        for rec in self:
            if rec.y_stock_quanat_packaing_id:
                rec.y_shipping_weight = rec.y_stock_quanat_packaing_id.shipping_weight


    @api.depends('y_net_weight','y_stock_quanat_packaing_id')
    def _compute_gross_weight_stock_quant_packge(self):
        for line in self:
            line.y_gross_weight = sum(line.y_packaging_list_id.y_packaging_list_line_ids.filtered(lambda x:x.y_stock_quanat_packaing_id == line.y_stock_quanat_packaing_id).mapped('y_net_weight')) + line.y_stock_quanat_packaing_id.shipping_weight

class SaleOrderNew12(models.Model):
    _inherit = "sale.order"

    def post_packing_details(self):
        for rec in self:
            filtered_move_ids = rec.picking_ids.move_line_ids_without_package.filtered(lambda x:x.result_package_id and x.quantity > 0)
            for move_line in filtered_move_ids:
                pack_val = self.env['packaging.list'].browse(self._context.get('ref_pack_id'))
                pack_val.y_sale_order_ids = filtered_move_ids.move_id.sale_line_id.order_id.mapped('id')
                net_weight = (move_line.product_id.product_tmpl_id.weight * move_line.quantity)
                gross_weight = (move_line.result_package_id.shipping_weight + net_weight)
                pack_val.y_packaging_list_line_ids = [(0,0,{
                    'y_product_id': move_line.product_id.id,
                    'y_product_description': move_line.product_id.name,
                    'y_sale_origin_id': rec.id,
                    'y_stock_move_line_id': move_line.id,
                    'y_stock_quanat_packaing_id': move_line.result_package_id.id,
                    'y_package_type_id': move_line.result_package_id.package_type_id.id,
                    'y_shipping_weight': move_line.result_package_id.shipping_weight,
                    'y_quantity': move_line.quantity,
                    'y_package_customer_id': pack_val.y_partner_id.id,
                    'y_customer_ref': pack_val.y_partner_id.ref,
                    'y_customer_po': rec.client_order_ref,
                    'y_net_weight': net_weight,
                    'y_gross_weight': gross_weight,
                    })]

                