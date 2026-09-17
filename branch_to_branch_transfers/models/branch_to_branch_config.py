# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo import modules
import base64

class BranchToBranchTransferCOnfiguration(models.Model):
    _name = 'branch.to.branch.transfer.config'
    _description = 'B To B Transfer Configuration'
    _rec_name = 'y_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_default_img():
        with open(modules.get_module_resource('branch_to_branch_transfers', 'static/src/img', 'BTB.png'),
              'rb') as f:
            return base64.b64encode(f.read())
    

    active = fields.Boolean(default=True,tracking=True)
    y_name = fields.Char(compute="_compute_name",tracking=True,string="Name",store=True)
    y_from_warehouse_id = fields.Many2one('stock.warehouse',string="From Warehouse",tracking=True)
    y_to_warehouse_id = fields.Many2one('stock.warehouse',string="To Warehouse",tracking=True)
    y_from_location_id = fields.Many2one('stock.location',string="From Location",tracking=True)
    y_to_location_id = fields.Many2one('stock.location',string="To Location",tracking=True)
    y_shipment_sequence_id = fields.Many2one('ir.sequence',string="Shipment Sequence",tracking=True)
    y_receipt_sequence_id = fields.Many2one('ir.sequence',string="Receipt Sequence",tracking=True)
    y_deliv_op_type_id = fields.Many2one('stock.picking.type',string="Delivery Operation Type",tracking=True)
    y_recit_op_type_id = fields.Many2one('stock.picking.type',string="Receipt Operation Type",tracking=True)
    y_is_interstate = fields.Boolean('Interstate Transfer',tracking=True)
    y_branch_sale_account_id = fields.Many2one('account.account',string="Branch Sale Account",tracking=True)
    y_branch_purchase_account_id = fields.Many2one('account.account',string="Branch Purchase Account",tracking=True)
    y_intranit_account_id = fields.Many2one('account.account',string="Intransit Account",tracking=True)
    y_branch_sale_journal_id = fields.Many2one('account.journal', string="Branch Sale Journal",tracking=True)
    y_branch_purchase_journal_id = fields.Many2one('account.journal', string="Branch Purchase Journal",tracking=True)
    y_lanaded_cost_product_id = fields.Many2one('product.product',domain="[('type','=','service'),('landed_cost_ok','!=',False)]",string="Landed Cost Product",tracking=True)
    y_receivable_payable_offset_account_id = fields.Many2one('account.account',string="Receivable/Payable Offset A/c",tracking=True)
    y_image_icon = fields.Binary(string=" " ,copy=False,default=get_default_img())
    y_is_same_company = fields.Boolean(compute="_compute_same_company",string="Is Same Company",store=True)

    _sql_constraints = [
        ('uniq_branch_warehouse_combination', 'UNIQUE(y_from_warehouse_id,y_to_warehouse_id)', 'B To B Transfer for this source and destination has already been configured')
    ]

    @api.depends('y_from_warehouse_id.company_id','y_to_warehouse_id.company_id')
    def _compute_same_company(self):
        for rec in self:
            rec.y_is_same_company = False
            if rec.y_from_warehouse_id.company_id == rec.y_to_warehouse_id.company_id:
                rec.y_is_same_company = True

    @api.depends('y_from_warehouse_id','y_to_warehouse_id')
    def _compute_name(self):
        for rec in self:
            rec.y_name = "{} -> {}".format(rec.y_from_warehouse_id.name,rec.y_to_warehouse_id.name) if rec.y_from_warehouse_id and rec.y_to_warehouse_id else ""
