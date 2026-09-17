from odoo import models, fields, api, _

class StockMoveReport(models.Model):
    _inherit = 'stock.move'

    y_stock_product_code = fields.Char(related="product_id.default_code",string="Product Code")
    y_mrp_fg_product_code = fields.Char(related="y_mrp_fg_product_id.default_code",string="FG Code")
    y_mrp_parent_state = fields.Selection(related="raw_material_production_id.state")
    y_mrp_fg_product_id = fields.Many2one(related="raw_material_production_id.product_id",string="FG Product")
    y_mrp_due_date = fields.Datetime(related="raw_material_production_id.date_start")
    y_remaining_quantity = fields.Float(string="Remaining Qty",compute="get_remianing_qty")
    y_mrp_sale_order_id = fields.Many2one('sale.order',string="Production Sale Order",compute="get_sale_order")

    @api.depends('raw_material_production_id')
    def get_sale_order(self):
        for move in self:
            move.y_mrp_sale_order_id = move.raw_material_production_id.y_sale_order_id

    @api.depends('product_uom_qty','quantity')
    def get_remianing_qty(self):
        for rec in self:
            rec.y_remaining_quantity = rec.product_uom_qty - rec.quantity
                

class ProductTemplateStockMoveReport(models.Model):
    _inherit = "product.template"

    def action_stock_move_report(self):
        for rec in self:
            tree_view_id = self.env.ref('manufacturing_base_18.stock_move_report_inherit_tree_view').id
            return {
            'name': 'Stock Move',
            'view_mode': 'list',
            'views': [[tree_view_id, 'list']],
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'target': 'fullscreen',
            'domain': [('y_mrp_parent_state','in',('confirmed','progress','to_close')),('product_id','=',rec.product_variant_id.id)],
            "context":{},
            }