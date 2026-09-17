#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, AccessError,ValidationError
import logging
import re
import pdb
import pytz
from datetime import datetime, timedelta,date
from datetime import datetime
import pdb
_logger = logging.getLogger(__name__)

class SettingupGateManagement(models.Model):
    _name = "settingup.gate.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description ="Setting up Gate Management"
    _rec_name = "y_warehouse_id"

    y_warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse",tracking=True)
    y_product_category_ids = fields.Many2many('product.category',string="Product Category",tracking=True)
    active = fields.Boolean(default=True,string="Activate Gate Management",tracking=True)
    y_inward_sequence = fields.Many2one("ir.sequence", string="Inward Sequence",tracking=True)
    y_outward_sequence = fields.Many2one("ir.sequence", string="Outward Sequence",tracking=True)
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id,tracking=True)

    @api.constrains('active','y_company_id','y_warehouse_id')
    def check_document_y_name(self):
        for rec in self:
            docs = rec.env['settingup.gate.management'].search([('y_warehouse_id','=',rec.y_warehouse_id.id),
                                                                ('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("Oops, looks like we've got a duplicate record!"))
    
class GateStationFrom(models.Model):
    _name = 'gate.station'
    _description ="Gate Station From"
    _rec_name = "y_name"

    y_name = fields.Char(string="Name")

class GateManagement(models.Model):
    """
       One of Main class for this module, contains purchase_order_ids, sale_order_ids [ split into two  inward/outward because conditions for domain
       is different for inward and outward ].And order type is changed based on the y_entry_type. [ Ex: If y_entry_type is "in" then it should show ( purchase, sale return)
       if its "out" it should show(sale, purchase return)]. 
       Similarly we have fields for rece 
    """
    _name = 'gate.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Gate Management'
    _order = ' id desc,y_name desc'
    _rec_name = 'y_name'


    y_name = fields.Char(string='Name')
    y_entry_type = fields.Selection(string='Entry Type', selection=[('in', 'Inward'),('out','Outward')])
    y_order_type_inward = fields.Selection(string="In Posting type", selection=[ ('p','Purchase'), ('sr','Sales Return'),('sto','Stock Transfer'),('dc','Delivery Challan'),('others','Others')]) # p = purchase, sr = sales return, tin = transefer In
    y_order_type_outward = fields.Selection(string="Out Order type",selection =[ ('s','Sale'), ('pr','Purchase Return'),('sto','Stock Transfer'),('dc','Delivery Challan'),('others','Others')]) # s = sales, pr = purchase return, t = transefer Out
    y_username = fields.Many2one("gate.user.registration",string="Username")
    y_description = fields.Char(string="Description")
    y_doc_datetime = fields.Datetime("Document Date", required=True)
    y_post_datetime = fields.Datetime("Posting Date")
    y_lr_rr_no = fields.Char(string="LR/RR No.")
    y_lr_rr_date = fields.Datetime(string="LR/RR Date")
    y_vehicle_no_id = fields.Many2one('fleet.vehicle',string="Internal Vehicle No.")
    y_external_vehicle_no = fields.Char(string="External Vehicle No.")
    y_odometer = fields.Float(string="Odometer")
    y_driver_name = fields.Many2one('res.partner',string="Driver Name",readonly=True)
    y_warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    y_gate_line = fields.One2many('gate.management.line', 'y_gate_id',string="Gate Line")
    y_gate_station_from_id = fields.Many2one('gate.station',string="Station From")
    y_gate_station_to_id = fields.Many2one('gate.station',string="Station To")
    y_station_from_id = fields.Many2one('res.partner',string="Gate Station From")
    y_station_to_id = fields.Many2one('res.partner',string="Gate Station To")
    y_state = fields.Selection([
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('returnable', 'Returnable'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft',copy=False)
    y_external_ref = fields.Char(string="External Reference")
    y_is_returnable = fields.Selection([
        ('returnable', 'Returnable'),
        ('non_returnable', 'Non Returnable'),
    ], string='Gate Pass Type', default='non_returnable', required=True)
    y_returnable_date = fields.Datetime(string="Return Date")
    y_activity_id = fields.One2many('mail.activity','y_gate_management_id',"Next Activity")
    y_user_id = fields.Many2one('res.users',compute="compute_get_user")
    y_picking_ids = fields.Many2many('stock.picking',compute="get_picking_id_gate_managements")
    y_purchase_ids = fields.Many2many('purchase.order',compute="get_purchase_gate_managements",store=True)
    y_status = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),('pending_approve', 'PendingApproval'),('done', 'Done'),('cancel', 'Cancelled'),],string="Status")
    

    def get_picking_id_gate_managements(self):
        for rec in self:
            rec.y_picking_ids = False 
            query = """SELECT stock_picking_id FROM stock_gate_management_rel WHERE gate_management_id = {}""".format(rec.id)
            self.env.cr.execute(query)
            picking_ids = [row[0] for row in self.env.cr.fetchall()]
            if picking_ids:
                rec.y_picking_ids = [(6,0,picking_ids)]


    @api.depends('y_picking_ids')
    def get_purchase_gate_managements(self):
        for rec in self:
            rec.y_purchase_ids = False 
            if rec.y_picking_ids.purchase_id.ids:
                rec.y_purchase_ids = [(6,0,rec.y_picking_ids.purchase_id.ids)]

    @api.depends('y_warehouse_id','y_name')
    def compute_get_user(self):
        for rec in self:
            rec.y_user_id = rec.env.user.id

    @api.constrains('y_doc_datetime')
    def check_doctime(self):
        for rec in self:
            if rec.y_doc_datetime and rec.y_doc_datetime > fields.Datetime.now():
                raise UserError('Document Date should be less than current date')

    @api.model
    def check_gate_access(self):
        if self.env.user.has_group('gate_management.group_gate_management_access'):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'gate.user.login',
                'view_mode': 'form',
                'view_type': 'form',
                'views': [[False, 'form']],
                'target': 'current',
            }
        else:
            return {
                'name':'Gate Management Type',
                'type': 'ir.actions.act_window',
                'res_model': 'gate.management.type',
                'view_mode': 'kanban',
                'view_type': 'kanban',
                'views': [[False, 'kanban']],
                'target': 'current',
            }


    @api.constrains('y_vehicle_no_id','y_external_vehicle_no')
    def vehicle_number(self):
        if not self.y_vehicle_no_id and not self.y_external_vehicle_no:
            raise UserError(_('Please Select Vehicle Number.'))

    @api.constrains('y_warehouse_id')
    def warehouse_name(self):
        if self.y_username:
            if self.y_warehouse_id != self.y_username.y_warehouse_id:
                raise UserError(_('Your Not Authorised To Do Transaction In %s Warehouse.') % ', '.join(self.y_warehouse_id.mapped('name')))

    def unlink(self):
        for each_entry in self:
            if each_entry.y_state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super().unlink()

    @api.model
    def create(self, vals):
        if (self.env.context['default_y_entry_type'] == 'in'):
            warehouse_id =  vals.get('y_warehouse_id')
            settingup_gate_id = self.env['settingup.gate.management'].search([('y_warehouse_id','=',warehouse_id)])
            if not settingup_gate_id.y_inward_sequence:
                raise UserError('Inward sequence is not set')
            else: 
                vals['y_name'] = settingup_gate_id.y_inward_sequence.next_by_id()
                vals['y_post_datetime'] = fields.Datetime.now()
        else:
            warehouse_id = vals.get('y_warehouse_id')
            settingup_gate_id = self.env['settingup.gate.management'].search([('y_warehouse_id','=',warehouse_id)])
            if not settingup_gate_id.y_outward_sequence:
                raise UserError('Outward sequence is not set')
            else:
                vals['y_name'] = settingup_gate_id.y_outward_sequence.next_by_id()
                vals['y_post_datetime'] = fields.Datetime.now()
        res=super().create(vals)
        if res:
            if vals.get('y_vehicle_no_id'):
                self.env['fleet.vehicle.odometer'].create({
                    'vehicle_id': vals.get('y_vehicle_no_id'),
                    'value': vals.get('y_odometer'),
                    'driver_id': vals.get('y_driver_name')
                    })
        return res

    @api.onchange('y_vehicle_no_id')
    def onchnage_of_internalvehicle(self):
        for l in self:
            if l.y_vehicle_no_id:
                l.y_driver_name = l.y_vehicle_no_id.driver_id.id


    def process(self):
        for each in self:
            if not each.y_gate_line:
                raise ValidationError("Lines are empty")      
            type_id = self.env.ref("gate_management.activity_returnable") if each.y_is_returnable == 'returnable' else self.env.ref("gate_management.activity_non_returnable")
            mode_id = self.env['ir.model'].search([('model','=','gate.management')])
            new_id = self.env['mail.activity'].create({'activity_type_id':type_id.id,
                                                    'user_id':each.env.user.id,
                                                    'res_model':'gate.management',
                                                    'res_model_id':mode_id.id,
                                                    'res_id':each.id,
                                                    'y_gate_management_id':each.id,
                                                    'automated': True,
                                                    'date_deadline': each.y_post_datetime})
            if new_id:
                new_id.write({'y_gate_management_id': [(4,each.id)]})

            if each.y_entry_type == 'out':
                for line in each.y_gate_line:
                    picking = line.y_sale_order_outward_id or line.y_purchase_return_receipt_id or line.y_stock_outward_id or line.y_other_outward
                    if picking:
                        gate_ids = picking.y_stock_gate_management_ids + each
                        picking.write({'y_stock_gate_management_ids':[(6,0,gate_ids.ids)]})

            return self.write({'y_state': 'processed'})
            
    
    
    def cancel(self):
        for line in self.y_gate_line:
            po = line.y_purchase_order_inward_id
            if not po:
                continue
            related_pickings = po.picking_ids.filtered(lambda p: self in p.y_stock_gate_management_ids)
            for picking in related_pickings:
                if picking.state == 'done':
                    raise ValidationError(
                        f"Cannot cancel Purchase Order '{po.name}' because it is in the 'Done' state."
                    )
                picking.write({'y_stock_gate_management_ids': [(3, self.id)]})
            self.y_state = 'cancel'
        return True


    

    
class GateManagementLine(models.Model):
    _name = 'gate.management.line'
    _description = 'Gate Management Line'

    y_challan_no = fields.Char(string="Vendor Invoice/DC Number")
    y_challan_date = fields.Datetime(string="Vendor Invoice/DC Date")
    y_description = fields.Char(string='Item Description')
    y_gate_id = fields.Many2one('gate.management', string='Gate Id')
    y_sequence = fields.Integer(default=10)
    
    y_purchase_order_inward_id = fields.Many2one("purchase.order", string="Purchase Order")
    y_sale_return_receipt_id = fields.Many2one("stock.picking",string="Sale Return Transfers")

    y_sale_order_outward_id = fields.Many2one("stock.picking", string="Sale Order")
    y_purchase_return_receipt_id = fields.Many2one("stock.picking", string="Purchase Return Transfers")

    y_stock_inward_id = fields.Many2one('stock.picking',string="In Stock Transfer")
    y_stock_outward_id = fields.Many2one('stock.picking',string="Out Stock Transfer")

    y_other_inward = fields.Many2one('stock.picking',string='In Delivery Challan',store=True)
    y_other_outward = fields.Many2one('stock.picking',string='Out Delivery Challan',store=True)

    y_remarks = fields.Char(string="Others",copy=False)
    y_is_delivery_challan_done = fields.Boolean(copy=False,string="Is Delivery Challan Done")
   
    def unlink(self):
        for each_entry in self:
            if each_entry.y_gate_id.y_state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super().unlink()
 
class PurchaseOrderDone(models.Model):
    _inherit= "purchase.order"

    y_warehouse_id = fields.Many2one("stock.warehouse", related="picking_type_id.warehouse_id")

class StockPicking(models.Model):
    _inherit="stock.picking"

    y_stock_gate_management_ids = fields.Many2many('gate.management','stock_gate_management_rel',copy=False,string="Gate Management",tracking=True)
    y_gate_management_ids = fields.Many2many('gate.management',compute="_compute_is_gate_management_domain",string="Gate Entry Doamin")

    @api.onchange('y_stock_gate_management_ids')
    def _onchange_stock_gate_management_ids(self):
        for picking in self:
            if picking.y_stock_gate_management_ids:
                if picking.y_stock_gate_management_ids.y_gate_line.filtered(lambda x:x.y_challan_no).mapped('y_challan_no'):
                    picking.y_external_document_number = ",".join(picking.y_stock_gate_management_ids.y_gate_line.mapped('y_challan_no'))
                if picking.y_stock_gate_management_ids.y_gate_line.filtered(lambda x:x.y_challan_date).mapped('y_challan_date'):
                    now = picking.y_stock_gate_management_ids.y_gate_line[:1].y_challan_date
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(now))
                    picking.y_external_document_date = seq_date

                if picking.y_stock_gate_management_ids.filtered(lambda x:x.y_lr_rr_date).mapped('y_lr_rr_date'):
                    now = picking.y_stock_gate_management_ids[:1].y_lr_rr_date
                    seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(now))
                    picking.y_lr_date = seq_date
                if picking.y_stock_gate_management_ids.filtered(lambda x:x.y_lr_rr_no).mapped('y_lr_rr_no'):
                    picking.y_lr_number = ",".join(picking.y_stock_gate_management_ids.mapped('y_lr_rr_no'))


    @api.depends('picking_type_code','y_stock_gate_management_ids')
    def _compute_is_gate_management_domain(self):
        for picking in self:
            picking.y_gate_management_ids = False
            purchase_order_id = picking.move_ids.purchase_line_id.mapped('order_id')
            sale_order_id = picking.move_ids.sale_line_id.mapped('order_id')
            warehouse_id = picking.picking_type_id.warehouse_id
            # GATE IN Ward
            if picking.picking_type_code == 'incoming':
                if purchase_order_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_inward','=','p'),('y_gate_line.y_purchase_order_inward_id','=',purchase_order_id.id),('y_state','=','processed')]).filtered(lambda x:x not in purchase_order_id.picking_ids.filtered(lambda x:x.state == 'done').mapped('y_stock_gate_management_ids'))
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]
                if sale_order_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_inward','=','sr'),('y_gate_line.y_sale_return_receipt_id','=',picking.id),('y_state','=','processed')]).filtered(lambda x:x not in sale_order_id.picking_ids.filtered(lambda x:x.state == 'done').mapped('y_stock_gate_management_ids'))
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

                if not purchase_order_id and not sale_order_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_inward','=','dc'),('y_gate_line.y_other_inward','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

            # GATE OUT Ward
            if picking.picking_type_code == 'outgoing':
                if sale_order_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_outward','=','s'),('y_gate_line.y_sale_order_outward_id','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

                if purchase_order_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_outward','=','pr'),('y_gate_line.y_purchase_return_receipt_id','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

                
                if not purchase_order_id and not sale_order_id:
                    if picking.location_dest_id.is_subcontracting_location == False:
                        gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_outward','=','dc'),('y_gate_line.y_other_outward','=',picking.id),('y_state','=','processed')])
                        if picking.backorder_id.y_stock_gate_management_ids:
                            gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                        if gate_ids:
                            picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

                

            if picking.picking_type_code == 'internal':
                if picking.location_id.usage == 'inventory' and picking.location_id.scrap_location == False and not picking.picking_type_id.warehouse_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_inward','=','sto'),('y_gate_line.y_stock_inward_id','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]

                if picking.location_dest_id.usage == 'customer' and picking.location_dest_id.scrap_location == False and not picking.picking_type_id.warehouse_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_gate_line.y_stock_outward_id','=','sto'),('y_gate_line.y_stock_outward_id','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]
                
                if picking.location_id.usage == 'supplier' and picking.location_id.usage != 'inventory' and picking.location_id.scrap_location == False and not picking.picking_type_id.warehouse_id:
                    gate_ids = picking.env['gate.management'].search([('y_warehouse_id','=',warehouse_id.id),('y_order_type_inward','=','sto'),('y_gate_line.y_stock_inward_id','=',picking.id),('y_state','=','processed')])
                    if picking.backorder_id.y_stock_gate_management_ids:
                        gate_ids = gate_ids + picking.backorder_id.y_stock_gate_management_ids
                    if gate_ids:
                        picking.y_gate_management_ids = [(6,0,gate_ids.ids)]


    def button_validate(self):
        res = super(StockPicking,self).button_validate()
        if not self.y_stock_gate_management_ids:
            settingup_gate_id = self.env['settingup.gate.management'].search([('y_warehouse_id','=',self.picking_type_id.warehouse_id.id),('y_company_id','=',self.company_id.id)])
            is_gate_entry_not_done = False
            if settingup_gate_id:
                if self.move_ids_without_package.filtered(lambda x:x.product_id.product_tmpl_id.categ_id in settingup_gate_id.y_product_category_ids):
                    purchase_order_id = self.move_ids.purchase_line_id.mapped('order_id')
                    sale_order_id = self.move_ids.sale_line_id.mapped('order_id')
                    if (self.picking_type_id.code == 'incoming' and (purchase_order_id or sale_order_id)) or (self.location_id.usage == 'supplier' and self.location_id.usage != 'inventory'):
                        is_gate_entry_not_done = True
            if is_gate_entry_not_done:
                raise ValidationError('Gate Entry Not Done')

        return res

class MailActivity(models.Model):
    _inherit='mail.activity'

    y_gate_management_id = fields.Many2one('gate.management',"Gate Management")