# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo import tools
from datetime import datetime, timedelta
import pdb


class PurchaseRegisterReport(models.Model):
    _name = "purchase.analysis.report"
    _auto = False
    _description =  " "

    y_po_name = fields.Many2one('purchase.order','Purchase Reference', readonly=True)
    y_display_name = fields.Char(string="Vendor")
    y_picking_id = fields.Many2one('stock.picking', string="Picking Ref")
    y_date_done = fields.Date(string="Date")
    y_quantity = fields.Float('Quantity',readonly=True)
    y_price_unit = fields.Float('Unit Price',readonly=True)
    y_value = fields.Float('Value',readonly=True)
    y_avg_price=fields.Float('Avg Price',readonly=True,digits=(12, 2))
    

    # Product Details
    y_product_id = fields.Many2one('product.product', string="Product")
    y_product_cat_id=fields.Many2one('product.category',string="Product Category")
    

    def init(self):
        """Initialize the view - this is called when the model is loaded"""
        tools.drop_view_if_exists(self._cr, self._table)

        self._cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    row_number() OVER () as id,
                    svl.quantity AS y_quantity,
                    svl.product_id AS y_product_id,
                    pc.id AS y_product_cat_id,
                    svl.unit_cost AS y_price_unit,
                    svl.value AS y_value,
                    po.id as y_po_name,
                    sm.picking_id as y_picking_id,
                    (CASE
                        WHEN svl.quantity != 0.0
                        THEN (svl.value / svl.quantity)
                        ELSE 0
                    END ) AS y_avg_price,
                    sp.date_done AS y_date_done,
                    rp.name AS y_display_name
                FROM stock_valuation_layer svl
                LEFT JOIN product_product product ON product.id = svl.product_id
                LEFT JOIN product_template pt ON pt.id = product.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN stock_move sm ON sm.id = svl.stock_move_id
                LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
                LEFT JOIN purchase_order po ON po.id = pol.order_id
                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                LEFT JOIN res_partner rp ON rp.id = sp.partner_id
                WHERE sm.purchase_line_id IS NOT NULL
                AND svl.create_date >= CURRENT_DATE - INTERVAL '30 days'
            )
        """)
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        data=super(PurchaseRegisterReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        # pdb.set_trace()
        for res in data:
            if res.get('y_avg_price'):
                res['y_avg_price']=(res['y_value'])/( res['y_quantity'] if res['y_quantity'] > 0.0  else 1)
            else:
                res['y_avg_price']=1
        return data

       
  

    @api.model
    def purchase_register_query(self,start_date,end_date):
    
        tools.drop_view_if_exists(self._cr, 'purchase_analysis_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW purchase_analysis_report AS (
                 SELECT 
                row_number() OVER () as id,
                svl.quantity AS y_quantity,
                svl.product_id AS y_product_id,
                pc.id AS y_product_cat_id,
                svl.unit_cost AS y_price_unit,
                svl.value AS y_value,
				po.id as y_po_name,
                sm.picking_id as y_picking_id,
                (CASE
                        WHEN  svl.quantity != 0.0 
                         THEN (svl.value / svl.quantity)
                        ELSE svl.value
                    END ) AS y_avg_price,
                sm.picking_id AS picking_id,
                sp.date_done AS y_date_done,
                rp.name AS y_display_name

                FROM stock_valuation_layer svl
                LEFT JOIN product_product product ON product.id = svl.product_id
                LEFT JOIN product_template pt ON pt.id = product.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN stock_move sm ON sm.id = svl.stock_move_id
				LEFT JOIN purchase_order_line pol ON pol.id = sm.purchase_line_id
				LEFT JOIN purchase_order po ON po.id = pol.order_id
                LEFT JOIN stock_picking sp ON sp.id = sm.picking_id
                LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
                LEFT JOIN res_partner rp ON rp.id = sp.partner_id				
				where sm.purchase_line_id is not null and svl.create_date BETWEEN '{start_date}' AND '{end_date}'

                group by pc.id,po.id,svl.quantity,svl.product_id,svl.unit_cost,svl.value,sm.picking_id,sp.date_done,rp.name)""".format(start_date=start_date, end_date=end_date))
                
        return {
            'name': _("Purchase Analysis Report"),

            'type': 'ir.actions.act_window',

            'res_model': 'purchase.analysis.report',

            'view_mode': 'list',

            'view_type': 'list',

            'views': [[False, 'list']],

            'target': 'current'
        }