# -*- coding: utf-8 -*-

from . import models


def pre_init(cr):
    create_invg_bal_sum_report_view_sp(cr)

def create_invg_bal_sum_report_view_sp(cr):
	query = """
        CREATE OR REPLACE VIEW inv_bal_sum_report_view AS ( 
            SELECT distinct Row_Number() OVER() ID, result.*
            from (SELECT distinct pp.id as y_product_id,categ_id.id AS y_categ_id,
            ,group_1.id as product_group_1_id,pp.y_product_group_2 as product_group_2_id,pp.y_product_group_3 as product_group_3_id,
            svl.company_id as y_company_id,pt.uom_id as y_uom_id,pp.default_code as y_default_code,
            opening_stock.opening_stock as y_opening_stock,opening_value.opening_value as y_opening_value,
            stock_increase.stock_increase as y_stock_increase,increase_value.increase_value as y_increase_value,
            stock_decrease.stock_decrease as y_stock_decrease,decrease_value.decrease_value as y_decrease_value,
            (coalesce((opening_stock.opening_stock),0) + (coalesce((stock_increase.stock_increase),0) + (coalesce((stock_decrease.stock_decrease),0)))) as y_closing_stock,
            (coalesce((opening_value.opening_value),0) + (coalesce((increase_value.increase_value),0) + (coalesce((decrease_value.decrease_value),0)))) as y_closing_value
            from stock_valuation_layer svl
            LEFT JOIN product_product pp on svl.product_id = pp.id
            LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
            LEFT JOIN product_category categ_id ON categ_id.id = pt.categ_id
            LEFT JOIN product_group_1 y_product_group_1 ON y_product_group_1.id = pp.y_product_group_1
            
            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(quantity)as opening_stock FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date < '{}' AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)opening_stock on opening_stock.product_id = svl.product_id and opening_stock.company_id = svl.company_id

            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(value) as opening_value FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date < '{}' AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)opening_value on opening_value.product_id = svl.product_id and opening_value.company_id = svl.company_id 

            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(quantity) as stock_increase FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date >= '{}' AND svl.create_date <= '{}' AND (svl.quantity > 0) AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)stock_increase on stock_increase.product_id = svl.product_id and stock_increase.company_id = svl.company_id 

            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(value) as increase_value FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date >= '{}' AND svl.create_date <= '{}' AND ((svl.quantity > 0) or (svl.quantity = 0 and svl.value > 0)) AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)increase_value on increase_value.product_id = svl.product_id and increase_value.company_id = svl.company_id

            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(quantity) as stock_decrease FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date >= '{}' AND svl.create_date <= '{}' AND (svl.quantity < 0) AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)stock_decrease on stock_decrease.product_id = svl.product_id and stock_decrease.company_id = svl.company_id

            LEFT JOIN(SELECT svl.product_id,svl.company_id,SUM(value) as decrease_value FROM stock_valuation_layer as svl join product_product pp on pp.id = svl.product_id join product_template pt on pt.id = pp.product_tmpl_id WHERE svl.create_date >= '{}' AND svl.create_date <= '{}' AND ((svl.quantity < 0) or (svl.quantity = 0 and svl.value < 0)) AND (svl.company_id in {} )
                        AND pt.detailed_type = 'product' GROUP BY product_id,svl.company_id)decrease_value on decrease_value.product_id = svl.product_id and decrease_value.company_id = svl.company_id
                    where pt.detailed_type = 'product' and ((svl.company_id in {}) and pp.active = true) order by pp.id asc)result),"""
	cr.execute(query)