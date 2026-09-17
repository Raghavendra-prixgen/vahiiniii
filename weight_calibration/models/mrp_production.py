# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'
   
    y_mrp_ideal_weight = fields.Float('Planned Ideal Weight ', compute='compute_y_mrp_ideal_weight',store=True ,digits=(12,3),copy=False)
    y_fg_actual_weight = fields.Float('Actual Weight of FG',store=True ,digits=(12,3),copy=False)
    y_product_actual_weight = fields.Float('Actual Weight of By products' ,store=True, compute='compute_actual_weight', digits=(12,3),copy=False)
    y_total_actual_weight = fields.Float('Actual Total Weight', store=True ,compute='compute_y_total_actual_weight',copy=False)
    y_check_toggle = fields.Boolean('Weight Calibration' , store=True,copy=False)
    y_check_approve_weight = fields.Boolean('check approve',store=True,copy=False)
    
    y_actual_ideal_weight = fields.Float('Actual Ideal Weight',compute='compute_actual_ideal_weight',store=True,digits=(12,3),copy=False)

    @api.depends('move_byproduct_ids')
    def compute_actual_weight(self):
        for order in self:
            total_qty = 0
            for quantities in order.move_byproduct_ids:
                total_qty += quantities.y_actual_weight_cal
            order.update({
                'y_product_actual_weight': total_qty,
            })

    @api.depends('qty_producing','product_id','product_id.weight')
    def compute_actual_ideal_weight(self):    
        for weight in self:
            if weight.product_id.weight != 0:
                weight.y_actual_ideal_weight = weight.qty_producing * weight.product_id.weight 
            else:
                weight.y_actual_ideal_weight = 0
                
    @api.depends('bom_id','bom_id.y_ideal_weight','product_qty','bom_id.product_qty')
    def compute_y_mrp_ideal_weight(self):
        for weight in self:
            if weight.bom_id.product_qty != 0:
                ratio = weight.bom_id.y_ideal_weight/ weight.bom_id.product_qty
                weight.y_mrp_ideal_weight = weight.product_qty * ratio 
            else:
                weight.y_mrp_ideal_weight = 0
        
            if weight.product_id.y_toggle_button == True:
                weight.y_check_toggle = True
            else:
                weight.y_check_toggle = False

    @api.depends('y_fg_actual_weight','y_product_actual_weight')
    def compute_y_total_actual_weight(self):
        for record in self:
            record.y_total_actual_weight = record.y_fg_actual_weight + record.y_product_actual_weight
            
    def button_mark_done(self):
        for rec in self:
            # Check if weight difference is approved
            if rec.product_id.y_toggle_button and not rec._get_subcontract_move():
                if rec.y_fg_actual_weight != 0 and rec.qty_producing != 0 and rec.y_actual_ideal_weight != rec.y_total_actual_weight and not rec.y_check_approve_weight:
                    raise ValidationError(
                        "Weight difference approval is required before marking this Manufacturing Order as done.\n"
                        "Please approve the weight difference."
                    )
                # Check if FG actual weight is zero
                if rec.qty_producing == 0:
                    raise ValidationError("The quantity being produced cannot be zero. Please update the quantity before proceeding.")
                if rec.y_fg_actual_weight == 0:
                    raise ValidationError("The actual weight of FG cannot be zero. Please enter a valid weight.")
        return super(MrpProduction, self).button_mark_done()

    @api.onchange('y_fg_actual_weight','move_raw_ids')
    def _onchange_y_fg_actual_weight_approve(self):
        if self.y_check_approve_weight:
            self.y_check_approve_weight = False
    
    def approve_weight_difference(self):
        if self.qty_producing == 0:
            raise ValidationError("The quantity being produced cannot be zero. Please update the quantity before proceeding.")

        if self.y_fg_actual_weight == 0:
            raise ValidationError("The actual weight of FG cannot be zero. Please provide a valid weight.")
        
        # for line in self.move_raw_ids:
        #     # Adjust raw material quantities based on total actual weight
        #     if line.move_line_ids:
        #         line.move_line_ids[:1].quantity = line.y_ratio_for_weight * self.y_total_actual_weight
        #     else:
        #         line.quantity = line.y_ratio_for_weight * self.y_total_actual_weight


        # Get all move lines that need lot assignment
        production_moves = self.move_raw_ids.filtered(
            lambda move: move.state not in ('done', 'cancel') and 
                        move.product_id.tracking in ['lot', 'serial']
        )
        
        insufficient_materials = []
        # Process each move that requires lot assignment
        for move in production_moves:
            # Clear any existing move lines
            move.move_line_ids.unlink()
            move_quantity = move.y_ratio_for_weight * self.y_total_actual_weight
            
            # Get available quants for this product sorted by date (FIFO)
            domain = [
                ('product_id', '=', move.product_id.id),
                ('location_id', '=', move.location_id.id),
                ('quantity', '>', 0),
                ('lot_id', '!=', False),
            ]
            
            quants = self.env['stock.quant'].search(domain, order='in_date asc')
            
            # Calculate total available quantity from quants
            available_qty = sum(quant.quantity for quant in quants)
            
            # Compare with required quantity
            if float_compare(available_qty, move_quantity, 
                            precision_rounding=move.product_uom.rounding) < 0:
                # Add to list of insufficient materials
                insufficient_materials.append({
                    'product': move.product_id.display_name,
                    'required': move_quantity,
                    'available': available_qty,
                    'uom': move.product_uom.name
                })
                continue
            
            # Only process if we have enough materials
            remaining_qty = move_quantity
            move_line_vals_list = []
            
            # Assign lots based on FIFO until we fulfill the required quantity
            for quant in quants:
                if float_compare(remaining_qty, 0, precision_rounding=move.product_uom.rounding) <= 0:
                    break
                    
                # Determine quantity to take from this lot
                qty_to_take = min(remaining_qty, quant.quantity)
                
                # Create a move line for this lot
                move_line_vals = {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id, 
                    'location_dest_id': move.location_dest_id.id,
                    'lot_id': quant.lot_id.id,
                    'qty_done': qty_to_take,
                }
                move_line_vals_list.append((0, 0, move_line_vals))
                
                # Update remaining quantity
                remaining_qty -= qty_to_take
            
            # Validate that all required quantity has been assigned
            total_assigned = sum(vals[2]['qty_done'] for vals in move_line_vals_list)
            if float_compare(total_assigned, move_quantity, 
                            precision_rounding=move.product_uom.rounding) < 0:
                insufficient_materials.append({
                    'product': move.product_id.display_name,
                    'required': move_quantity,
                    'available': total_assigned,
                    'uom': move.product_uom.name
                })
                continue
                
            # Create the move lines
            if move_line_vals_list:
                move.write({'move_line_ids': move_line_vals_list})
        
        # Check for non-tracked products as well
        non_tracked_moves = self.y_co_prod_mo_id.move_raw_ids.filtered(
            lambda move: move.state not in ('done', 'cancel') and 
                        move.product_id.tracking == 'none'
        )
        
        for move in non_tracked_moves:
            # Get available quantity
            available_qty = self.env['stock.quant']._get_available_quantity(
                move.product_id, move.location_id)
            
            # Compare with required quantity
            if float_compare(available_qty, move_quantity, 
                            precision_rounding=move.product_uom.rounding) < 0:
                insufficient_materials.append({
                    'product': move.product_id.display_name,
                    'required': move_quantity,
                    'available': available_qty,
                    'uom': move.product_uom.name
                })
        
        # If there are any insufficient materials, raise validation error
        if insufficient_materials:
            error_message = _("Cannot complete co-product MO due to insufficient materials:\n\n")
            for item in insufficient_materials:
                error_message += _("- %s: Required %.2f %s, Available %.2f %s\n") % (
                    item['product'], item['required'], item['uom'], 
                    item['available'], item['uom']
                )
            raise ValidationError(error_message)
        

        # Mark weight difference as approved
        self.y_check_approve_weight = True
          
    @api.onchange('bom_id')
    def onchange_bom_id(self):
        for rec in self:
            for line in rec.move_raw_ids:
                value = self.env['mrp.bom.line'].search([('id', '=', line.bom_line_id.id)])
                line.y_ratio_for_weight = value.y_ratio_for_weight
   
class StockMoveline(models.Model):
    _inherit = 'stock.move.line'

    y_actual_weight_cal = fields.Float(string='Actual Weight in Kgs', store=True)
    
class StockMove(models.Model):
    _inherit = 'stock.move'

    y_actual_weight_cal = fields.Float(string='Actual Weight in Kg', store=True)
    y_ratio_for_weight = fields.Float('Ratio for weight of o/p to weight of i/p',related="bom_line_id.y_ratio_for_weight",store=True)
   

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    y_ideal_weight = fields.Float('Ideal Weight', compute='compute_y_ideal_weight', store=True,inverse='compute_bom_weight')
    y_ideal_weight_uom_name = fields.Char('Weight unit of measure label', compute='_ideal_compute_weight_uom_name',store=True)
    y_check_bom_weight = fields.Boolean('check bom weight',store=True)
    
    @api.depends('product_tmpl_id.weight','product_qty','product_tmpl_id')
    def compute_y_ideal_weight(self):
        for each in self:
            each.y_ideal_weight = each.product_qty * each.product_tmpl_id.weight

    def _get_default_weight_uom(self):
        return self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    def _ideal_compute_weight_uom_name(self):
        self.y_ideal_weight_uom_name = self._get_default_weight_uom()

    @api.depends('product_tmpl_id','product_qty')
    def compute_bom_weight(self):
        for each in self:
            if each.product_tmpl_id.y_toggle_button == True:
                each.y_check_bom_weight = True

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    
    y_ratio_for_weight = fields.Float('Ratio for weight of o/p to weight of i/p', compute='compute_ratio_for_weight', store=True)

    @api.depends('product_qty','product_id','bom_id.y_ideal_weight')
    def compute_ratio_for_weight(self):
        for rec in self:
            if rec.bom_id.y_ideal_weight != 0 and rec.product_qty != 0:
                rec.y_ratio_for_weight = rec.product_qty / rec.bom_id.y_ideal_weight
            else:
                rec.y_ratio_for_weight = 0
                
                
# class MrpConsumption(models.TransientModel):
#     _inherit = 'mrp.consumption.warning'