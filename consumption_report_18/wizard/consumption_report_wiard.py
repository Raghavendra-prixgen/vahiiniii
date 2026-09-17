from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools.float_utils import float_round, float_is_zero
from odoo import tools

class ConsumptionReport(models.Model):
    _name = 'mrp.production.consumption.report'
    _auto = False
        
    id = fields.Integer("ID")
    y_name = fields.Char('Name')
    y_date = fields.Date('Date')
    y_in_product_id = fields.Many2one('product.product',domain="[('type', 'in', ('product', 'consu'))]", string="Components")
    y_product_code = fields.Char('Product Code')
    y_product_uom = fields.Many2one('uom.uom', string="UOM")
    y_planned_consu_qty = fields.Float('Planned Consumption(Qty)')
    y_actual_consu_qty = fields.Float('Actual Consumption(Qty)')
    y_variance_qty = fields.Float('Variance(Qty)')
    y_planned_consu_val = fields.Float('Planned Consumption(Value)' , readonly=True)
    y_actual_consu_val = fields.Float('Actual Consumption(Value)', readonly=True)
    y_variance_val = fields.Float('Variance(Value)', readonly=True)
    y_lot_id = fields.Many2one('stock.lot',string="Lot Number")
    y_unit_cost = fields.Float('Unit Cost',readonly=True)
    y_out_product_id = fields.Many2one('product.product',  string="FG Product")
    y_source_document = fields.Char('Source Document')
    y_mrp_name = fields.Char('Manufacturing Order')
    y_company_id = fields.Many2one('res.company',string="Company")
    y_stock_move_id = fields.Many2one('stock.move', string="Stock Move")
    y_production_id = fields.Many2one('mrp.production',string="Manufacturing Order")
    # y_analytic_distribution_id = fields.Many2one('account.analytic.account',string="Analytic Distribution")
    
    @api.model
    def init(self):
        company = self.env.company.id
        tools.drop_view_if_exists(self._cr, 'mrp_production_consumption_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW mrp_production_consumption_report AS (
            WITH base_data AS (
                SELECT
                row_number() OVER (PARTITION BY mp.id ORDER BY sm.date) as id,

                    sm.id as y_stock_move_id,
                    mp.id as y_production_id,
                    %(company)s AS y_company_id,
                    sm.name as y_name,
                    sm.date as y_date,
                    sm.product_id as y_in_product_id,
                    pp.default_code as y_product_code,
                    uom.id as y_product_uom,
                    sml.quantity as y_actual_consu_qty,
                    sm.product_uom_qty as y_planned_consu_qty,
                    (sm.product_uom_qty - sml.quantity) as y_variance_qty,
                    svl.unit_cost as y_unit_cost,
                    (svl.unit_cost * sml.quantity) as y_actual_consu_val,
                    (svl.unit_cost * sm.product_uom_qty) as y_planned_consu_val,
                    ((svl.unit_cost * sm.product_uom_qty) - (svl.unit_cost * sml.quantity)) as y_variance_val,
                    sml.lot_id as y_lot_id,
                    mp.product_id as y_out_product_id,
                    mp.name as y_mrp_name,
                    mp.origin as y_source_document
                FROM 
                    stock_move AS sm 
                    LEFT JOIN stock_move_line AS sml ON sml.move_id = sm.id
                    LEFT JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                    LEFT JOIN product_product AS pp ON pp.id = sm.product_id             
                    LEFT JOIN product_template AS pt ON pt.id = pp.product_tmpl_id 
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_dest_id
                    LEFT JOIN uom_uom AS uom ON uom.id = sm.product_uom
                    LEFT JOIN mrp_production AS mp ON mp.id = sm.raw_material_production_id
                    
                WHERE 
                    sl.usage = 'production' AND mp.state = 'done'
                    AND (svl.unit_cost * sml.quantity != 0 OR svl.unit_cost * sm.product_uom_qty != 0) 
                    AND sm.company_id = %(company)s 
                ),
            scrap_data AS (
                SELECT
                row_number() OVER (PARTITION BY mp.id ORDER BY ss.date_done) as id,
                    ss.id as y_scrap_id,
                    mp.id as y_production_id,
                    %(company)s AS y_company_id,
                    ss.name as y_name,
                    ss.date_done as y_date,
                    mp.product_id as y_in_product_id,
                    pp.default_code as y_product_code,
                    uom.id as y_product_uom,
                    ss.scrap_qty as y_actual_consu_qty,
                    0 as y_planned_consu_qty,
                    0 as y_variance_qty,
                    0 as y_unit_cost,
                    0 as y_actual_consu_val,
                    0 as y_planned_consu_val,
                    0 as y_variance_val,
                    ss.lot_id as y_lot_id,
                    ss.product_id as y_out_product_id,
                    ss.origin as y_mrp_name,
                    mp.name as y_source_document
                FROM 
                    stock_scrap AS ss
                    LEFT JOIN product_product AS pp ON pp.id = ss.product_id
                    LEFT JOIN product_template AS pt ON pt.id = pp.product_tmpl_id 
                    LEFT JOIN stock_location AS sl ON sl.id = ss.scrap_location_id
                    LEFT JOIN uom_uom AS uom ON uom.id = ss.product_uom_id
                    LEFT JOIN mrp_production AS mp ON mp.id = ss.production_id
                WHERE 
                    mp.state = 'done'
                    AND ss.scrap_qty != 0
                    AND ss.company_id = %(company)s
            )
            SELECT
                row_number() OVER () as id,
                y_company_id,
                y_name,
                y_date,
                y_in_product_id,
                y_product_code,
                y_product_uom,
                y_actual_consu_qty,
                y_planned_consu_qty,
                y_variance_qty,
                y_unit_cost,
                y_actual_consu_val,
                y_planned_consu_val,
                y_variance_val,
                y_lot_id,
                y_out_product_id,
                y_mrp_name,
                y_source_document
            FROM (
                SELECT * FROM base_data
                UNION ALL
                SELECT * FROM scrap_data
            ) AS combined_data
            ORDER BY y_production_id, id
        )
            """,{'company': company})
        
  
        
    @api.model
    def consumption_report_query(self,start_date,end_date,company_clause):    
        company = self.env.company.id        
        tools.drop_view_if_exists(self._cr, 'mrp_production_consumption_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW mrp_production_consumption_report AS (
            WITH base_data AS (
                SELECT 
                    row_number() OVER (PARTITION BY mp.id ORDER BY sm.date) as id,

                    sm.id as y_stock_move_id,
                    mp.id as y_production_id,
                    mp.company_id AS y_company_id,
                    sm.name as y_name,
                    sm.date as y_date,
                    sm.product_id as y_in_product_id,
                    pp.default_code as y_product_code,
                    uom.id as y_product_uom,
                    sml.quantity as y_actual_consu_qty,
                    sm.product_uom_qty as y_planned_consu_qty,
                    (sm.product_uom_qty - sml.quantity) as y_variance_qty,
                    svl.unit_cost as y_unit_cost,
                    (svl.unit_cost * sml.quantity) as y_actual_consu_val,
                    (svl.unit_cost * sm.product_uom_qty) as y_planned_consu_val,
                    ((svl.unit_cost * sm.product_uom_qty) - (svl.unit_cost * sml.quantity)) as y_variance_val,
                    sml.lot_id as y_lot_id,
                    mp.product_id as y_out_product_id,
                    mp.name as y_mrp_name,
                    mp.origin as y_source_document
                FROM 
                    stock_move AS sm 
                    LEFT JOIN stock_move_line AS sml ON sml.move_id = sm.id
                    LEFT JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                    LEFT JOIN product_product AS pp ON pp.id = sm.product_id             
                    LEFT JOIN product_template AS pt ON pt.id = pp.product_tmpl_id 
                    LEFT JOIN stock_location AS sl ON sl.id = sm.location_dest_id
                    LEFT JOIN uom_uom AS uom ON uom.id = sm.product_uom
                    LEFT JOIN mrp_production AS mp ON mp.id = sm.raw_material_production_id
                WHERE    
                    sl.usage = 'production' AND mp.state = 'done'
                    AND (svl.unit_cost * sml.quantity != 0 OR svl.unit_cost * sm.product_uom_qty != 0)
                    AND mp.company_id {company_clause}
                    AND sm.date >= '{sd}'
                    AND sm.date <= '{ed}'
            ),
            scrap_data AS (
                SELECT
                    row_number() OVER (PARTITION BY mp.id ORDER BY ss.date_done) as id,
                    ss.id as y_scrap_id,
                    mp.id as y_production_id,
                    mp.company_id AS y_company_id,
                    ss.name as y_name,
                    ss.date_done as y_date,
                    mp.product_id as y_in_product_id,
                    pp.default_code as y_product_code,
                    uom.id as y_product_uom,
                    ss.scrap_qty as y_actual_consu_qty,
                    0 as y_planned_consu_qty,
                    0 as y_variance_qty,
                    0 as y_unit_cost,
                    0 as y_actual_consu_val,
                    0 as y_planned_consu_val,
                    0 as y_variance_val,
                    ss.lot_id as y_lot_id,
                    ss.product_id as y_out_product_id,
                    ss.origin as y_mrp_name,
                    mp.name as y_source_document
                FROM 
                    stock_scrap AS ss
                    LEFT JOIN product_product AS pp ON pp.id = ss.product_id
                    LEFT JOIN product_template AS pt ON pt.id = pp.product_tmpl_id 
                    LEFT JOIN stock_location AS sl ON sl.id = ss.scrap_location_id
                    LEFT JOIN uom_uom AS uom ON uom.id = ss.product_uom_id
                    LEFT JOIN mrp_production AS mp ON mp.id = ss.production_id
                WHERE 
                    mp.state = 'done'
                    AND ss.scrap_qty != 0
                    AND ss.date_done >= '{sd}'
                    AND ss.date_done <= '{ed}'
                    AND mp.company_id {company_clause}
                )
                SELECT
                    row_number() OVER () as id,
                    y_company_id,
                    y_name,
                    y_date,
                    y_in_product_id,
                    y_product_code,
                    y_product_uom,
                    y_actual_consu_qty,
                    y_planned_consu_qty,
                    y_variance_qty,
                    y_unit_cost,
                    y_actual_consu_val,
                    y_planned_consu_val,
                    y_variance_val,
                    y_lot_id,
                    y_out_product_id,
                    y_mrp_name,
                    y_source_document
                FROM (
                    SELECT * FROM base_data
                    UNION ALL
                    SELECT * FROM scrap_data
                ) AS combined_data
                ORDER BY y_production_id, id
            )
            """.format(company_clause=company_clause,sd=start_date, ed=end_date))
        
        list_view_id = self.env.ref('consumption_report_18.view_consumption_report_list').id
        
        return {
            'name': _("Consumption Report"),

            'type': 'ir.actions.act_window',

            'res_model': 'mrp.production.consumption.report',

            'view_mode': 'list',

            'views': [[list_view_id, 'list']],
            
            'target': 'current',


        }
        
class ConsumptionWizard(models.TransientModel):
    _name = 'consumption.report.wizard'
    _description = ""
    
    y_date_start = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    y_date_end = fields.Date(string="End Date", required=True, default=fields.Date.today)
    y_company_id = fields.Many2one('res.company', string="Company")
    
    def retrive_consumption_report(self):
        if not self.sudo().y_company_id.child_ids:
            company_clause = " = {}".format(self.y_company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id).ids
            if len(access_company_ids) == 1:
                company_clause = " = {}".format(access_company_ids[0])
            else:
                company_clause = " in {}".format(tuple(access_company_ids))
        return  self.env['mrp.production.consumption.report'].consumption_report_query(self.y_date_start, self.y_date_end,company_clause)
        
    @api.constrains('y_date_start')
    def _code_constrains(self):
        if self.y_date_start > self.y_date_end:
            raise ValidationError(_("'Start Date' Must Be Before 'End Date'"))