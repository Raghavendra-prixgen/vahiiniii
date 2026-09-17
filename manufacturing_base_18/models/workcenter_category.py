from urllib import request
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

# descrite
# process

class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    y_output_quantity = fields.Float(string="Output Quantity", store=True)
    y_output_bool = fields.Boolean(string="Output Boolean")

class workOrderCategory(models.Model):
    _name = 'wizard.outquantity'

    y_output_quantity = fields.Float(string="Quantity Output", required=True)
    y_workorder_id = fields.Many2one('mrp.workorder',string="Workorder")
    y_po_demand = fields.Float(related='y_workorder_id.y_total_workorder_demand',string="Total Workorder Demand")
    y_po_total_output_qty = fields.Float(related='y_workorder_id.y_total_output_quantity',string="Total Workorder Quantity")
    y_po_remaining_qty = fields.Float(related='y_workorder_id.y_total_workorder_remaining',string="Remaining Qty")
    y_is_done_workorder = fields.Boolean(string="Is Workorder Done")

    @api.onchange('y_output_quantity')
    def _onchange_output_quantity(self):
        if self.y_is_done_workorder == True and self.y_output_quantity < self.y_po_remaining_qty:
            return {
                    'warning': {
                        'title': _('User Warning'), 
                        'message': _('Output Quantity is less than remaining quantity press ok to continue'),
                        },
                    }

        if self.y_is_done_workorder == True and self.y_output_quantity > self.y_po_remaining_qty:
            return {
                    'warning': {
                        'title': _('User Warning'), 
                        'message': _('Output Quantity is more than remaining quantity'),
                        },
                    }

    @api.onchange('y_workorder_id')
    def _onchange_workorder_id(self):
        for rec in self:
            rec.y_workorder_id = self.env['mrp.workorder'].browse(self._context.get('y_workorder_id'))
           
    def added(self):
        timeline_obj = self.env['mrp.workcenter.productivity']
        domain = [('workorder_id', '=', self._context.get('active_id'))]
        wod = self.env['mrp.workorder'].search([('id','=',self._context.get('active_id'))])
        if (self.y_output_quantity + wod.y_total_output_quantity) > wod.y_total_workorder_demand:
            raise UserError("Output quantity should not be greater than product quantity")

        total_output_quantity_list = wod.production_id.workorder_ids.filtered(lambda x: x.y_workcenter_routing_sequence < wod.y_workcenter_routing_sequence and x.state != 'cancel').mapped('y_total_output_quantity')
        if len(total_output_quantity_list):
            for line in total_output_quantity_list: 
                if (wod.y_total_output_quantity + self.y_output_quantity) > line:
                    raise UserError("Output quantity should not be greater than product quantity")
        

        productivity_workorder = self.env['mrp.workcenter.productivity'].search(domain)
        if productivity_workorder:
            productivity_workorder[0].y_output_quantity = self.y_output_quantity
            if sum(wod.time_ids.mapped('y_output_quantity')) > wod.y_total_workorder_demand:
                raise UserError("Output quantity should not be greater than product quantity")
            
        if wod.production_id.workorder_ids[-1] == wod:
            wod.production_id.qty_producing = sum(wod.time_ids.mapped('y_output_quantity'))

        if self.y_is_done_workorder == True:
            self.y_workorder_id.y_total_workorder_remaining = 0
            self.y_workorder_id.with_context(y_is_done_workorder=True).button_finish()
               
        # Disabling Auto Mark As Done
        if wod.y_total_workorder_demand == wod.y_total_output_quantity:
            # if self.env.user.has_group('manufacturing_base_18.group_mo_user_validation_workorder'):
            if wod.production_id.workorder_ids[-1] != wod:
                wod.do_finish()
            else:
                # action = wod.action_open_manufacturing_order()
                # return action
                button_mark_done = wod.production_id.button_mark_done()
                return button_mark_done
            # else:
            #     wod.do_finish()

        # if self.env.user.has_group('manufacturing_base_18.group_mo_user_validation_workorder')

        # for timeline in timeline_obj.search(domain):
        #   timeline.y_output_quantity = self.y_output_quantity
        #   timeline.y_output_bool = True 
        # wod.production_id.qty_producing = wod.y_total_output_quantity
            
        return True

class workOrderCategory(models.Model):
    _inherit = 'mrp.workorder'

    y_total_output_quantity = fields.Float(string = "Total output quantity",  compute ='compute_total_outquantity' )
    y_workcenter_routing_sequence = fields.Integer(string = "Workcenter Routing Sequence", related = "operation_id.sequence", store = True)
    y_total_workorder_demand = fields.Float(string="Demand",compute="get_total_wordorder_demand")
    y_total_workorder_remaining = fields.Float(string="Remaining",compute="compute_total_remaining_quantity")

    #this is for validation is like without start of previous workorder its next workorder should not started
    def button_start(self):
        # if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.sequential_operation'):
        #     workorder_obj = self.production_id.workorder_ids.filtered(lambda x:x.state != 'cancel').ids
        #     if workorder_obj.index(self.id) != 0:
        #         previous_workorder_index = workorder_obj.index(self.id) - 1
        #         previous_workorder = workorder_obj[previous_workorder_index]
        #         previous_workorder_obj = self.env['mrp.workorder'].browse(previous_workorder)
        #         if previous_workorder_obj.date_finished:
        #             if previous_workorder_obj.y_total_output_quantity == 0:
        #                 raise UserError("{} Operation Output Quantity not Recored".format(previous_workorder_obj.name))
        #         else:
        #             raise UserError('Previous operation {} is not yet started'.format(previous_workorder_obj.operation_id.name))

        #reserved_availability field not in odoo 17 ....................................................... 

        if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_restrict_reserved_qty_warning'):
            product_ids = self.production_id.move_raw_ids.filtered(lambda x:x.quantity < 1 and x.product_uom_qty > 0).product_id.mapped('name')
            product_names = "\n".join(product_ids)
            if self.production_id.bom_id.ready_to_produce == 'all_available' and any(self.production_id.move_raw_ids.filtered(lambda x:x.quantity <= 0 and x.product_uom_qty > 0)):
                raise ValidationError("Below products are not reserved to start the production\n{}".format(product_names))
            
            if self.production_id.bom_id.ready_to_produce == 'asap' and self.production_id.move_raw_ids[:1].quantity <= 0 and self.production_id.move_raw_ids[:1].product_uom_qty > 0:
                raise ValidationError("{} is not reserved to start the production".format(self.production_id.move_raw_ids[:1].product_id.name))

        #reserved_availability field not in odoo 17 ....................................................... 

        res = super().button_start()
        if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_is_output_quantity_validation'):
            for rec in self:
                if self.production_id.workorder_ids[-1] == rec and rec.y_total_output_quantity > 0:
                    self.production_id.qty_producing = rec.y_total_output_quantity
        return res

    @api.depends('production_id')
    def get_total_wordorder_demand(self):
        for rec in self:
            rec.y_total_workorder_demand = rec.production_id.product_qty

    @api.depends('y_total_output_quantity','y_total_workorder_demand')
    def compute_total_remaining_quantity(self):
        for line_record in self:
            line_record.y_total_workorder_remaining = (line_record.y_total_workorder_demand-line_record.y_total_output_quantity) or 0

    @api.depends('time_ids.y_output_quantity')
    def compute_total_outquantity(self):
        for rec in self:
            rec.y_total_output_quantity = sum(rec.time_ids.mapped('y_output_quantity')) or 0
                
    def button_pending(self):
        res = super(workOrderCategory, self).button_pending()
        if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_is_output_quantity_validation'):
            return {
                        'name':_("Workorder Wizard"),
                        'view_mode': 'form',
                        'view_id': self.env.ref('manufacturing_base_18.mrp_workorder_center_category_wizard_outquantity').id,
                        'view_type': 'form',
                        'res_model': 'wizard.outquantity',
                        'context':{'y_workorder_id': self.id},
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'active_ids':self.ids
                    }

    def button_finish(self):
        if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_is_output_quantity_validation'):
            for rec in self:
                if rec.y_total_workorder_remaining > 0 and not rec._context.get('y_is_done_workorder'):
                    context = dict(default_y_workorder_id=rec.id,default_y_is_done_workorder=True,default_y_output_quantity=rec.y_total_workorder_remaining)
                    context.update({'y_workorder_id': rec.id})
                    return {
                            'name':_("Workorder Wizard"),
                            'view_mode': 'form',
                            'view_id': rec.env.ref('manufacturing_base_18.mrp_workorder_center_category_wizard_outquantity').id,
                            'view_type': 'form',
                            'res_model': 'wizard.outquantity',
                            'context':context,
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'active_ids':rec.ids
                        }
                else:
                    return super(workOrderCategory, self).button_finish()
        else:
            return super(workOrderCategory, self).button_finish()

    def unlink(self):
        for rec in self:
            if rec.date_start or rec.state == 'done':
                raise UserError("Operation cannot be Deleted")
        res = super(workOrderCategory,self).unlink()
        return res

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    y_is_output_quantity_validation = fields.Boolean(string="Output Quantity Validation")
    y_restrict_reserved_qty_warning = fields.Boolean(string="Allow operations Based on material Availability")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            y_is_output_quantity_validation = bool(params.get_param('manufacturing_base_18.y_is_output_quantity_validation')) or False,
            y_restrict_reserved_qty_warning = bool(params.get_param('manufacturing_base_18.y_restrict_reserved_qty_warning')) or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('manufacturing_base_18.y_is_output_quantity_validation',self.y_is_output_quantity_validation)
        self.env['ir.config_parameter'].sudo().set_param('manufacturing_base_18.y_restrict_reserved_qty_warning',self.y_restrict_reserved_qty_warning)

class MrpProductionOutputQty(models.Model):
    _inherit = 'mrp.production'

    y_sale_order_id = fields.Many2one('sale.order',"Sale Order.")
    y_partner_shipping_id = fields.Many2one('res.partner',string="Customer")

    def action_confirm(self):
        res = super(MrpProductionOutputQty,self).action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_is_output_quantity_validation'):
            for rec in self:
                for line in rec.workorder_ids:
                    line.y_total_workorder_demand = rec.product_qty
        return res

    def button_mark_done(self):
        for rec in self.workorder_ids.filtered(lambda x:x.state != 'cancel'):
            if rec.date_finished:
                if self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_is_output_quantity_validation'):
                    if rec.y_total_output_quantity == 0:
                        raise UserError("{} Operation Output Quantity not Recored".format(rec.name))
            else:
                raise UserError("{} Operation Not Started".format(rec.name))

        move_raw_ids = self.move_raw_ids.filtered(lambda move:move.quantity > 0 and move.product_uom_qty > 0)
        if not move_raw_ids:
            raise UserError("You cannot proceed with zero consumption. Please ensure at least one product should be consumed.")

        return super(MrpProductionOutputQty, self).button_mark_done()

    #this is standard function,Display the warning based on Boolean is configuraation
    # def _pre_button_mark_done(self):
    #     productions_to_immediate = self._check_immediate()
    #     if productions_to_immediate:
    #         return productions_to_immediate._action_generate_immediate_wizard()

    #     for production in self:
    #         if float_is_zero(production.qty_producing, precision_rounding=production.product_uom_id.rounding):
    #             raise UserError(_('The quantity to produce must be positive!'))
    #         if production.move_raw_ids and not any(production.move_raw_ids.mapped('quantity')):
    #             raise UserError(_("You must indicate a non-zero amount consumed for at least one of your components"))

    #     consumption_issues = self._get_consumption_issues()
    #     if not self.env['ir.config_parameter'].sudo().get_param('manufacturing_base_18.y_remove_consumption_warning'):
    #         if consumption_issues:
    #             return self._action_generate_consumption_wizard(consumption_issues)

    #     quantity_issues = self._get_quantity_produced_issues()
    #     if quantity_issues:
    #         return self._action_generate_backorder_wizard(quantity_issues)
    #     return True         
    
    def update_sale_order_number(self):
        if self.user_has_groups('manufacturing_base_18.group_mo_update_sale_order'):
            for rec in self:
                parent_sale = self.env['sale.order'].search([('name','=',rec.origin)])
                if not parent_sale:
                    mrp_origin = self.env['mrp.production'].search([('name','=',rec.origin)])
                    sale_origin = self.env['sale.order'].search([('name','=',mrp_origin.origin)])
                    if sale_origin:
                        rec.y_sale_order_id = mrp_origin.origin
                        rec.y_partner_shipping_id = sale_origin.partner_shipping_id.id
                    else:
                        rec.y_sale_order_id = mrp_origin.y_sale_order_id
                        sale_origin = self.env['sale.order'].search([('name','=',mrp_origin.y_sale_order_id)])
                        rec.y_partner_shipping_id = sale_origin.partner_shipping_id.id
                else:
                    rec.y_sale_order_id = rec.origin
                    sale_origin = self.env['sale.order'].search([('name','=',rec.origin)])
                    rec.y_partner_shipping_id = sale_origin.partner_shipping_id.id

                stock_picking_val = self.env['stock.picking'].search([('name','=',rec.origin)])
                if stock_picking_val:
                    rec.y_sale_order_id = stock_picking_val.y_sale_order_id
                    sale_origin = self.env['sale.order'].search([('name','=',stock_picking_val.y_sale_order_id)])
                    rec.y_partner_shipping_id = sale_origin.partner_shipping_id.id
        else:
            raise UserError(_("You are Not Authorised To Update Sale Order"))
