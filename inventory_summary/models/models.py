# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo import tools
from lxml import etree
import json

class InvBalSumReport(models.Model):
    _name = 'inv.bal.sum.report.view'
    _auto = False
    _description = 'Inventory Summary'

    y_product_id = fields.Many2one('product.product',string="Product")
    y_lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    y_company_id = fields.Many2one('res.company' ,string="Company")
    y_uom_id = fields.Many2one('uom.uom', store=True, string="UOM")
    y_default_code = fields.Char(store=True, string="Code")
    y_opening_stock = fields.Float('Opening(Qty)')
    y_opening_value = fields.Float('Opening(Value)')
    y_stock_increase = fields.Float('Inward(Qty)')
    y_increase_value = fields.Float('Inward(Value)')
    y_stock_decrease = fields.Float('Outward(Qty)')
    y_decrease_value = fields.Float('Outward(Value)')
    y_closing_stock = fields.Float('Closing(Qty)')
    y_closing_value = fields.Float('Closing(Value)')
    y_product_group_1_id= fields.Many2one('product.group.1',string="Product Group 1")
    y_product_group_2_id = fields.Many2one('product.group.2',string="Product Group 2")
    y_product_group_3_id = fields.Many2one('product.group.3',string="Product Group 3")
    y_categ_id = fields.Many2one('product.category',string="Product Category")

    def _select(self):
        select_str = f"""
            SELECT DISTINCT
                pp.id AS y_product_id,
                svl.lot_id AS y_lot_id,
                pt.categ_id AS y_categ_id,
                pp.y_product_group_1 AS y_product_group_1_id,
                pp.y_product_group_2 AS y_product_group_2_id,
                pp.y_product_group_3 AS y_product_group_3_id,
                svl.company_id AS y_company_id,
                pt.uom_id AS y_uom_id,
                pp.default_code AS y_default_code,
                opening_stock.opening_stock AS y_opening_stock,
                opening_value.opening_value AS y_opening_value,
                stock_increase.stock_increase AS y_stock_increase,
                increase_value.increase_value AS y_increase_value,
                stock_decrease.stock_decrease AS y_stock_decrease,
                decrease_value.decrease_value AS y_decrease_value,
                (
                    COALESCE(opening_stock.opening_stock, 0) + 
                    COALESCE(stock_increase.stock_increase, 0) + 
                    COALESCE(stock_decrease.stock_decrease, 0)
                ) AS y_closing_stock,
                (
                    COALESCE(opening_value.opening_value, 0) + 
                    COALESCE(increase_value.increase_value, 0) + 
                    COALESCE(decrease_value.decrease_value, 0)
                ) AS y_closing_value 
            """
        return select_str

    def _from(self):
        from_str = """
            FROM 
                stock_valuation_layer svl
            LEFT JOIN 
                product_product pp ON svl.product_id = pp.id
            LEFT JOIN 
                product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN 
                stock_lot lot ON lot.id = svl.lot_id
            """
        return from_str

    def _where(self):
        where_str = """
            WHERE 
                (opening_stock.opening_stock is not null or opening_value.opening_value is not null or
                stock_increase.stock_increase is not null or increase_value.increase_value is not null or
                stock_decrease.stock_decrease is not null or decrease_value.decrease_value is not null)
                AND pt.type = 'consu' 
                AND pt.is_storable
            """

        return where_str    

    @api.model
    def init(self):
        select_query = self._select()
        # from_query = self._from()
        tools.drop_view_if_exists(self._cr, 'inv_bal_sum_report_view')
        self._cr.execute("""CREATE OR REPLACE VIEW inv_bal_sum_report_view AS (
                                SELECT 
                                    ROW_NUMBER() OVER() AS ID, 
                                    result.*
                                FROM (
                                    SELECT DISTINCT
                                    pp.id AS y_product_id,
                                    svl.lot_id AS y_lot_id,
                                    pt.categ_id AS y_categ_id,
                                    pp.y_product_group_1 AS y_product_group_1_id,
                                    pp.y_product_group_2 AS y_product_group_2_id,
                                    pp.y_product_group_3 AS y_product_group_3_id,
                                    svl.company_id AS y_company_id,
                                    pt.uom_id AS y_uom_id,
                                    pp.default_code AS y_default_code,
                                    opening_stock.opening_stock AS y_opening_stock,
                                    opening_value.opening_value AS y_opening_value,
                                    stock_increase.stock_increase AS y_stock_increase,
                                    increase_value.increase_value AS y_increase_value,
                                    stock_decrease.stock_decrease AS y_stock_decrease,
                                    decrease_value.decrease_value AS y_decrease_value,
                                    (
                                        COALESCE(opening_stock.opening_stock, 0) + 
                                        COALESCE(stock_increase.stock_increase, 0) + 
                                        COALESCE(stock_decrease.stock_decrease, 0)
                                    ) AS y_closing_stock,
                                    (
                                        COALESCE(opening_value.opening_value, 0) + 
                                        COALESCE(increase_value.increase_value, 0) + 
                                        COALESCE(decrease_value.decrease_value, 0)
                                    ) AS y_closing_value 
                                
                                    FROM 
                                        stock_valuation_layer svl
                                    LEFT JOIN 
                                        product_product pp ON svl.product_id = pp.id
                                    LEFT JOIN 
                                        product_template pt ON pt.id = pp.product_tmpl_id
                                    LEFT JOIN 
                                        stock_lot lot ON lot.id = svl.lot_id
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.quantity) AS opening_stock 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) opening_stock ON opening_stock.product_id = svl.product_id AND (opening_stock.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.value) AS opening_value 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) opening_value ON opening_value.product_id = svl.product_id AND (opening_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.quantity) AS stock_increase 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) stock_increase ON stock_increase.product_id = svl.product_id AND (stock_increase.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.value) AS increase_value 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) increase_value ON increase_value.product_id = svl.product_id AND (increase_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.quantity) AS stock_decrease 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) stock_decrease ON stock_decrease.product_id = svl.product_id AND (stock_decrease.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    JOIN (
                                        SELECT 
                                            svl.lot_id AS lot_id,
                                            svl.product_id, 
                                            SUM(svl.value) AS decrease_value 
                                        FROM 
                                            stock_valuation_layer svl 
                                        GROUP BY 
                                            product_id,svl.lot_id
                                    ) decrease_value ON decrease_value.product_id = svl.product_id AND (decrease_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)
                                    ORDER BY 
                                        pp.id ASC
                                ) result
                            )
                            """)
        
    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)


        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])

            # Fields Lables
            node = doc.xpath("//field[@name='y_product_group_1_id']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2_id']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3_id']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')
            # Fields Invisible
            if view_type == 'list':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1_id"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2_id"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3_id"]'):
                        make_invisible(field)
           
        return result
        
       
class InvBalSumWiz(models.TransientModel):
    _name = 'inv.bal.sum.wiz'
    _description = 'Inventory Summary Wizard'

    y_open_date = fields.Date(string='Start Date')
    y_close_date = fields.Date(string='End Date')
    y_company_id = fields.Many2one('res.company',string='Company')
    y_product_group_id_1 = fields.Many2one('product.group.1',string='Product Group 1')
    y_product_group_id_2 = fields.Many2one('product.group.2',string='Product Group 2')
    y_product_group_id_3 = fields.Many2one('product.group.3',string='Product Group 3')
    # y_product_category_id = fields.Many2one('product.category',string="Product Category")
    y_categ_id = fields.Many2many('product.category', string="Product Category")
    
    @api.onchange('y_close_date')
    def _onchange_y_close_date(self):
        if self.y_close_date < self.y_open_date:
            raise ValidationError(_("""End Date should not be less than Start Date"""))   

    def prepare_domain(self):
        open_date = str(self.y_open_date) + ' 00:00:00'
        close_date = str(self.y_close_date) + ' 23:59:59' 
        tz_name = self._context.get('tz') or self.env.user.tz
        domain_clause = " AND svl.create_date BETWEEN (TIMESTAMP '{start_1_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{end_1_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')".format(start_1_date=open_date,end_1_date=close_date,tz_name=tz_name)    
        if len(self.y_categ_id.ids) > 1:
            domain_clause += " AND pt.categ_id IN {}".format(format(tuple(self.y_categ_id.ids)))
            
        elif len(self.y_categ_id.ids) == 1:
            domain_clause += " AND pt.categ_id = {}".format(self.y_categ_id.ids[0])    
        
        if self.y_product_group_id_1:
            domain_clause += " AND pp.y_product_group_1 = {}".format(self.y_product_group_id_1.id)
            
        if self.y_product_group_id_2:
            domain_clause += " AND pp.y_product_group_2 = {}".format(self.y_product_group_id_2.id)
            
        if self.y_product_group_id_3:
            domain_clause += " AND pp.y_product_group_3 = {} ".format(self.y_product_group_id_3.id)
            
        if not self.y_categ_id.ids and not self.y_product_group_id_1 and not self.y_product_group_id_2 and not self.y_product_group_id_3:
            domain_clause = "  " 

        return domain_clause

    def prepare_company_clause(self):
        company_clause = " AND svl.company_id = {}".format(self.y_company_id.id)
        if not self.sudo().y_company_id.child_ids:
            company_clause = " AND svl.company_id = {}".format(self.y_company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id).ids
            if len(access_company_ids) == 1:
                company_clause = " AND svl.company_id = {}".format(access_company_ids[0])
            else:
                company_clause = " AND svl.company_id in {}".format(tuple(access_company_ids))

        return company_clause

    def prepare_base_stock_query(self,open_date,close_date,company_clause):
        from_query = self.env['inv.bal.sum.report.view']._from()
        tz_name = self._context.get('tz') or self.env.user.tz
        base_query = """
                -- Opening Stock

                LEFT JOIN (
                    SELECT 
                        svl.product_id,
                        svl.lot_id AS lot_id,
                        svl.company_id,
                        SUM(svl.quantity) AS opening_stock
                    FROM 
                        stock_valuation_layer svl
                    JOIN 
                        product_product pp ON pp.id = svl.product_id
                    JOIN 
                        product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE 
                        svl.create_date < (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                        {company_clause} 
                        AND pt.type = 'consu' 
                        AND pt.is_storable
                    GROUP BY 
                        svl.product_id, svl.company_id,svl.lot_id
                ) opening_stock ON opening_stock.product_id = svl.product_id 
                    AND opening_stock.company_id = svl.company_id
                        AND (opening_stock.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                  -- Opening Value

                  LEFT JOIN (
                      SELECT 
                          svl.product_id,
                          svl.lot_id AS lot_id,
                          svl.company_id,
                          SUM(value) AS opening_value
                      FROM 
                          stock_valuation_layer svl
                      JOIN 
                          product_product pp ON pp.id = svl.product_id
                      JOIN 
                          product_template pt ON pt.id = pp.product_tmpl_id
                      WHERE 
                          svl.create_date < (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                          {company_clause} 
                          AND pt.type = 'consu' 
                          AND pt.is_storable
                      GROUP BY 
                          svl.product_id, svl.company_id,svl.lot_id
                  ) opening_value ON opening_value.product_id = svl.product_id 
                                   AND opening_value.company_id = svl.company_id
                                    AND (opening_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                  -- Stock Increase

                  LEFT JOIN (
                      SELECT 
                          svl.product_id,
                          svl.lot_id AS lot_id,
                          svl.company_id,
                          SUM(quantity) AS stock_increase
                      FROM 
                          stock_valuation_layer svl
                      JOIN 
                          product_product pp ON pp.id = svl.product_id
                      JOIN 
                          product_template pt ON pt.id = pp.product_tmpl_id
                      WHERE 
                          svl.create_date BETWEEN (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{close_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                          AND svl.quantity > 0 
                          {company_clause} 
                          AND pt.type = 'consu' 
                          AND pt.is_storable
                      GROUP BY 
                          svl.product_id, svl.company_id,svl.lot_id
                  ) stock_increase ON stock_increase.product_id = svl.product_id 
                                    AND stock_increase.company_id = svl.company_id
                                     AND (stock_increase.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                  -- Stock Increase Value

                  LEFT JOIN (
                      SELECT 
                          svl.product_id,
                          svl.lot_id AS lot_id,
                          svl.company_id,
                          SUM(value) AS increase_value
                      FROM 
                          stock_valuation_layer svl
                      JOIN 
                          product_product pp ON pp.id = svl.product_id
                      JOIN 
                          product_template pt ON pt.id = pp.product_tmpl_id
                      WHERE 
                          svl.create_date BETWEEN (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{close_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                          AND (
                              svl.quantity > 0 
                              OR (svl.quantity = 0 AND svl.value > 0)
                          ) 
                          {company_clause} 
                          AND pt.type = 'consu' 
                          AND pt.is_storable
                      GROUP BY 
                          svl.product_id, svl.company_id,svl.lot_id
                  ) increase_value ON increase_value.product_id = svl.product_id 
                                    AND increase_value.company_id = svl.company_id
                                     AND (increase_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                  -- Stock Decrease

                  LEFT JOIN (
                      SELECT 
                          svl.product_id,
                          svl.lot_id AS lot_id,
                          svl.company_id,
                          SUM(quantity) AS stock_decrease
                      FROM 
                          stock_valuation_layer svl
                      JOIN 
                          product_product pp ON pp.id = svl.product_id
                      JOIN 
                          product_template pt ON pt.id = pp.product_tmpl_id
                      WHERE 
                          svl.create_date BETWEEN (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{close_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                          AND svl.quantity < 0 
                          {company_clause} 
                          AND pt.type = 'consu' 
                          AND pt.is_storable
                      GROUP BY 
                          svl.product_id, svl.company_id,svl.lot_id
                  ) stock_decrease ON stock_decrease.product_id = svl.product_id 
                                    AND stock_decrease.company_id = svl.company_id
                                     AND (stock_decrease.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                  -- Stock Decrease Value

                  LEFT JOIN (
                      SELECT 
                          svl.product_id,
                          svl.lot_id AS lot_id,
                          svl.company_id,
                          SUM(value) AS decrease_value
                      FROM 
                          stock_valuation_layer svl
                      JOIN 
                          product_product pp ON pp.id = svl.product_id
                      JOIN 
                          product_template pt ON pt.id = pp.product_tmpl_id
                      WHERE 
                          svl.create_date BETWEEN (TIMESTAMP '{open_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{close_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                          AND (
                              svl.quantity < 0 
                              OR (svl.quantity = 0 AND svl.value < 0)
                          ) 
                          {company_clause} 
                          AND pt.type = 'consu' 
                          AND pt.is_storable
                      GROUP BY 
                          svl.product_id, svl.company_id,svl.lot_id
                  ) decrease_value ON decrease_value.product_id = svl.product_id 
                                    AND decrease_value.company_id = svl.company_id
                                     AND (decrease_value.lot_id = svl.lot_id OR svl.lot_id IS NULL)

                """.format(open_date=open_date,close_date=close_date,company_clause=company_clause,tz_name=tz_name)

        return from_query + base_query

            
    def action_open_report(self):
        open_date = str(self.y_open_date) + ' 00:00:00'
        close_date = str(self.y_close_date) + ' 23:59:59'
        company_clause = self.prepare_company_clause()
        tools.drop_view_if_exists(self._cr, 'invg_bal_sum_report_view')
        query = """CREATE OR REPLACE VIEW inv_bal_sum_report_view AS (
                                SELECT DISTINCT 
                                    ROW_NUMBER() OVER() AS ID, 
                                    result.*
                                FROM (
                                    {select_query}
                                    {from_query}
                                    {where_query}
                                    {company_clause}                
                                    {domain_clause}
                                    ORDER BY 
                                        pp.id ASC
                                ) result
                            )
                        """.format(select_query = self.env['inv.bal.sum.report.view']._select(),
                                   from_query = self.prepare_base_stock_query(open_date,close_date,company_clause),
                                   where_query = self.env['inv.bal.sum.report.view']._where(),
                                   company_clause = company_clause,
                                   domain_clause = self.prepare_domain()
                                   )

        print('\n'*10)
        print(query)
        print('\n'*10)
        self._cr.execute(query)

        tree_view_id = self.env.ref('inventory_summary.inventory_balance_summmary_tree_view').id
      

        y_open_date = self.y_open_date.strftime('%d-%m-%Y')
        y_close_date = self.y_close_date.strftime('%d-%m-%Y')

        return {
            'name': 'Inventory Summary ({} To {}) '.format(y_open_date,y_close_date),
            'view_mode': 'list,pivot',
            'views': [[tree_view_id, 'list']],
            'res_model': 'inv.bal.sum.report.view',
            'type': 'ir.actions.act_window',
            'target': 'current',}


    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)


        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])

            # Fields Lables
            node = doc.xpath("//field[@name='y_product_group_id_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_id_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_id_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_id_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_id_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_id_3"]'):
                        make_form_invisible(field)
           
        return result