# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class MrpOrderReport(models.Model):
    _name = "prix.mrp.report"
    _description = "mrp report"

    y_mo_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    y_mo_date = fields.Datetime('MO Date', related='y_mo_id.y_date_confirm')
    y_fgproduct_id = fields.Many2one('product.product', 'FG Product')
    y_product_id = fields.Many2one('product.product', 'Component')
    y_sale_order_id = fields.Many2one('sale.order',related='y_mo_id.y_sale_order_id')
    y_move_id = fields.Many2one('stock.move', string="Raw Material Move Line")

    #for FG Products
    y_planned_fgp_qty = fields.Float('Planned FG Qty')
    y_planned_fgp_cost = fields.Float('Planned FG Cost')

    y_actual_fgp_qty = fields.Float('Actual FG Qty',compute="compute_actual_fg_quantity",store=True)
    y_actual_fgp_cost = fields.Float('Actual FG Cost',compute="compute_actual_fg_cost",store=True)

    #for components
    y_planned_qty = fields.Float('Planned Qty')
    y_actual_qty = fields.Float('Actual Qty')

    y_purchase_consum_cost = fields.Float("Purchase Cost")

    y_planned_cost = fields.Float('Planned Cost')
    y_actual_cost = fields.Float('Actual Cost')
    
    y_currency_id = fields.Many2one('res.currency',related='y_product_id.currency_id',store=True)

    y_variance_qty = fields.Float(compute="compute_variance_qty",string='Variance Qty', store=True)
    y_variance_cost = fields.Float(compute="compute_variance_cost",string='Variance Cost' , store=True)

    y_variance_qty_percent = fields.Float(compute="compute_variance_qty_percent",string='Variance Qty(%)', store=True)
    y_variance_cost_percent = fields.Float(compute="compute_variance_cost_percent",string='Variance Cost(%)', store=True)


    @api.depends('y_actual_qty','y_mo_id')
    def compute_actual_fg_quantity(self):
        for each in self:
            actual_qty = sum(each.y_mo_id.y_prod_analysis_ids.mapped('y_actual_qty'))
            each.y_actual_fgp_qty = actual_qty

    @api.depends('y_actual_cost','y_mo_id')
    def compute_actual_fg_cost(self):
        for each in self:
            actual_cost = sum(each.y_mo_id.y_prod_analysis_ids.mapped('y_actual_cost'))
            each.y_actual_fgp_cost = actual_cost

    @api.depends('y_planned_qty','y_actual_qty')
    def compute_variance_qty(self):
        for rec in self:
            rec.y_variance_qty = rec.y_planned_qty - rec.y_actual_qty

    @api.depends('y_planned_cost','y_actual_cost')
    def compute_variance_cost(self):
        for rec in self:
            rec.y_variance_cost = rec.y_planned_cost - rec.y_actual_cost

    @api.depends('y_planned_qty','y_variance_qty')
    def compute_variance_qty_percent(self):
        for rec in self:
            if rec.y_planned_qty and rec.y_variance_qty:
                rec.y_variance_qty_percent = (rec.y_variance_qty * 100) / rec.y_planned_qty
            else:
                rec.y_variance_qty_percent = 0.0

    @api.depends('y_planned_cost','y_variance_cost')
    def compute_variance_cost_percent(self):
        for rec in self:
            if rec.y_planned_cost and rec.y_variance_cost:
                rec.y_variance_cost_percent = (rec.y_variance_cost * 100) / rec.y_planned_cost
            else:
                rec.y_variance_cost_percent = 0.0

  
    @api.model
    def retrieve_dashboard(self, mo_id=None):
        result = {
            'mo': '',
            'planned_qty': 0.0,
            'planned_fg_cost': 0.0,
            'actual_qty': 0.0,
            'actual_fg_cost': 0.0,
            'yield_val': "0.00",
            'yield_percentage': "0.00",
            'is_increased': False,
            'company_currency_symbol': self.env.company.currency_id.symbol,
            'cost_per_unit_planned': "0.00",
            'cost_per_unit_actual': "0.00",
        }

        if mo_id:
            mo_id = int(mo_id)
            prod_analysis_ids = self.env['prix.mrp.report'].search([('y_mo_id', '=', mo_id)])
            if prod_analysis_ids:
                fg_prod_analysis = prod_analysis_ids[0]  # Assuming first record as FG
                planned_qty = fg_prod_analysis.y_planned_fgp_qty or 0.0
                planned_cost = fg_prod_analysis.y_planned_fgp_cost or 0.0
                actual_qty = fg_prod_analysis.y_mo_id.product_qty or 0.0
                actual_cost = sum(prod_analysis_ids.mapped('y_actual_cost')) or 0.0

                result.update({
                    'y_mo_id': fg_prod_analysis.y_mo_id.id,
                    'planned_qty': round(planned_qty,2),
                    'planned_fg_cost': round(planned_cost,2),
                    'actual_qty': round(actual_qty,2),
                    'actual_fg_cost': round(actual_cost,2),
                })

                # Compute cost per unit
                planned_unit_cost = planned_cost / planned_qty if planned_qty else 0.0
                actual_unit_cost = actual_cost / actual_qty if actual_qty else 0.0

                 # Yield variance
                if planned_unit_cost and actual_unit_cost:
                    yield_val = actual_unit_cost - planned_unit_cost
                    yield_percent = ((actual_unit_cost / planned_unit_cost) * 100) - 100

                    result.update({
                        'yield_val': format(yield_val, ".2f"),
                        'yield_percentage': format(yield_percent, ".2f"),
                        'is_increased': yield_val > 0,
                    })

                # Cost per unit breakdown
                result['cost_per_unit_planned'] = format(planned_unit_cost, ".2f") if planned_unit_cost else "0.00"
                result['cost_per_unit_actual'] = format(actual_unit_cost, ".2f") if actual_unit_cost else "0.00"

        return result


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    y_prod_analysis_count = fields.Integer(compute="get_analysis_count", store=True)
    y_prod_analysis_ids = fields.One2many('prix.mrp.report','y_mo_id',string="Production Analysis Lines")

    @api.depends('y_prod_analysis_ids')
    def get_analysis_count(self):
        for each in self:
            each.y_prod_analysis_count = len(each.y_prod_analysis_ids.ids)

    def _get_compo_planned_vals(self, move,production):
        company = production.company_id
        cost = move.product_id.with_company(company).standard_price * move.product_uom_qty
        return cost

    def _get_compo_actual_vals(self, move,production):
        company = production.company_id
        cost = move.product_id.with_company(company).standard_price  * move.quantity
        if move.product_id.lot_valuated and move.lot_ids:
            cost = sum([line.lot_id.with_company(company).standard_price * line.quantity for line in move.move_line_ids if line.lot_id.with_company(company).standard_price])
        return cost

    def _get_fg_planned_vals(self,production):
        company = production.company_id
        cost = production.product_id.with_company(company).standard_price * production.product_qty
        return cost

    def _get_compo_purchase_consum_cost(self, move,production):
        company = production.company_id
        cost = 0
        if move.product_id.lot_valuated and move.lot_ids:
            cost = sum([line.lot_id.with_company(company).purchase_cost_per_unit for line in move.move_line_ids if line.lot_id.with_company(company).purchase_cost_per_unit])
        return cost


    def _generate_or_update_report_line(self, production, move, update_actual=False):
        Report = self.env['prix.mrp.report']
        existing = production.y_prod_analysis_ids.filtered(lambda line:line.y_move_id == move)

        planned_qty = move.product_uom_qty
        planned_cost = self._get_compo_planned_vals(move,production)

        vals = {
            'y_mo_id': production.id,
            'y_move_id': move.id,
            'y_mo_date': production.y_date_confirm,
            'y_planned_fgp_qty': production.product_qty,
            'y_planned_fgp_cost': self._get_fg_planned_vals(production),
            'y_fgproduct_id': production.product_id.id,
            'y_product_id': move.product_id.id,
            'y_planned_qty': planned_qty,
            'y_purchase_consum_cost': self._get_compo_purchase_consum_cost(move,production),
            'y_planned_cost': planned_cost,
        }

        if update_actual:
            actual_qty = move.quantity
            actual_cost = self._get_compo_actual_vals(move,production)

            vals.update({
                'y_actual_qty': actual_qty,
                'y_actual_cost': actual_cost,
            })

        if existing:
            existing.write(vals)
        else:
            Report.create(vals)

    
    def action_confirm(self):
        self._check_company()
        for production in self:
            for move in production.move_raw_ids:
                self._generate_or_update_report_line(production,move)
        return super(MrpProduction, self).action_confirm()

    def button_mark_done(self):
        for production in self:
            for move in production.move_raw_ids:
                self._generate_or_update_report_line(production,move,update_actual=True)
                
        return super(MrpProduction, self).button_mark_done()

    def yield_analysis_values_server_action(self):
        for production in self:
            for move in production.move_raw_ids:
                if production.state in ('progress', 'to_close', 'done', 'cancel'):
                    self._generate_or_update_report_line(production,move,update_actual=True)
                else:
                    self._generate_or_update_report_line(production,move)
        
    def action_view_action_mrp_reports_records(self):
        self.yield_analysis_values_server_action()
        view_id = self.env.ref('yield_management.manufacturing_report_list_with_dashboard_view').id
        return {
            'name': 'Yield Analysis',
            'view_mode': 'list,pivot,graph',
            'views': [[view_id, 'list'], [False, 'pivot'], [False, 'graph']],
            'res_model': 'prix.mrp.report',
            'type': 'ir.actions.act_window',
            'domain': [('y_mo_id', '=', self.id)],
        }