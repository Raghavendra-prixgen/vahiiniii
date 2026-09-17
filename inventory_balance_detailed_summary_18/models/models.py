# -*- coding: utf-8 -*-
from odoo import models, fields, api, _,tools
from odoo.exceptions import ValidationError
import pdb
    
class InvBalSumWiz(models.Model):
    _inherit = 'inv.bal.sum.report.view'
    _description = 'Inventory Summary'
    
    y_purchase_qty = fields.Float('Purchase(Qty)')
    y_purchase_value = fields.Float('Purchase(Value)')
    y_purchase_return_qty = fields.Float('Purchase Return(Qty)')
    y_purchase_return_value = fields.Float('Purchase Return(Value)')
    y_sale_qty = fields.Float('Sale(Qty)')
    y_sale_value = fields.Float('Sale(Value)')
    y_sale_return_qty = fields.Float('Sale Return(Qty)')
    y_sale_return_value = fields.Float('Sale Return(Value)')
    y_production_qty = fields.Float('Production(Qty)')
    y_production_value = fields.Float('Production(Value)')
    y_consumption_qty = fields.Float('Consumption(Qty)')
    y_consumption_value = fields.Float('Consumption(Value)')
    y_positive_adjustment_qty = fields.Float('Positive Adjustment(Qty)')
    y_positive_adjustment_value = fields.Float('Positive Adjustment(Value)')
    y_negative_adjustment_qty = fields.Float('Negative Adjustment(Qty)')
    y_negative_adjustment_value = fields.Float('Negative Adjustment(Value)')

    def _select(self):
      select_str = super()._select()
      select_str += f""",
                        purchase.purchase_qty AS y_purchase_qty,
                        purchase.purchase_value AS y_purchase_value,
                        purchase_return.purchase_return_qty AS y_purchase_return_qty,
                        purchase_return.purchase_return_value AS y_purchase_return_value,
                        sale.sale_qty AS y_sale_qty,
                        sale.sale_value AS y_sale_value,
                        sale_return.sale_return_qty AS y_sale_return_qty,
                        sale_return.sale_return_value AS y_sale_return_value,
                        production.production_qty AS y_production_qty,
                        production.production_value AS y_production_value,
                        consumption.consumption_qty AS y_consumption_qty,
                        consumption.consumption_value AS y_consumption_value,
                        positive_adjustment.positive_adjustment_qty AS y_positive_adjustment_qty,
                        positive_adjustment.positive_adjustment_value AS y_positive_adjustment_value,
                        negative_adjustment.negative_adjustment_qty AS y_negative_adjustment_qty,
                        negative_adjustment.negative_adjustment_value AS y_negative_adjustment_value 
                         """

      return select_str

class InvBalSumWiz(models.TransientModel):
    _inherit = 'inv.bal.sum.wiz'
    _description = 'Inventory Summary Wizard'

    def prepare_base_stock_query(self,open_date,close_date,company_clause):
      from_query = super().prepare_base_stock_query(open_date,close_date,company_clause)
      from_query += """LEFT JOIN (
                                          SELECT 
                                              svl.product_id AS product_id,
                                              svl.lot_id AS lot_id,
                                              SUM(svl.quantity) AS purchase_qty,
                                              SUM(svl.value) AS purchase_value
                                          FROM stock_valuation_layer AS svl
                                          JOIN product_product pp ON pp.id = svl.product_id
                                          JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                          JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                          JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                          JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                          JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                          WHERE svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu'
                                            AND pt.is_storable
                                            AND source_sl.usage = 'supplier'
                                            AND dest_sl.usage = 'internal'
                                          GROUP BY 
                                            svl.product_id,svl.lot_id
                                      ) AS purchase ON purchase.product_id = svl.product_id AND (purchase.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                      
                                      LEFT JOIN (
                                          SELECT 
                                              svl.product_id AS product_id,
                                              svl.lot_id AS lot_id,
                                              SUM(svl.quantity) AS purchase_return_qty,
                                              SUM(svl.value) AS purchase_return_value
                                          FROM stock_valuation_layer AS svl
                                          JOIN product_product pp ON pp.id = svl.product_id
                                          JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                          JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                          JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                          JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                          JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                          WHERE svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu'
                                            AND pt.is_storable
                                            AND source_sl.usage = 'internal'
                                            AND dest_sl.usage = 'supplier'
                                          GROUP BY 
                                            svl.product_id,svl.lot_id
                                      ) AS purchase_return ON purchase_return.product_id = svl.product_id AND (purchase_return.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                      
                                      LEFT JOIN (
                                          SELECT 
                                              svl.product_id,
                                              svl.lot_id AS lot_id,
                                              SUM(svl.quantity) AS sale_qty,
                                              SUM(svl.value) AS sale_value
                                          FROM 
                                              stock_valuation_layer AS svl
                                              JOIN product_product pp ON pp.id = svl.product_id
                                              JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                              JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                              JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                              JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                              JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                          WHERE 
                                              svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                              {company_clause}
                                              AND pt.type = 'consu' 
                                              AND pt.is_storable
                                              AND source_sl.usage = 'internal'
                                              AND dest_sl.usage = 'customer'
                                          GROUP BY 
                                              svl.product_id,svl.lot_id
                                      ) AS sale ON sale.product_id = svl.product_id AND (sale.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                      
                                      LEFT JOIN (
                                          SELECT 
                                              svl.product_id,
                                              svl.lot_id AS lot_id,
                                              SUM(svl.quantity) AS sale_return_qty,
                                              SUM(svl.value) AS sale_return_value
                                          FROM 
                                              stock_valuation_layer AS svl
                                              JOIN product_product pp ON pp.id = svl.product_id
                                              JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                              JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                              JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                              JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                              JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                          WHERE 
                                              svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                              {company_clause}
                                              AND pt.type = 'consu' 
                                              AND pt.is_storable
                                              AND source_sl.usage = 'customer'
                                              AND dest_sl.usage = 'internal'
                                          GROUP BY 
                                              svl.product_id,svl.lot_id
                                      ) AS sale_return ON sale_return.product_id = svl.product_id AND (sale_return.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                      LEFT JOIN (
                                        SELECT 
                                            svl.product_id,
                                            svl.lot_id AS lot_id,
                                            SUM(svl.quantity) AS production_qty,
                                            SUM(svl.value) AS production_value
                                        FROM 
                                            stock_valuation_layer AS svl
                                            JOIN product_product pp ON pp.id = svl.product_id
                                            JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                            JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                            JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                            JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                            JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                        WHERE 
                                            svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu' 
                                            AND pt.is_storable 
                                            AND source_sl.usage = 'production' 
                                            AND dest_sl.usage = 'internal'
                                        GROUP BY 
                                            svl.product_id,svl.lot_id
                                    ) AS production ON production.product_id = svl.product_id AND (production.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                    LEFT JOIN (
                                        SELECT 
                                            svl.product_id,
                                            svl.lot_id AS lot_id,
                                            SUM(svl.quantity) AS consumption_qty,
                                            SUM(svl.value) AS consumption_value
                                        FROM 
                                            stock_valuation_layer AS svl
                                            JOIN product_product pp ON pp.id = svl.product_id
                                            JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                            JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                            JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                            JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                            JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                        WHERE 
                                            svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu' 
                                            AND pt.is_storable 
                                            AND source_sl.usage = 'internal' 
                                            AND dest_sl.usage = 'production'
                                        GROUP BY 
                                            svl.product_id,svl.lot_id
                                    ) AS consumption ON consumption.product_id = svl.product_id AND (consumption.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                    LEFT JOIN (
                                        SELECT 
                                            svl.product_id,
                                            svl.lot_id AS lot_id,
                                            SUM(svl.quantity) AS positive_adjustment_qty,
                                            SUM(svl.value) AS positive_adjustment_value
                                        FROM 
                                            stock_valuation_layer AS svl
                                            JOIN product_product pp ON pp.id = svl.product_id
                                            JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                            JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                            JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                            JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                            JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                        WHERE 
                                            svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu' 
                                            AND pt.is_storable 
                                            AND source_sl.usage = 'inventory' 
                                            AND dest_sl.usage = 'internal'
                                        GROUP BY 
                                            svl.product_id,svl.lot_id
                                    ) AS positive_adjustment ON positive_adjustment.product_id = svl.product_id AND (positive_adjustment.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                                    
                                    LEFT JOIN (
                                        SELECT 
                                            svl.product_id,
                                            svl.lot_id AS lot_id,
                                            SUM(svl.quantity) AS negative_adjustment_qty,
                                            SUM(svl.value) AS negative_adjustment_value
                                        FROM 
                                            stock_valuation_layer AS svl
                                            JOIN product_product pp ON pp.id = svl.product_id
                                            JOIN product_template pt ON pt.id = pp.product_tmpl_id
                                            JOIN stock_move source_sm ON source_sm.id = svl.stock_move_id
                                            JOIN stock_location source_sl ON source_sl.id = source_sm.location_id
                                            JOIN stock_move dest_sm ON dest_sm.id = svl.stock_move_id
                                            JOIN stock_location dest_sl ON dest_sl.id = dest_sm.location_dest_id
                                        WHERE 
                                            svl.create_date BETWEEN ('{open_date}' AT TIME ZONE 'UTC') AND ('{close_date}' AT TIME ZONE 'UTC')
                                            {company_clause}
                                            AND pt.type = 'consu' 
                                            AND pt.is_storable 
                                            AND source_sl.usage = 'internal' 
                                            AND dest_sl.usage = 'inventory'
                                        GROUP BY 
                                            svl.product_id,svl.lot_id
                                    ) AS negative_adjustment ON negative_adjustment.product_id = svl.product_id AND (negative_adjustment.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                     """.format(open_date=open_date,close_date=close_date,company_clause=company_clause)

      return from_query
    
    def action_open_detailed_report(self):
        open_date = str(self.y_open_date) + ' 00:00:00'
        close_date = str(self.y_close_date) + ' 23:59:59'    
        company_clause = self.prepare_company_clause()
        tools.drop_view_if_exists(self._cr, 'inv_bal_sum_report_view')
        query = """CREATE OR REPLACE VIEW inv_bal_sum_report_view AS ( 
                              SELECT distinct Row_Number() OVER() ID, result.*
                                FROM (
                                      {select_query}
                                      {from_query}
                                      
                                      {where_query}
                                      {company_clause}
                                      {domain_clause}
                                      ORDER BY 
                                        pp.id ASC
                          )result)
                          """.format(select_query = self.env['inv.bal.sum.report.view']._select(),
                              from_query = self.prepare_base_stock_query(open_date,close_date,company_clause),
                              where_query = self.env['inv.bal.sum.report.view']._where(),
                              company_clause = company_clause,
                              domain_clause = self.prepare_domain(),
                              open_date=open_date,
                              close_date=close_date,
                              )

        
        self._cr.execute(query)


        tree_view_id = self.env.ref('inventory_balance_detailed_summary_18.tree_view_inventory_balance_detailed_summmary').id
        y_open_date = self.y_open_date.strftime('%d-%m-%Y')
        y_close_date = self.y_close_date.strftime('%d-%m-%Y')
        return {
            'name': 'Inventory Detailed Summary ({} To {})'.format(y_open_date,y_close_date),
            'view_mode': 'list,pivot',
            'views': [[tree_view_id, 'list']],
            'res_model': 'inv.bal.sum.report.view',
            'type': 'ir.actions.act_window',
            'target': 'current',
            }


