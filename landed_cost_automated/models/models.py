# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import api, models, fields,tools, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super(PurchaseOrder,self).button_confirm()
        for line in self.order_line.filtered(lambda x:x.product_id.type == 'service' and x.product_id.product_tmpl_id.y_automated_landed_cost):
            stock_picking_id = self.picking_ids.filtered(lambda x:x.state not in ('done','cancel'))
            if stock_picking_id:
                if not stock_picking_id.y_landed_cost_ids.filtered(lambda x:x.y_purchase_line_id == line):
                    self.env['stock.landed.cost.lines'].create({
                                'product_id':line.product_id.id,
                                'name':line.product_id.name,
                                'account_id':line.product_id.property_account_expense_id.id,
                                'split_method':line.product_id.split_method_landed_cost,
                                'price_unit':line.product_id.standard_price,
                                'y_stock_picking_id': stock_picking_id[0].id,
                                'y_purchase_line_id':line.id,
                                })
        return res

    def button_approve(self, force=False):
        res = super().button_approve(force)
        for line in self.order_line.filtered(lambda x:x.product_id.type == 'service' and x.product_id.product_tmpl_id.y_automated_landed_cost):
            stock_picking_id = self.picking_ids.filtered(lambda x:x.state not in ('done','cancel'))
            if stock_picking_id:
                if not stock_picking_id.y_landed_cost_ids.filtered(lambda x:x.y_purchase_line_id == line):
                    self.env['stock.landed.cost.lines'].create({
                                'product_id':line.product_id.id,
                                'name':line.product_id.name,
                                'account_id':line.product_id.property_account_expense_id.id,
                                'split_method':line.product_id.split_method_landed_cost,
                                'price_unit':line.product_id.standard_price,
                                'y_stock_picking_id': stock_picking_id[0].id,
                                'y_purchase_line_id':line.id,
                                })
        return res



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def write(self,vals):
        res = super(PurchaseOrderLine,self).write(vals)
        for line in self:
            if line.order_id.state == 'purchase' and vals.get('product_id'):
                if line.product_id.type == 'service' and line.product_id.product_tmpl_id.y_automated_landed_cost:
                    stock_picking_id = line.order_id.picking_ids.filtered(lambda x:x.state not in ('done','cancel'))
                    if stock_picking_id:
                        if not stock_picking_id.y_landed_cost_ids.filtered(lambda x:x.y_purchase_line_id == line):
                            line.env['stock.landed.cost.lines'].create({
                                'product_id':line.product_id.id,
                                'name':line.product_id.name,
                                'account_id':line.product_id.property_account_expense_id.id,
                                'split_method':line.product_id.split_method_landed_cost,
                                'price_unit':line.product_id.standard_price,
                                'y_stock_picking_id': stock_picking_id[0].id,
                                'y_purchase_line_id':line.id,
                                })

        return res
        
class ProducttemplateNew(models.Model):
    _inherit = "product.template"

    y_automated_landed_cost = fields.Boolean(string="Automated Landed Cost",default=False)

class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    y_stock_picking_id = fields.Many2one('stock.picking')
    y_purchase_line_id = fields.Many2one('purchase.order.line')
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost',required=False)
    product_id = fields.Many2one('product.product', 'Product', domain=[('landed_cost_ok', '=', True),('y_automated_landed_cost','=',True)])

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    picking_ids = fields.Many2many('stock.picking', string='Transfers',copy=False, store=True)
    y_restrict_create_bool = fields.Boolean()

    
    # def compute_landed_cost(self):
    #     AdjustementLines = self.env['stock.valuation.adjustment.lines']
    #     AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()
    #     digits = self.env['decimal.precision'].precision_get('Product Price')
    #     towrite_dict = {}
    #     for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
    #         total_qty = 0.0
    #         total_cost = 0.0
    #         total_weight = 0.0
    #         total_volume = 0.0
    #         total_line = 0.0
    #         all_val_line_values = cost.get_valuation_lines()
    #         for val_line_values in all_val_line_values:
    #             for cost_line in cost.cost_lines:
    #                 val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
    #                 self.env['stock.valuation.adjustment.lines'].create(val_line_values)
    #             total_qty += val_line_values.get('quantity', 0.0)
    #             total_weight += val_line_values.get('weight', 0.0)
    #             total_volume += val_line_values.get('volume', 0.0)

    #             former_cost = val_line_values.get('former_cost', 0.0)
    #             # round this because former_cost on the valuation lines is also rounded
    #             total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

    #             total_line += 1

    #         for line in cost.cost_lines:
    #             value_split = 0.0
    #             for valuation in cost.valuation_adjustment_lines:
    #                 value = 0.0
    #                 if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
    #                     if line.split_method == 'by_quantity' and total_qty:
    #                         per_unit = (line.price_unit / total_qty)
    #                         value = valuation.quantity * per_unit
    #                     elif line.split_method == 'by_weight' and total_weight:
    #                         per_unit = (line.price_unit / total_weight)
    #                         value = valuation.weight * per_unit
    #                     elif line.split_method == 'by_volume' and total_volume:
    #                         per_unit = (line.price_unit / total_volume)
    #                         value = valuation.volume * per_unit
    #                     elif line.split_method == 'equal':
    #                         value = (line.price_unit / total_line)
    #                     elif line.split_method == 'by_current_cost_price' and total_cost:
    #                         per_unit = (line.price_unit / total_cost)
    #                         value = valuation.former_cost * per_unit
    #                     else:
    #                         value = (line.price_unit / total_line)

    #                     if digits:
    #                         value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
    #                         fnc = min if line.price_unit > 0 else max
    #                         value = fnc(value, line.price_unit - value_split)
    #                         value_split += value

    #                     if valuation.id not in towrite_dict:
    #                         towrite_dict[valuation.id] = value
    #                     else:
    #                         towrite_dict[valuation.id] += value
    #     for key, value in towrite_dict.items():
    #         AdjustementLines.browse(key).write({'additional_landed_cost': value})
    #     return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Unused Fields
    y_bool_field = fields.Boolean(default=False,copy=False)
    y_button_validate_bool = fields.Boolean(default=True,copy=False)
    y_button_box_landed_cost_bool = fields.Boolean(default=False,copy=False)
    y_post_validate_button_bools = fields.Boolean(default=False,copy=False)
    # END    
    
    y_post_validate_button_warning = fields.Boolean(default=False,copy=False)
    y_post_validate_button_success = fields.Boolean(default=False,copy=False)
    y_is_post_landedcost = fields.Boolean(default=False,copy=False)
    y_landed_cost_ids = fields.One2many('stock.landed.cost.lines','y_stock_picking_id')
    
    def button_validate(self):
        res = super(StockPicking,self).button_validate()
        if self.y_landed_cost_ids:
            self.write({'y_post_validate_button_warning' :True})
        return res

    def validate_lc(self):
        landed_cost_objs = self.env['stock.landed.cost'].search([('picking_ids', 'in', self.ids)])
        if landed_cost_objs:
            raise ValidationError(_("""For this Transfers already LandedCost is done."""))
        if not self.y_is_post_landedcost:
            landed_cost_obj = self.env['stock.landed.cost']
            move_ids_without_package = self.move_ids_without_package.filtered(lambda x:x.quantity > 0)
            if len(self.y_landed_cost_ids) and move_ids_without_package:
                valuation_quantity = sum(self.move_ids_without_package.stock_valuation_layer_ids.mapped('quantity'))
                po_order_quantity = sum(self.move_ids_without_package.purchase_line_id.mapped('product_qty'))                    
                if any(self.move_ids_without_package.filtered(lambda x:x.product_uom != x.purchase_line_id.product_uom)):
                    po_order_quantity = 0
                    for move in self.move_ids_without_package:
                        if move.product_uom != move.purchase_line_id.product_uom:
                            po_order_quantity += move.purchase_line_id.product_uom._compute_quantity(move.purchase_line_id.product_qty,move.product_uom)                                
                        else:
                            po_order_quantity += move.purchase_line_id.product_qty
                for lc_line in self.y_landed_cost_ids:
                    lc_line.price_unit = round((lc_line.y_purchase_line_id.price_unit/po_order_quantity) * valuation_quantity,2)
                landed_cost_obj = self.env['stock.landed.cost'].create({
                    'picking_ids':[(4, self.id)],
                    'y_restrict_create_bool':True,
                    'target_model':'picking',
                    'cost_lines':[(6, 0, self.y_landed_cost_ids.ids)]
                    })
                landed_cost_obj.compute_landed_cost()
                landed_cost_obj.sudo().button_validate()
                
            if landed_cost_obj:
                self.y_post_validate_button_warning = False
                self.y_post_validate_button_success = True
                self.y_is_post_landedcost = True

    def view_landed_cost_tree(self):
        self.ensure_one()
        tree_view = self.env.ref('stock_landed_costs.view_stock_landed_cost_tree')
        view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form')
        return {
            'name': _('Landed Cost'),
            'view_type': 'form',
            'view_mode': 'list, form',
            'res_model': 'stock.landed.cost',
            'domain': [('picking_ids', 'in', self.ids)],
            'view_id': view_id.id,
            'views': [(tree_view.id, 'list'),(view_id.id, 'form')],
            'type': 'ir.actions.act_window',

            }

    def _create_backorder(self, backorder_moves=None):
        backorders = super()._create_backorder(backorder_moves)
        for line in backorders.move_ids_without_package.purchase_line_id.order_id.order_line.filtered(lambda x:x.product_id.type == 'service' and x.product_id.product_tmpl_id.y_automated_landed_cost):
            stock_picking_id = backorders.filtered(lambda x:x.state not in ('done','cancel'))
            if stock_picking_id:
                land_cost_vals = self.env['stock.landed.cost.lines'].create({
                            'product_id':line.product_id.id,
                            'name':line.product_id.name,
                            'account_id':line.product_id.property_account_expense_id.id,
                            'split_method':line.product_id.split_method_landed_cost,
                            'price_unit':0,
                            'y_stock_picking_id': stock_picking_id[0].id,
                            'y_purchase_line_id': line.id,
                            })    

        return backorders

class StockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    y_remaining_qty = fields.Float(string="Remaining Qty" ,related='move_id.stock_valuation_layer_ids.remaining_qty')
    y_calculated_landed_cost = fields.Float(string="Calculated Landed Cost",compute="_compute_clc_landed_cost")

    @api.depends('y_remaining_qty','additional_landed_cost','quantity')
    def _compute_clc_landed_cost(self):
        for rec in self:
            if rec.quantity != 0:
                rec.y_calculated_landed_cost = (rec.y_remaining_qty * rec.additional_landed_cost) / rec.quantity

    @api.depends('move_id')
    def _compute_remaining_qty(self):
        for rec in self:
            rec.y_remaining_qty = sum(self.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))

class Stockmove(models.Model):
    _inherit = "stock.move"

    y_button_validate_bool = fields.Boolean(default=False,compute="get_y_button_validate_bool")
    y_quantity_done = fields.Float(store=True)

    @api.depends('y_quantity_done','product_uom_qty')
    def get_y_button_validate_bool(self):
        for rec in self:
            rec.y_button_validate_bool = False
            if rec.y_quantity_done and rec.product_uom_qty:
                if rec.y_quantity_done == rec.product_uom_qty:
                    rec.y_button_validate_bool = True