from odoo import fields, models, api,_,tools
from operator import itemgetter
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from lxml import etree

class InventoryAgingQtyValueReportView(models.Model):
    _name = 'inventory.aging.qty.value.report.view'
    _auto = False
    _description = "Inventory Ageing Qty Value Report View"

    company_id = fields.Many2one('res.company',string="Company")
    product_id = fields.Many2one('product.product')
    product_code = fields.Char(string="Product Code")
    product_name = fields.Char(string="Product Name")
    lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    lot_create_date = fields.Datetime(string="Lot Create Date")
    product_category_id = fields.Many2one('product.category',string="Product Category")
    product_uom_id = fields.Many2one('uom.uom',string="UoM")
    quantity = fields.Float(string="Quantity")
    value = fields.Float(string="Value")
    period_1_qty = fields.Float(string="Period 1 Qty")
    period_1_value = fields.Float(string="Period 1 Value")
    period_2_qty = fields.Float(string="Period 2 Qty")
    period_2_value = fields.Float(string="Period 2 Value")
    period_3_qty = fields.Float(string="Period 3 Qty")
    period_3_value = fields.Float(string="Period 3 Value")
    period_4_qty = fields.Float(string="Period 4 Qty")
    period_4_value = fields.Float(string="Period 4 Value")
    period_5_qty = fields.Float(string="Period 5 Qty")
    period_5_value = fields.Float(string="Period 5 Value")
    period_6_qty = fields.Float(string="Period 6 Qty")
    period_6_value = fields.Float(string="Period 6 Value")
    period_7_qty = fields.Float(string="Period 6 Qty")
    period_7_value = fields.Float(string="Period 6 Value")
    older_qty = fields.Float(string="Older Qty")
    older_value = fields.Float(string="Older Value")
    cost = fields.Float("Cost")
    avg_cost = fields.Float(string="Average Cost",compute="_compute_avg_cost_from_lot_product")

    @api.depends('company_id','lot_id','product_id')
    def _compute_avg_cost_from_lot_product(self):
        for quant in self:
            quant.avg_cost = quant.product_id.with_company(quant.company_id).avg_cost
            if quant.product_id.lot_valuated:
                quant.avg_cost = quant.lot_id.with_company(quant.company_id).avg_cost      

    def _select_query(self):
        return """  svl.product_id AS product_id,
                    svl.company_id AS company_id,
                    row_number() OVER () AS id,
                    svl.lot_id AS lot_id,
                    template.categ_id AS product_category_id,
                    template.uom_id AS product_uom_id,
                    0 AS value,
                    0 AS quantity,
                    0 AS cost,
                    0 AS period_1_qty,
                    0 AS period_2_qty,
                    0 AS period_3_qty,
                    0 AS period_4_qty,
                    0 AS period_5_qty,
                    0 AS period_6_qty,
                    0 AS period_7_qty,
                    0 AS older_qty,
                    0 AS period_1_value,
                    0 AS period_2_value,
                    0 AS period_3_value,
                    0 AS period_4_value,
                    0 AS period_5_value,
                    0 AS period_6_value,
                    0 AS period_7_value,
                    0 AS older_value

                     """
    def _from_query(self):
        return """  FROM 
                        stock_valuation_layer svl
                    LEFT JOIN 
                        product_product product ON product.id = svl.product_id
                    LEFT JOIN 
                        stock_lot lot ON lot.id = svl.lot_id
                    LEFT JOIN 
                        product_template template ON template.id = product.product_tmpl_id
                 """

    def _where_query(self):
        return """ WHERE template.type = 'consu' and template.is_storable = 't' """

    def _group_by_query(self):
        return """GROUP BY svl.product_id,svl.company_id,svl.lot_id,template.categ_id,template.uom_id"""


    def init(self):        
        tools.drop_view_if_exists(self._cr, 'inventory_aging_qty_value_report_view')
        select_query = self._select_query()
        from_query = self._from_query()
        where_query = self._where_query()
        group_by_query = self._group_by_query()
        # print('\n'*2)
        # print(select_query)
        # print('\n'*2)
        # print(from_query)
        # print('\n'*2)
        # print(where_query)
        # print('\n'*2)
        # print(group_by_query)
        # print('\n'*2)
        self._cr.execute("""
            CREATE OR REPLACE VIEW inventory_aging_qty_value_report_view AS (
                SELECT DISTINCT 
                    {select_query}

                    {from_query}
                    
                    {where_query}
                
                    {group_by_query}
                )""".format(select_query=select_query,from_query=from_query,where_query=where_query,group_by_query=group_by_query))

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + tuple(eval(self.env.user.y_inventory_aging_domain))


    @api.model
    def _get_view(self, view_id=None, view_type=None, **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        print(self.env.user.y_inventory_aging_domain,"44444444444444444444444444444")
        aging_intervals = eval(self.env.user.y_inventory_aging_domain)
        if aging_intervals:            
            field = arch.xpath("//field[@name='period_1_qty']")
            if field:
                field[0].set('string', aging_intervals[0])
            field = arch.xpath("//field[@name='period_2_qty']")
            if field:
                field[0].set('string', aging_intervals[1])
            field = arch.xpath("//field[@name='period_3_qty']")
            if field:
                field[0].set('string', aging_intervals[2])

            field = arch.xpath("//field[@name='period_4_qty']")
            if field:
                field[0].set('string', aging_intervals[3])

            field = arch.xpath("//field[@name='period_5_qty']")
            if field:
                field[0].set('string', aging_intervals[4])

            field = arch.xpath("//field[@name='period_6_qty']")
            if field:
                field[0].set('string', aging_intervals[5])

            field = arch.xpath("//field[@name='period_7_qty']")
            if field:
                field[0].set('string', aging_intervals[6])

            field = arch.xpath("//field[@name='older_qty']")
            if field:
                field[0].set('string', aging_intervals[7])

        # Value Fields
        value_aging_intervals = eval(self.env.user.y_inventory_value_aging_domain)
        if value_aging_intervals:
            field = arch.xpath("//field[@name='period_1_value']")
            if field:
                field[0].set('string', value_aging_intervals[0])
            field = arch.xpath("//field[@name='period_2_value']")
            if field:
                field[0].set('string', value_aging_intervals[1])
            field = arch.xpath("//field[@name='period_3_value']")
            if field:
                field[0].set('string', value_aging_intervals[2])

            field = arch.xpath("//field[@name='period_4_value']")
            if field:
                field[0].set('string', value_aging_intervals[3])

            field = arch.xpath("//field[@name='period_5_value']")
            if field:
                field[0].set('string', value_aging_intervals[4])

            field = arch.xpath("//field[@name='period_6_value']")
            if field:
                field[0].set('string', value_aging_intervals[5])

            field = arch.xpath("//field[@name='period_7_value']")
            if field:
                field[0].set('string', value_aging_intervals[6])

            field = arch.xpath("//field[@name='older_value']")
            if field:
                field[0].set('string', value_aging_intervals[7])
        
        return arch, view

class InventoryAgingQtyValueReport(models.Model):
    _name = 'inventory.aging.qty.value.report'
    _description =  "Inventory Ageing Value Report"
    _rec_name= 'product_id'

    company_id = fields.Many2one('res.company',string="Company")
    product_id = fields.Many2one('product.product')
    product_code = fields.Char(string="Product Code")
    product_name = fields.Char(string="Product Name")
    lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    lot_create_date = fields.Datetime(string="Lot Create Date")
    product_category_id = fields.Many2one('product.category',string="Product Category")
    product_uom_id = fields.Many2one('uom.uom',string="UoM")
    quantity = fields.Float(string="Quantity")
    value = fields.Float(string="Value")
    period_1_qty = fields.Float(string="Period 1 Qty")
    period_1_value = fields.Float(string="Period 1 Value")
    period_2_qty = fields.Float(string="Period 2 Qty")
    period_2_value = fields.Float(string="Period 2 Value")
    period_3_qty = fields.Float(string="Period 3 Qty")
    period_3_value = fields.Float(string="Period 3 Value")
    period_4_qty = fields.Float(string="Period 4 Qty")
    period_4_value = fields.Float(string="Period 4 Value")
    period_5_qty = fields.Float(string="Period 5 Qty")
    period_5_value = fields.Float(string="Period 5 Value")
    period_6_qty = fields.Float(string="Period 6 Qty")
    period_6_value = fields.Float(string="Period 6 Value")
    period_7_qty = fields.Float(string="Period 7 Qty")
    period_7_value = fields.Float(string="Period 7 Value")
    older_qty = fields.Float(string="Older Qty")
    older_value = fields.Float(string="Older Value")
    cost = fields.Float("Cost")
    avg_cost = fields.Float(string="Average Cost",compute="_compute_avg_cost_from_lot_product")

    @api.depends('company_id','lot_id','product_id')
    def _compute_avg_cost_from_lot_product(self):
        for quant in self:
            quant.avg_cost = quant.product_id.with_company(quant.company_id).avg_cost
            if quant.product_id.lot_valuated:
                quant.avg_cost = quant.lot_id.with_company(quant.company_id).avg_cost    

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + tuple(eval(self.env.user.y_inventory_aging_domain))


    @api.model
    def _get_view(self, view_id=None, view_type=None, **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        aging_intervals = eval(self.env.user.y_inventory_aging_domain)
        if aging_intervals:            
            field = arch.xpath("//field[@name='period_1_qty']")
            if field:
                field[0].set('string', aging_intervals[0])
            field = arch.xpath("//field[@name='period_2_qty']")
            if field:
                field[0].set('string', aging_intervals[1])
            field = arch.xpath("//field[@name='period_3_qty']")
            if field:
                field[0].set('string', aging_intervals[2])

            field = arch.xpath("//field[@name='period_4_qty']")
            if field:
                field[0].set('string', aging_intervals[3])

            field = arch.xpath("//field[@name='period_5_qty']")
            if field:
                field[0].set('string', aging_intervals[4])

            field = arch.xpath("//field[@name='period_6_qty']")
            if field:
                field[0].set('string', aging_intervals[5])

            field = arch.xpath("//field[@name='period_7_qty']")
            if field:
                field[0].set('string', aging_intervals[6])

            field = arch.xpath("//field[@name='older_qty']")
            if field:
                field[0].set('string', aging_intervals[7])

        # Value Fields
        value_aging_intervals = eval(self.env.user.y_inventory_value_aging_domain)
        if value_aging_intervals:
            field = arch.xpath("//field[@name='period_1_value']")
            if field:
                field[0].set('string', value_aging_intervals[0])
            field = arch.xpath("//field[@name='period_2_value']")
            if field:
                field[0].set('string', value_aging_intervals[1])
            field = arch.xpath("//field[@name='period_3_value']")
            if field:
                field[0].set('string', value_aging_intervals[2])

            field = arch.xpath("//field[@name='period_4_value']")
            if field:
                field[0].set('string', value_aging_intervals[3])

            field = arch.xpath("//field[@name='period_5_value']")
            if field:
                field[0].set('string', value_aging_intervals[4])

            field = arch.xpath("//field[@name='period_6_value']")
            if field:
                field[0].set('string', value_aging_intervals[5])

            field = arch.xpath("//field[@name='period_7_value']")
            if field:
                field[0].set('string', value_aging_intervals[6])

            field = arch.xpath("//field[@name='older_value']")
            if field:
                field[0].set('string', value_aging_intervals[7])
        
        return arch, view


    def action_inventory_aging_at_date(self):
        action = self.env["ir.actions.actions"]._for_xml_id("inventory_aging_report_flexible_dates.action_inventory_aging_value_report_wizard")
        return action

