# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import api, models, fields,tools, _
from odoo.exceptions import UserError, ValidationError

class MrpWorkCenter(models.Model):
    _inherit = "mrp.workcenter"

    y_workcenter_landed_cost_lines_ids = fields.One2many('workcenter.landed.cost.lines','y_workcenter_id',string="Workcenter Landed Cost Lines")

class WorkcenterLandedCost(models.Model):
    _name = "workcenter.landed.cost.lines"

    y_product_id = fields.Many2one('product.product',string="Cost Element")
    y_mrp_product_id = fields.Many2one('product.product',string="Product")
    y_method_type = fields.Selection([('hours', 'Hours'),
                                    ('qty', 'Qty'),
                                    ('percentage', 'Percentage'),
                                    ('fixed_amount', 'Fixed Amount'),
                                    ], string='Type')
    y_cost_per_hr = fields.Float(string="Cost per",digits=(16, 2))
    y_workcenter_id = fields.Many2one('mrp.workcenter',string="Workcenter")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)

    y_standard_weight = fields.Float(string="Standard Weight",related='y_mrp_product_id.product_tmpl_id.weight',store=True)
    y_cost_per_weight = fields.Float(string="Cost per Weight")
    y_product_weight_in_lbs = fields.Selection([
        ('0', 'Kilograms'),
        ('1', 'Pounds'),
    ], 'UOM',compute="_compute_weight_uom_id_from_ir_config_parameter")

    @api.depends('y_workcenter_id')
    def _compute_weight_uom_id_from_ir_config_parameter(self):
        for line in self:
            line.y_product_weight_in_lbs = self.env['ir.config_parameter'].sudo().get_param('product.weight_in_lbs') or '0'
            
    @api.constrains('y_cost_per_hr')
    def _check_cost_per_hr(self):
        for record in self:
            if record.y_cost_per_hr <= 0:
                raise ValidationError("Cost per cannot be negative/zero.")

    @api.onchange('y_standard_weight','y_cost_per_weight','y_method_type')
    def _onchange_standard_weight(self):
        for record in self:
            if record.y_method_type == 'qty':
                record.y_cost_per_hr = record.y_standard_weight * record.y_cost_per_weight

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def calculate_cost(self,duration_seconds, cost_per_hour):
        cost = (duration_seconds / 3600) * cost_per_hour
        return cost


    def button_mark_done(self):
        res = super().button_mark_done()
        for rec in self:
            stock_valuation_layer_ids = rec.move_finished_ids.stock_valuation_layer_ids
            if stock_valuation_layer_ids:
                for workorder in rec.workorder_ids:
                    for workorder_landed_cost_lines in workorder.workcenter_id.y_workcenter_landed_cost_lines_ids.filtered(lambda x:x.y_mrp_product_id == rec.product_id and x.y_company_id == rec.company_id):
                        cost = 0
                        if workorder_landed_cost_lines.y_method_type == 'hours':
                            duration = 0
                            for time_id in workorder.time_ids:
                                dd = (time_id.date_end - time_id.date_start).seconds
                                duration += (time_id.date_end - time_id.date_start).seconds
                            cost = self.calculate_cost(duration,workorder_landed_cost_lines.y_cost_per_hr)
                        elif workorder_landed_cost_lines.y_method_type == 'qty':
                            cost = (workorder.qty_producing * workorder_landed_cost_lines.y_cost_per_hr)
                        elif workorder_landed_cost_lines.y_method_type == 'percentage':
                            svl_obj = stock_valuation_layer_ids.filtered(lambda x:x.product_id == rec.product_id and not x.stock_landed_cost_id)
                            cost = (svl_obj.value * workorder_landed_cost_lines.y_cost_per_hr)/100
                        elif workorder_landed_cost_lines.y_method_type == 'fixed_amount':
                            cost = workorder_landed_cost_lines.y_cost_per_hr
                        val = self.env['stock.landed.cost'].sudo().create({
                            'mrp_production_ids': [(4, rec.id)],
                            'target_model': 'manufacturing',
                        })
                        land_cost_vals = self.env['stock.landed.cost.lines'].sudo().create({
                            'cost_id': val.id, 
                            'product_id': workorder_landed_cost_lines.y_product_id.id,
                            'name': workorder_landed_cost_lines.y_product_id.name,
                            'account_id': workorder_landed_cost_lines.y_product_id.property_account_expense_id.id if workorder_landed_cost_lines.y_product_id.property_account_expense_id else workorder_landed_cost_lines.y_product_id.categ_id.property_account_expense_categ_id.id,
                            'split_method': workorder_landed_cost_lines.y_product_id.split_method_landed_cost,
                            'price_unit': cost
                        })
                        val.write({
                            'cost_lines': [(4, land_cost_vals.id)]
                        })
                        val.sudo().compute_landed_cost()
                        val.sudo().button_validate()
        return res


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    y_product_ids = fields.Many2many('product.product',string="Service Products",store=True)

    @api.model
    def create(self,vals):
        if vals.get('stock_landed_cost_id') :
            landedcost_obj = self.env['stock.landed.cost'].sudo().browse(vals.get('stock_landed_cost_id'))
            vals['y_product_ids'] = landedcost_obj.cost_lines.mapped('product_id')
        return super().create(vals)






