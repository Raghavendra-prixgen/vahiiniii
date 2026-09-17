# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
import base64
from datetime import timedelta,date,datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta   
from odoo.exceptions import UserError, ValidationError
import os
from odoo import modules




class ShipmentResPartner(models.Model):
    _inherit = 'res.partner'
    
    y_shipment_tracking_id = fields.Many2one('master.shipment',string="Shipment Tracking Code",tracking=True)
    y_is_shipment_tracking = fields.Boolean(string="Shipment Tracking")


class AddActivities(models.Model):
    _name = "sub.activities"
    _description = "SUB Activities"
    _rec_name = "y_name"

    y_name = fields.Char(string="Activities")
    y_sl_no = fields.Char(string='Sl NO',compute="_compute_sl_no_new") 
    y_lead_time = fields.Integer("Lead Time",tracking=True)

    y_shipment_tracking_id = fields.Many2one('shipment.tracking',string="Shipment Tracking")
    y_purchase_shipment_id = fields.Many2one('purchase.shipment',string="Purchase Shipment")


    def _compute_sl_no_new(self):
        serial_num = 0
        for rec in self:
            serial_num += 1
            if rec.y_shipment_tracking_id:
                rec.y_sl_no = str(rec.y_shipment_tracking_id.y_drag_and_drop_seq) + '.'+str(serial_num)
            elif rec.y_purchase_shipment_id:
                rec.y_sl_no = str(rec.y_purchase_shipment_id.y_sl_no) + '.'+str(serial_num)




class ShipmentTracking(models.Model):
    _name = 'master.shipment'
    _rec_name = 'y_sequence'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'image.mixin']
    


    y_sequence = fields.Char('Sequence',default=lambda self: _('New'),tracking=True,copy=False)

    y_active = fields.Boolean(default=True, copy=False)
    y_name = fields.Char('Description', required=True)
    y_incoterm_id = fields.Many2one('account.incoterms',string="Incoterm")
    y_partner_category_id = fields.Many2one('partner.category',string="Partner Category")
    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")
    y_shipment_ids = fields.One2many('shipment.tracking','y_master_shipment_id',string="Shipment Tracking")
    y_partner_id = fields.Many2one('res.partner',string="Partner",tracking=True)
    y_company_id = fields.Many2one('res.company', 'Company', index=True,default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('y_sequence', _('New')) == _('New'):
            vals.update({'y_sequence': self.env['ir.sequence'].next_by_code('master.shipment') or 'New'})
        return super().create(vals)
        
class SrlImports(models.Model):
    _name = 'shipment.tracking'
    _description = 'shipment.imports'
    _rec_name = 'y_name'

    y_sl_no = fields.Char(string='Sl NO',compute="_compute_sl_no_new") 
    y_sequence = fields.Char('Sequence',default=lambda self: _('New'),tracking=True,copy=False)

    y_drag_and_drop_seq = fields.Integer(default=1)
    y_name = fields.Char('Description',tracking=True)
    y_activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type',tracking=True)    
    y_lead_time = fields.Integer("Lead Time",tracking=True)
    y_company_id = fields.Many2one('res.company', 'Company', index=True,default=lambda self: self.env.company)
    y_is_notifiable = fields.Boolean("is Notifiable",tracking=True)

    y_master_shipment_id = fields.Many2one('master.shipment',string="Shipment",tracking=True)

    y_sub_activities = fields.One2many('sub.activities','y_shipment_tracking_id',string="Sub Activities")


    
    def add_sub_activities(self):
        # if self.partner_id.y_shipment_tracking_id:
        return {
            'name': _("Add Activities"),
            'type': 'ir.actions.act_window',
            'res_model': 'shipment.tracking',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                y_sl_no=self.y_sl_no
            ),

            'views': [(self.env.ref('incoming_shipment_tracker.add_activities_view_form').id, 'form')]}
                

        

    
    def _compute_sl_no_new(self):
        serial_num = 0
        for rec in self:
            serial_num += 1

            rec.y_sl_no = str(serial_num)

    @api.model
    def create(self, vals):
        if vals.get('y_sequence', _('New')) == _('New'):
            vals.update({'y_sequence': self.env['ir.sequence'].next_by_code('shipment.tracking') or 'New'})
        return super().create(vals)

 
    
class PurchaseShipmentTrack(models.Model):
    _name = 'purchase.shipment'
    _description = 'Shipment Lines'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'image.mixin']
    _rec_name = "y_name"
    _order = 'y_flot_sl_no'


    def get_default_img():
        with open(modules.get_module_resource('incoming_shipment_tracker', 'static/src/img', 'Cargoship.gif'),
              'rb') as f:
            return base64.b64encode(f.read())
    
    y_sl_no = fields.Char(string='Serial No') 
    y_flot_sl_no = fields.Float(string="Float Sl NO")
    y_serial = fields.Integer(string='Serial No') 
    y_purchase_id = fields.Many2one('purchase.order', string="Purchase")
    y_sale_id = fields.Many2one('sale.order', string="Sale")
    y_name = fields.Char(string="Description", tracking=True)
    y_remarks = fields.Char("Remarks", tracking=True)
    y_etd_date = fields.Date('ETD', help='Expected Time of Departure.', copy=False, tracking=True)
    y_eta_date = fields.Date('ETA', help='Expected Time of Arrival.', copy=False, tracking=True)
    y_atd_date = fields.Date('ATD', help='Actual Time of Departure.', copy=False, tracking=True)
    y_ata_date = fields.Date('ATA', help='Actual Time of Arrival.', copy=False, tracking=True)
    y_master_id = fields.Many2one('master.shipment', "Shipment Master")
    y_shipment_line_id = fields.Many2one('shipment.tracking',string="Shipment line")

    y_type =  fields.Selection([('incoming','Incoming'),('outgoing','Outgoing')], string='Type', copy=False)

    
    # y_user_id = fields.Many2one('res.users', string="Responsible", tracking=True)
    y_activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type')
    y_partner_id = fields.Many2one('res.partner',related="y_purchase_id.partner_id")
    y_lead_time = fields.Integer("Lead Time",tracking=True)
    y_is_notifiable = fields.Boolean("is Notifiable",tracking=True)
    y_status_id = fields.Many2one('shipment.purchase.data',string="Status")
    y_image_icon = fields.Binary(string=" " ,copy=False,default=get_default_img())
    y_company_id = fields.Many2one('res.company', 'Company', index=True,
                                 default=lambda self: self.env.company)

    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group",related="y_purchase_id.y_procurement_group_id")
    y_sub_activities = fields.One2many('sub.activities','y_purchase_shipment_id',string="Sub Activities")

    def merge_activity(self):
        for activities in self.y_sub_activities:
            self.copy({
            'y_purchase_id':self.y_purchase_id.id,
            'y_sl_no':activities.y_sl_no,
            'y_flot_sl_no':activities.y_sl_no,
            'y_name':activities.y_name,
            'y_lead_time':activities.y_lead_time
            })







    # def button_create_boe(self):

    #     if self.filtered(lambda x:x.y_create_boe == True):
    #         for purchase_shipment_record in self:
    #             if purchase_shipment_record.y_purchase_id:
    #                 boe_vals = {
    #                 'y_bill_of_entry_date':purchase_shipment_record.y_eta_date,
    #                 'y_purchase_id':purchase_shipment_record.y_purchase_id.id
    #                 }
    #                 boe_obj = self.env['boe.template'].create(boe_vals)
    #                 boe_obj._onchange_sale_auto_complete()
    #                 break
    #             else:
    #                 raise ValidationError(_("You cannot generate a BOE for the sales order."))


    def add_sub_activities(self):
        # if self.partner_id.y_shipment_tracking_id:
        return {
            'name': _("Add Activities"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.shipment',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            
            'views': [(self.env.ref('incoming_shipment_tracker.purchase_shipmentadd_activities_view_form').id, 'form')]}
                

    



    @api.onchange('y_activity_type_id')
    def onchange_activity_type_id(self):
        for rec in self:
            if rec.y_purchase_id:

                mode_id = self.env['ir.model'].search([('model','=','purchase.order')])
                new_id = self.env['mail.activity'].create({'activity_type_id':rec.y_activity_type_id.id,
                                                        'user_id':self.env.user.id,
                                                        'res_model':'purchase.order',
                                                        'res_model_id':mode_id.id,
                                                        'res_id':rec.y_purchase_id.id,
                                                        })
            else:
                mode_id = self.env['ir.model'].search([('model','=','sale.order')])
                new_id = self.env['mail.activity'].create({'activity_type_id':rec.y_activity_type_id.id,
                                                        'user_id':self.env.user.id,
                                                        'res_model':'sale.order',
                                                        'res_model_id':mode_id.id,
                                                        'res_id':rec.y_sale_id.id,
                                                        })

    
    @api.constrains('y_etd_date','y_eta_date')
    def ValidationForDate(self):  
        for result in self:
            if result.y_etd_date and result.y_eta_date:
                if result.y_etd_date > result.y_eta_date:
                    raise ValidationError("ETD Date Should Not Greater Than ETA")
           
    def button_calculate_eta(self):
        if self.y_purchase_id:

            purchse_shipment = self.y_purchase_id.y_purchase_shipment_ids
           
            for rec in purchse_shipment:
                if rec.y_sl_no == 1 and not rec.y_etd_date: 
                    # raise ValidationError("Please Enter ETD") 
                    raise ValidationError(_("Please Enter ETD Date Of(%s)", rec.y_name))
                else:
                    if rec.y_etd_date:
                        data = rec.y_etd_date  + timedelta(rec.y_lead_time)
                        rec._origin.y_eta_date = data
                        value = purchse_shipment.filtered(lambda a:a.y_sl_no == str(int(rec.y_sl_no) + 1))
                        value.y_etd_date = data
            if purchse_shipment:
                purchse_shipment[-1].y_purchase_id.date_planned = purchse_shipment[-1].y_eta_date
        else:
            sale_shipment = self.y_sale_id.y_purchase_shipment_ids
            for rec in sale_shipment:
                if rec.y_sl_no == 1 and not rec.y_etd_date: 
                    # raise ValidationError("Please Enter ETD") 
                    raise ValidationError(_("Please Enter ETD Date Of(%s)", rec.y_name))
                else:
                    if rec.y_etd_date:
                        data = rec.y_etd_date  + timedelta(rec.y_lead_time)
                        rec._origin.y_eta_date = data
                        value = sale_shipment.filtered(lambda a:a.y_sl_no == str(int(rec.y_sl_no) + 1))
                        value.y_etd_date = data
            if sale_shipment:
                sale_shipment[-1].y_sale_id.expected_date = sale_shipment[-1].y_eta_date



        
class CHACharges(models.Model):
    _name = "cha.charges"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")

class PurchaseTransactionWizard(models.TransientModel):
    _name = 'purchase.transaction.wizard'
    _rec_name = 'y_incoterm_id'

    y_incoterm_id = fields.Many2one('account.incoterms',string="Incoterm")
    y_partner_category_id = fields.Many2one('partner.category',string="Partner Category")
    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")
    y_type =  fields.Selection([('incoming','Incoming'),('outgoing','Outgoing')], string='Type', copy=False)

    y_shipment_master_ids = fields.Many2many('master.shipment',domain="[('y_incoterm_id','=',y_incoterm_id),('y_partner_category_id','=',y_partner_category_id)]")

    def button_create_shipment_activites(self):

        

        if self.y_type == 'incoming':

            purchase_order_obj = self.env['purchase.order'].browse(self._context.get('active_id'))
            # self = purchase_order_obj
            for rec in self.y_shipment_master_ids:
                

                serial_num = 0
                if not purchase_order_obj.y_purchase_shipment_ids:
                    if purchase_order_obj.partner_id.y_is_shipment_tracking:
                        purchase_order_obj.y_is_shipment_check = True                    
                        for master in rec.y_shipment_ids:
                            serial_num += 1
                            vals = {
                                'y_sl_no' : serial_num,
                                'y_flot_sl_no':serial_num,
                                'y_purchase_id': purchase_order_obj.id,
                                'y_name':master.y_name,
                                'y_master_id':master.y_master_shipment_id.id,
                                'y_activity_type_id':master.y_activity_type_id.id,
                                'y_shipment_line_id' : master.id,
                                'y_is_notifiable':master.y_is_notifiable,
                                'y_lead_time' : master.y_lead_time,
                                'y_type':'incoming'


                            }
                            purchase_shipment_obj = self.env['purchase.shipment'].create(vals)
                            if master.y_sub_activities:
                                for sub_activities in master.y_sub_activities:
                                    sub_activities_vals = {
                                        'y_purchase_shipment_id': purchase_shipment_obj.id,
                                        'y_name':sub_activities.y_name,
                                        'y_lead_time' : sub_activities.y_lead_time
                                    }
                                    sub_activities_obj = self.env['sub.activities'].create(sub_activities_vals)


                    else:
                              
                        purchase_order_obj.y_is_shipment_check = False 
        else:
            sale_obj = self.env['sale.order'].browse(self._context.get('active_id'))
            # self = sale_obj
            for rec in self.y_shipment_master_ids:
                
                serial_num = 0
                if not sale_obj.y_purchase_shipment_ids:
                    if sale_obj.partner_id.y_is_shipment_tracking:
                        sale_obj.y_is_shipment_check = True                    
                        for master in rec.y_shipment_ids:
                            serial_num += 1
                            vals = {
                                'y_sl_no' : serial_num,
                                'y_flot_sl_no':serial_num,
                                'y_sale_id': sale_obj.id,
                                'y_name':master.y_name,
                                'y_master_id':master.y_master_shipment_id.id,
                                'y_activity_type_id':master.y_activity_type_id.id,
                                'y_shipment_line_id' : master.id,
                                'y_is_notifiable':master.y_is_notifiable,
                                'y_lead_time' : master.y_lead_time,
                                'y_type':'outgoing'


                            }
                            purchase_shipment_obj = self.env['purchase.shipment'].create(vals)
                            if master.y_sub_activities:
                                for sub_activities in master.y_sub_activities:
                                    sub_activities_vals = {
                                        'y_purchase_shipment_id': purchase_shipment_obj.id,
                                        'y_name':sub_activities.y_name,
                                        'y_lead_time' : sub_activities.y_lead_time
                                    }
                                    sub_activities_obj = self.env['sub.activities'].create(sub_activities_vals)


                    else:
                              
                        sale_obj.y_is_shipment_check = False 



class SaleOrder(models.Model):
    _inherit ="sale.order"

    y_purchase_shipment_ids = fields.One2many('purchase.shipment', 'y_sale_id',string="Sale Shipment",copy=False)
    y_is_shipment_check = fields.Boolean("Shipment Check",copy=False,related="partner_id.y_is_shipment_tracking")


    def action_sale_shipment_tracking(self):    
        for rec in self:

            list_id = self.env.ref('incoming_shipment_tracker.purchase_shipment_view_list')
            return {
                'name': _("Shipment Tracking"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.shipment',
                'domain': [('y_sale_id', '=', rec.id)],
                'view_mode': 'list',
                'target': 'current',
                'views': [(self.env.ref('incoming_shipment_tracker.purchase_shipment_view_list').id, 'list')]
                
                
            }

    def action_incoming_schedule(self):
        for rec in self:
            if rec.state in ('sale'):
                
        
                return {
                    'name': ("Shipment Activity"),
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.transaction.wizard',
                    'view_mode': 'form',
                    'views': [(self.env.ref('incoming_shipment_tracker.view_purchase_transaction_wizard_form').id, 'form')],
                    'target': 'new',                
                    'context': dict(self._context,
                                    default_y_incoterm_id=self.incoterm.id,
                                    default_y_partner_category_id=self.partner_id.y_partner_category.id,
                                    default_y_type = 'outgoing')

                    }
            else:
                raise ValidationError(_("You Can Only Generate Shipment Activities Once Purchase Order Confirmed"))


        

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    y_purchase_shipment_ids = fields.One2many('purchase.shipment', 'y_purchase_id',string="Purchase Shipment",copy=False)
    y_is_shipment_check = fields.Boolean("Shipment Check",copy=False,related="partner_id.y_is_shipment_tracking")

    def action_incoming_schedule(self):
        for rec in self:
            if rec.state in ('purchase','done'):
                list_procurement_group = self.order_line.mapped('product_id').mapped('y_procurement_group_id')
                procurement_group = rec.env['product.procurement.group']
                if list_procurement_group:
                    critical_group = [items for items in list_procurement_group if items.y_is_critical]
                    if critical_group:
                        procurement_group = critical_group[0]
                    else:
                        procurement_group = list_procurement_group[0]

        
                return {
                    'name': ("Shipment Activity"),
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.transaction.wizard',
                    'view_mode': 'form',
                    'views': [(self.env.ref('incoming_shipment_tracker.view_purchase_transaction_wizard_form').id, 'form')],
                    'target': 'new',                
                    'context': dict(self._context,
                                    default_y_incoterm_id=self.incoterm_id.id,
                                    default_y_partner_category_id=self.partner_id.y_partner_category.id,
                                    default_y_procurement_group_id=procurement_group.id,
                                    default_y_type = 'incoming')
                    }
            else:
                raise ValidationError(_("You Can Only Generate Shipment Activities Once Purchase Order Confirmed"))


    def action_purchase_shipment_tracking(self):    
        for rec in self:

            list_id = self.env.ref('incoming_shipment_tracker.purchase_shipment_view_list')
            return {
                'name': _("Shipment Tracking"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.shipment',
                'domain': [('y_purchase_id', '=', rec.id)],
                'view_mode': 'list',
                'target': 'current',
                'views': [(self.env.ref('incoming_shipment_tracker.purchase_shipment_view_list').id, 'list')]
                
                
            }
           
                
                
   
           
class ShipmentPurchaseAddline(models.Model):
    _name = 'shipment.purchase.data'
    _rec_name = 'y_status'
    
    y_status = fields.Char("Status")
    y_company_id = fields.Many2one('res.company', 'Company', index=True,
                                 default=lambda self: self.env.company)
           