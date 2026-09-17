from odoo import fields, models, api,_,tools
from operator import itemgetter
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from lxml import etree
from lxml import etree
from datetime import datetime, timedelta,date
from xlwt import easyxf
import xlwt
import io
import base64
import math
import pdb
import json
import xlsxwriter
import pytz

class InventoryAgingValueWizard(models.TransientModel):
    _name = "inventory.aging.value.wizard"
    _description = ""

    date_start = fields.Date(string="Aging at Date", required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', 'Company')
    period_1_from = fields.Integer(string="Period 1 From")
    period_2_from = fields.Integer(string="Period 2 From",default=31)
    period_3_from = fields.Integer(string="Period 3 From",default=61)
    period_4_from = fields.Integer(string="Period 4 From",default=91)
    period_5_from = fields.Integer(string="Period 5 From",default=121)
    period_6_from = fields.Integer(string="Period 6 From",default=151)
    period_7_from = fields.Integer(string="Period 7 From",default=181)
    period_8_from = fields.Integer(string="Period 8 From",default=211)

    period_1_to = fields.Integer(string="Period 1  To",default=30)
    period_2_to = fields.Integer(string="Period 2 To",default=60)
    period_3_to = fields.Integer(string="Period 3 To",default=90)
    period_4_to = fields.Integer(string="Period 4 To",default=120)
    period_5_to = fields.Integer(string="Period 5 To",default=150)
    period_6_to = fields.Integer(string="Period 6 To",default=180)
    period_7_to = fields.Integer(string="Period 7 To",default=210)
    period_8_to = fields.Char(string="Older",default="Older")

    @api.onchange('period_1_to')
    def _onchange_period_1_to(self):
        for wizard in self:
            if wizard.period_1_to > 0:
                wizard.period_2_from = wizard.period_1_to + 1

    @api.onchange('period_2_to')
    def _onchange_period_2_to(self):
        for wizard in self:
            if wizard.period_2_to > 0:
                wizard.period_3_from = wizard.period_2_to + 1

    @api.onchange('period_3_to')
    def _onchange_period_3_to(self):
        for wizard in self:
            if wizard.period_3_to > 0:
                wizard.period_4_from = wizard.period_3_to + 1

    @api.onchange('period_4_to')
    def _onchange_period_4_to(self):
        for wizard in self:
            if wizard.period_4_to > 0:
                wizard.period_5_from = wizard.period_4_to + 1

    @api.onchange('period_5_to')
    def _onchange_period_5_to(self):
        for wizard in self:
            if wizard.period_5_to > 0:
                wizard.period_6_from = wizard.period_5_to + 1

    @api.onchange('period_6_to')
    def _onchange_period_6_to(self):
        for wizard in self:
            if wizard.period_6_to > 0:
                wizard.period_7_from = wizard.period_6_to + 1
            
    @api.onchange('period_7_to')
    def _onchange_period_7_to(self):
        for wizard in self:
            if wizard.period_7_to > 0:
                wizard.period_8_from = wizard.period_7_to + 1
            

    @api.constrains('period_1_from','period_1_to')
    def _check_period_1_to(self):
        for wizard in self:
            if wizard.period_1_from >= wizard.period_1_to:
                raise ValidationError("Period 1 To should be greater than Period 1 From")

    @api.constrains('period_2_from','period_2_to')
    def _check_period_2_to(self):
        for wizard in self:
            if wizard.period_2_from >= wizard.period_2_to:
                raise ValidationError("Period 2 To should be greater than Period 2 From")

    @api.constrains('period_3_from','period_3_to')
    def _check_period_3_to(self):
        for wizard in self:
            if wizard.period_3_from >= wizard.period_3_to:
                raise ValidationError("Period 3 To should be greater than Period 3 From")

    @api.constrains('period_4_from','period_4_to')
    def _check_period_4_to(self):
        for wizard in self:
            if wizard.period_4_from >= wizard.period_4_to:
                raise ValidationError("Period 4 To should be greater than Period 4 From")

    @api.constrains('period_5_from','period_5_to')
    def _check_period_5_to(self):
        for wizard in self:
            if wizard.period_5_from >= wizard.period_5_to:
                raise ValidationError("Period 5 To should be greater than Period 5 From")

    @api.constrains('period_6_from','period_6_to')
    def _check_period_6_to(self):
        for wizard in self:
            if wizard.period_6_from >= wizard.period_6_to:
                raise ValidationError("Period 6 To should be greater than Period 6 From")

    @api.constrains('period_7_from','period_7_to')
    def _check_period_7_to(self):
        for wizard in self:
            if wizard.period_7_from >= wizard.period_7_to:
                raise ValidationError("Period 7 To should be greater than Period 7 From")

    
    # def dict_to_insert_query(self,table_name, data):
    #     def format_value(value):
    #         if isinstance(value, str):
    #             return f"'{value}'"
    #         elif isinstance(value, (int, float)):
    #             return str(value)
    #         elif isinstance(value, bool):
    #             return 'TRUE' if value else 'FALSE'
    #         elif value is None:
    #             return 'NULL'
    #         elif isinstance(value, list):
    #             return f"'{{{','.join(map(str, value))}}}'"  # Converts Python list to PostgreSQL array
    #         elif isinstance(value, datetime):
    #             return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    #         elif isinstance(value, date):
    #             return f"'{value.strftime('%Y-%m-%d')}'"
    #         else:
    #             raise ValueError(f"Unsupported data type: {type(value)}")

    #     # Extract columns and values
    #     columns = ', '.join(data.keys())
    #     values = ', '.join([format_value(v) for v in data.values()])
        
    #     # Construct the query
    #     company_id = data.get('company_id')
    #     product_id = data.get('product_id')
    #     lot_id = data.get('lot_id')
    #     if lot_id:
    #         sub_query = f"SELECT * FROM {table_name} WHERE product_id = {product_id} and lot_id = {lot_id} and company_id = {company_id}"
    #     else:
    #         sub_query = f"SELECT * FROM {table_name} WHERE product_id = {product_id} and lot_id = null and company_id = {company_id}"
    #     self._cr.execute(sub_query)
    #     exist_ids = self._cr.dictfetchall()
    #     if not exist_ids:
    #         query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
    #         return query
    #     else:
    #         return False


    def dict_to_insert_query(self, table_name, data):
        def format_value(value):
            if isinstance(value, str):
                # Escape single quotes within the string
                escaped_value = value.replace("'", "''")
                return f"'{escaped_value}'"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, bool):
                return 'TRUE' if value else 'FALSE'
            elif value is None:
                return 'NULL'
            elif isinstance(value, list):
                formatted_list_items = [format_value(item) for item in value] # Recursively format items
                return f"ARRAY[{','.join(formatted_list_items)}]" # Standard SQL array constructor
            elif isinstance(value, datetime):
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif isinstance(value, date):
                return f"'{value.strftime('%Y-%m-%d')}'"
            else:
                raise ValueError(f"Unsupported data type for SQL formatting: {type(value)} for value: {value}")

        # Extract columns and values
        columns = ', '.join(data.keys())
        values = ', '.join([format_value(v) for v in data.values()])

        # Extract columns and values
        columns = ', '.join([f'"{k}"' for k in data.keys()]) # Quote column names for safety
        
        company_id = data.get('company_id')
        product_id = data.get('product_id')
        lot_id = data.get('lot_id')

        if lot_id is not None:
            sub_query = f"SELECT * FROM \"{table_name}\" WHERE product_id = %s AND lot_id = %s AND company_id = %s"
            sub_query_params = (product_id, lot_id, company_id)
        else:
            sub_query = f"SELECT * FROM \"{table_name}\" WHERE product_id = %s AND lot_id IS NULL AND company_id = %s"
            sub_query_params = (product_id, company_id)
        
        self._cr.execute(sub_query, sub_query_params) # Use parameters
        exist_ids = self._cr.dictfetchall()
        
        if not exist_ids:
            formatted_values_str = ', '.join([format_value(v) for v in data.values()])
            query = f"INSERT INTO \"{table_name}\" ({columns}) VALUES ({formatted_values_str})"
            print("{}".format(query))
            return query 
        else:
            return False
            
    def inventory_aging_qty_value_report_view_select(self):
        query = """
                    qvr.product_id AS product_id,
                    qvr.product_code AS product_code,
                    qvr.product_name AS product_name,
                    row_number() OVER () AS id,
                    qvr.product_category_id AS product_category_id,
                    qvr.product_uom_id AS product_uom_id,
                    qvr.lot_id AS lot_id,
                    qvr.lot_create_date AS lot_create_date,
                    qvr.quantity AS quantity,
                    qvr.cost AS cost,
                    qvr.value AS value,
                    qvr.period_1_qty AS period_1_qty,
                    qvr.period_1_value AS period_1_value,
                    qvr.period_2_qty AS period_2_qty,
                    qvr.period_2_value AS period_2_value,
                    qvr.period_3_qty AS period_3_qty,
                    qvr.period_3_value AS period_3_value,
                    qvr.period_4_qty AS period_4_qty,
                    qvr.period_4_value AS period_4_value,
                    qvr.period_5_qty AS period_5_qty,
                    qvr.period_5_value AS period_5_value,
                    qvr.period_6_qty AS period_6_qty,
                    qvr.period_6_value AS period_6_value,
                    qvr.period_7_qty AS period_7_qty,
                    qvr.period_7_value AS period_7_value,
                    qvr.older_qty AS older_qty,
                    qvr.older_value AS older_value,
                    qvr.company_id AS company_id
                 """

        return query

    def check_parent_lot(self,lot_id):
        return lot_id

    def action_feach_first_positive_record(self,older_date,svl_product_id,lot_clause,svl_company_id):
        tz_name = self._context.get('tz') or self.env.user.tz
        return """  SELECT 
                        svl.create_date AS date
                    FROM 
                        stock_valuation_layer svl
                    WHERE 
                        svl.create_date < (TIMESTAMP '{older_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                        AND svl.quantity > 0
                        AND svl.product_id = {svl_product_id}
                        AND svl.company_id = {svl_company_id}
                        {lot_clause}
                    ORDER BY svl.create_date asc
                    LIMIT 1
                """.format(older_date=older_date,svl_product_id=svl_product_id,lot_clause=lot_clause,svl_company_id=svl_company_id,tz_name=tz_name)

    # def action_create_older_periods(self,older_date,svl_product_id,svl_lot_id,svl_company_id):
    #     return """  SELECT 
    #                     SUM(svl.quantity) AS quantity,
    #                 FROM 
    #                     stock_valuation_layer svl
    #                 LEFT JOIN 
    #                     stock_move move ON move.id = svl.stock_move_id
    #                 LEFT JOIN 
    #                     stock_location src_loc ON src_loc.id = move.location_id
    #                 LEFT JOIN 
    #                     stock_location src_dest ON src_dest.id = move.location_dest_id
    #                 WHERE 
    #                     svl.create_date < '{older_date}'
    #                     AND src_loc.usage NOT IN ('internal', 'transit')
    #                     AND src_dest.usage IN ('internal', 'transit','production')
    #                     AND svl.quantity > 0
    #                     AND svl.product_id = {svl_product_id}
    #                     AND (svl.lot_id = {svl_lot_id} OR svl.lot_id IS NULL)
    #                     AND svl.company_id = {svl_company_id}
    #             """.format(older_date=older_date,svl_product_id=svl_product_id,svl_lot_id=svl_lot_id,svl_company_id=svl_company_id)


    def action_create_periods(self,start_1_date,end_1_date,svl_product_id,lot_clause,svl_company_id):
        tz_name = self._context.get('tz') or self.env.user.tz
        return """  SELECT 
                        SUM(svl.quantity) AS quantity
                    FROM 
                        stock_valuation_layer svl
                    LEFT JOIN 
                        stock_move move ON move.id = svl.stock_move_id
                    LEFT JOIN 
                        stock_location src_loc ON src_loc.id = move.location_id
                    LEFT JOIN 
                        stock_location src_dest ON src_dest.id = move.location_dest_id
                    WHERE 
                        svl.create_date BETWEEN (TIMESTAMP '{start_1_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{end_1_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                        AND src_loc.usage NOT IN ('internal', 'transit')
                        AND src_dest.usage IN ('internal', 'transit','production')
                        AND svl.quantity > 0
                        AND svl.product_id = {svl_product_id}
                        {lot_clause}
                        AND svl.company_id = {svl_company_id}
                """.format(start_1_date=start_1_date,end_1_date=end_1_date,svl_product_id=svl_product_id,lot_clause=lot_clause,svl_company_id=svl_company_id,tz_name=tz_name)

    def action_select_query(self):
        return """  template.default_code AS product_code,
                    template.name->>'en_US' AS product_name,
                    svl.lot_id AS lot_id,
                    lot.create_date AS lot_create_date,
                    svl.product_id AS product_id,
                    svl.categ_id AS product_category_id,
                    template.uom_id AS product_uom_id,
                    svl.company_id as company_id,
                    SUM(svl.quantity) AS quantity,
                    SUM(svl.value) AS value,
                    CASE WHEN SUM(svl.quantity) > 0 THEN SUM(svl.value)/SUM(svl.quantity)
                    ELSE 0 END AS cost
                    """
    def action_group_by_query(self):
        return """svl.product_id, svl.lot_id,svl.company_id,lot.create_date,svl.categ_id,template.uom_id,template.default_code,template.name """

    def action_create_opening_records(self,date_to,company_clase):
        select_clase = self.action_select_query()
        group_by_query = self.action_group_by_query()
        tz_name = self._context.get('tz') or self.env.user.tz
        return """
                SELECT 
                    {select_clase}
                FROM 
                    stock_valuation_layer svl
                LEFT JOIN
                    stock_lot lot ON lot.id = svl.lot_id
                LEFT JOIN 
                    product_product product ON product.id = svl.product_id
                LEFT JOIN 
                    product_template template ON template.id = product.product_tmpl_id
                WHERE svl.create_date <= (TIMESTAMP '{date_to}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                    AND template.type = 'consu' 
                    AND template.is_storable
                {company_clase}
                GROUP BY 
                    {group_by_query}
                """.format(date_to=date_to,company_clase=company_clase,select_clase=select_clase,group_by_query=group_by_query,tz_name=tz_name)

    
    # Calling report method
    def retrieve_aging_report(self):
        open_date = self.date_start
        if not self.sudo().company_id.child_ids:
            company_clase = " AND svl.company_id = {}".format(self.company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.company_id) + self.company_id).ids
            if len(access_company_ids) == 1:
                company_clase = " AND svl.company_id = {}".format(access_company_ids[0])
            else:
                company_clase = " AND svl.company_id in {}".format(tuple(access_company_ids))

        period_2_from = self.period_2_from
        period_3_from = self.period_3_from
        period_4_from = self.period_4_from
        period_5_from = self.period_5_from
        period_6_from = self.period_6_from
        period_7_from = self.period_7_from
        period_8_from = self.period_8_from
        period_1_to = self.period_1_to
        period_2_to = self.period_2_to
        period_3_to = self.period_3_to
        period_4_to = self.period_4_to
        period_5_to = self.period_5_to
        period_6_to = self.period_6_to
        period_7_to = self.period_7_to
        period_8_to = self.period_8_to

        aging_days_list = [(0,period_1_to),
                           (period_1_to + 1, period_2_to),
                           (period_2_to + 1, period_3_to),
                           (period_3_to + 1, period_4_to),
                           (period_4_to + 1, period_5_to),
                           (period_5_to + 1, period_6_to),
                           (period_6_to + 1, period_7_to),
                        ]
        quantity_aging_periods = []
        value_aging_periods = []
        for period_val in aging_days_list:
            quantity_aging_periods.append('{}-{} Qty'.format(period_val[0],period_val[1]))
            value_aging_periods.append('{}-{} Value'.format(period_val[0],period_val[1]))


        quantity_aging_periods.append('{}-Older Qty'.format(period_7_to + 1))
        value_aging_periods.append('{}-Older Value'.format(period_7_to + 1))
    
        context = dict(self._context)
        context.update({'quantity_aging_periods':quantity_aging_periods,'value_aging_periods':value_aging_periods})
        self.env.user.write({'y_inventory_aging_domain': quantity_aging_periods})
        self.env.user.write({'y_inventory_value_aging_domain': value_aging_periods})
        date_to = str(open_date) + ' 23:59:59'
        
        start_1_date = open_date - relativedelta(days=period_1_to)
        end_1_date = open_date

        start_2_date = start_1_date - relativedelta(days=(period_2_to - period_2_from) + 1)
        end_2_date = start_1_date - relativedelta(days=1)

        start_3_date = start_2_date - relativedelta(days=(period_3_to - period_3_from) + 1)
        end_3_date = start_2_date - relativedelta(days=1)

        start_4_date = start_3_date - relativedelta(days=(period_4_to - period_4_from) + 1) 
        end_4_date = start_3_date - relativedelta(days=1)

        start_5_date = start_4_date - relativedelta(days=(period_5_to - period_5_from) + 1)
        end_5_date = start_4_date - relativedelta(days=1)

        start_6_date = start_5_date - relativedelta(days=(period_6_to - period_6_from) + 1)
        end_6_date = start_5_date - relativedelta(days=1)

        start_7_date = start_6_date - relativedelta(days=(period_7_to - period_7_from) + 1)
        end_7_date = start_6_date - relativedelta(days=1)

        older_date = start_7_date

        start_1_date = str(start_1_date) + ' 00:00:00'
        end_1_date = str(end_1_date) + ' 23:59:59'
        start_2_date = str(start_2_date) + ' 00:00:00'
        end_2_date = str(end_2_date) + ' 23:59:59'
        start_3_date = str(start_3_date) + ' 00:00:00'
        end_3_date = str(end_3_date) + ' 23:59:59'
        start_4_date = str(start_4_date) + ' 00:00:00'
        end_4_date = str(end_4_date) + ' 23:59:59'
        start_5_date = str(start_5_date) + ' 00:00:00'
        end_5_date = str(end_5_date) + ' 23:59:59'
        start_6_date = str(start_6_date) + ' 00:00:00'
        end_6_date = str(end_6_date) + ' 23:59:59'
        start_7_date = str(start_7_date) + ' 00:00:00'
        end_7_date = str(end_7_date) + ' 23:59:59'
        older_date = start_7_date

        date_periods = [(start_1_date,end_1_date,1),
                        (start_2_date,end_2_date,2),
                        (start_3_date,end_3_date,3),
                        (start_4_date,end_4_date,4),
                        (start_5_date,end_5_date,5),
                        (start_6_date,end_6_date,6),
                        (start_7_date,end_7_date,7)]


        self._cr.execute("""DELETE FROM inventory_aging_qty_value_report""")
        
        query = self.action_create_opening_records(date_to,company_clase)
        self._cr.execute(query)
        opening_valuation_data = self._cr.dictfetchall()
        for data in opening_valuation_data:
            if data.get('quantity') != 0 or data.get('value') != 0:
                query = self.dict_to_insert_query('inventory_aging_qty_value_report',data)
                if query:
                    self._cr.execute(query)

        for aging_data in self.env['inventory.aging.qty.value.report'].sudo().search([]):
            product_id = aging_data.product_id.id
            lot_id = aging_data.lot_id.id
            company_id = aging_data.company_id.id
            quantity = aging_data.quantity
            value = aging_data.value
            cost = aging_data.cost
            if lot_id:
                lot_clause = """ AND (svl.lot_id = {svl_lot_id} OR svl.lot_id IS NULL) """.format(svl_lot_id=lot_id)
            else:
                lot_clause = """ AND svl.lot_id IS NULL""".format(svl_lot_id=lot_id)
            for period_data in date_periods:
                period_query = self.action_create_periods(period_data[0],period_data[1],product_id,lot_clause,company_id)
                self._cr.execute(period_query)
                period_results = self._cr.dictfetchall()
                for period_result in period_results:
                    period_quantity = period_result.get('quantity')
                    if period_quantity:
                        self._cr.execute("""UPDATE inventory_aging_qty_value_report SET {}={} WHERE id = {}""".format('period_{}_qty'.format(period_data[-1]),period_quantity,aging_data.id))
            
            self.env.cr.commit()
            valuation_date = False
            valuation_date_record = self.action_feach_first_positive_record(date_to,product_id,lot_clause,company_id)
            self._cr.execute(valuation_date_record)
            valuation_record = self._cr.dictfetchall()
            if valuation_record:
                for svl in valuation_record:
                    valuation_date = svl.get('date')

            # check_lot_aging = False
            # if valuation_date:
            #     if aging_data.lot_id:
            #         if aging_data.lot_id.create_date.date() != valuation_date.date():
            #             check_lot_aging = True

            
            # if not check_lot_aging:
            #     period_1_qty = aging_data.period_1_qty
            #     period_2_qty = aging_data.period_2_qty
            #     period_3_qty = aging_data.period_3_qty
            #     period_4_qty = aging_data.period_4_qty
            #     period_5_qty = aging_data.period_5_qty
            #     period_6_qty = aging_data.period_6_qty
            #     period_7_qty = aging_data.period_7_qty
            #     if period_1_qty >= quantity:
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_1_qty={},
            #                                     period_2_qty=0,
            #                                     period_3_qty=0,
            #                                     period_4_qty=0,
            #                                     period_5_qty=0,
            #                                     period_6_qty=0,
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity,aging_data.id))
                    
            #     elif (period_1_qty + period_2_qty) >= quantity:
            #         qty = (quantity - period_1_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_2_qty={},
            #                                     period_3_qty=0,
            #                                     period_4_qty=0,
            #                                     period_5_qty=0,
            #                                     period_6_qty=0,
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(qty,aging_data.id))
            #     elif (period_1_qty + period_2_qty + period_3_qty) >= quantity:
            #         quantity_3 = quantity - (period_1_qty + period_2_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_3_qty={},
            #                                     period_4_qty=0,
            #                                     period_5_qty=0,
            #                                     period_6_qty=0,
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity_3,aging_data.id))
            #     elif (period_1_qty + period_2_qty + period_3_qty + period_4_qty) >= quantity:
            #         quantity_4 = quantity - (period_1_qty + period_2_qty + period_3_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_4_qty={},
            #                                     period_5_qty=0,
            #                                     period_6_qty=0,
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity_4,aging_data.id))
            #     elif (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty) >= quantity:
            #         quantity_5 = quantity - (period_1_qty + period_2_qty + period_3_qty + period_4_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_5_qty={},
            #                                     period_6_qty=0,
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity_5,aging_data.id))
            #     elif (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty + period_6_qty) >= quantity:
            #         quantity_6 = quantity - (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_6_qty={},
            #                                     period_7_qty=0,
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity_6,aging_data.id))
            #     elif (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty + period_6_qty + period_7_qty) >= quantity:
            #         quantity_7 = quantity - (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty + period_6_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_7_qty={},
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(quantity_7,aging_data.id))

            #     else:
            #         older_quantity = quantity - (period_1_qty + period_2_qty + period_3_qty + period_4_qty + period_5_qty + period_6_qty + period_7_qty)
            #         self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_7_qty={},
            #                                     older_qty=0
            #                                 WHERE id = {}""".format(older_quantity,aging_data.id))

            #     self.env.cr.commit()

            #     period_1_qty = aging_data.period_1_qty * cost
            #     period_2_qty = aging_data.period_2_qty * cost
            #     period_3_qty = aging_data.period_3_qty * cost
            #     period_4_qty = aging_data.period_4_qty * cost
            #     period_5_qty = aging_data.period_5_qty * cost
            #     period_6_qty = aging_data.period_6_qty * cost
            #     period_7_qty = aging_data.period_7_qty * cost
            #     older_qty = aging_data.older_qty * cost
            #     self._cr.execute("""UPDATE 
            #                                 inventory_aging_qty_value_report 
            #                                 SET 
            #                                     period_1_value={},
            #                                     period_2_value={},
            #                                     period_3_value={},
            #                                     period_4_value={},
            #                                     period_5_value={},
            #                                     period_6_value={},
            #                                     period_7_value={},
            #                                     older_value={}
            #                                 WHERE id = {}""".format(period_1_qty,
            #                                                         period_2_qty,
            #                                                         period_3_qty,
            #                                                         period_4_qty,
            #                                                         period_5_qty,
            #                                                         period_6_qty,
            #                                                         period_7_qty,
            #                                                         older_qty,
            #                                                         aging_data.id))

            # else:
            lot_create_date = aging_data.lot_id.create_date.date()
            lot_obj = aging_data.lot_id
            if lot_obj:
                lot_id = self.sudo().check_parent_lot(lot_obj)
                if lot_create_date != lot_id.create_date.date():
                    lot_create_date = lot_id.create_date.date()

            # tz_name = aging_data._context.get('tz') or aging_data.env.user.tz
            # timezone = pytz.timezone(tz_name)
            # now = datetime.now(tz = timezone)
            # current_date = now.date()
            # aging_days = (valuation_date.date() - lot_create_date).days
            aging_days = (self.date_start - lot_create_date).days
            matching_range = next((r for r in aging_days_list if r[0] <= aging_days <= r[1]), None)
            if matching_range:
                index = aging_days_list.index(matching_range)
                if index == 0:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty = {},
                                            period_1_value = {},
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 1:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty = {},
                                            period_2_value = {},
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 2:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty = {},
                                            period_3_value = {},
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 3:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty = {},
                                            period_4_value = {},
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 4:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty = {},
                                            period_5_value = {},
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 5:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty = {},
                                            period_6_value = {},
                                            period_7_qty=0,
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                elif index == 6:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty = {},
                                            period_7_value = {},
                                            older_qty=0
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

                else:
                    self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty = {},
                                            older_value = {}
                                        WHERE id = {}""".format(quantity,value,aging_data.id))

            else:
                self._cr.execute("""UPDATE 
                                        inventory_aging_qty_value_report 
                                        SET 
                                            period_1_qty=0,
                                            period_2_qty=0,
                                            period_3_qty=0,
                                            period_4_qty=0,
                                            period_5_qty=0,
                                            period_6_qty=0,
                                            period_7_qty=0,
                                            older_qty = {},
                                            older_value = {}
                                        WHERE id = {}""".format(quantity,value,aging_data.id))


    def button_view_report(self):
        self.retrieve_aging_report()
        
        # Origial Table
        # view_id = self.env.ref("inventory_aging_report_flexible_dates.inventory_inventory_aging_value_report_tree_view").id,
        # action = {
        #     'name': _("Inventory Ageing Report As On {}".format(self.date_start)),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'inventory.aging.qty.value.report',
        #     'view_mode': 'list',
        #     'view_type': 'tree',
        #     'view_id': view_id,
        #     'views': [[view_id, 'list']],
        #     # 'domain':['|',('quantity','!=',0),('value','!=',0),('product_id.is_storable', '=', True)],
        #     'target': 'current',
        #     # 'context': context,
        #     }

        # Return Query
        tools.drop_view_if_exists(self._cr, 'inventory_aging_qty_value_report_view')
        select_fields = self.inventory_aging_qty_value_report_view_select()
        query = self._cr.execute("""
            CREATE OR REPLACE VIEW inventory_aging_qty_value_report_view AS (
                SELECT DISTINCT 
                    {select_fields}
                FROM  
                    inventory_aging_qty_value_report qvr

                )""".format(select_fields=select_fields))

        view_id = self.env.ref("inventory_aging_report_flexible_dates.inventory_inventory_aging_value_report_view_tree_view").id,
        action = {
            'name': _("Inventory Ageing Report As On {}".format(self.date_start)),
            'type': 'ir.actions.act_window',
            'res_model': 'inventory.aging.qty.value.report.view',
            'view_mode': 'list',
            'view_type': 'tree',
            'view_id': view_id,
            'views': [[view_id, 'list']],
            'target': 'current',
            'context': {'search_default_positive_values':1},
            }

        return action

    def action_prepare_xlsx_data_values(self,worksheet,row,line,left_alignment,center_alignment,right_alignment):
        worksheet.write(row, 1, line.product_id.default_code,  left_alignment)
        worksheet.write(row, 2, line.product_id.name,  left_alignment)
        worksheet.write(row, 3, line.product_category_id.display_name,  left_alignment)
        worksheet.write(row, 4, line.product_uom_id.display_name,  center_alignment)
        worksheet.write(row, 5, line.lot_id.name,  left_alignment)
        worksheet.write(row, 6, line.lot_create_date.strftime('%Y-%m-%d'),  center_alignment)
        return 6

    def action_prepare_xlsx_heading_values(self,worksheet,column_heading_style):
        worksheet.write(1, 1, "Product Code",column_heading_style)        
        worksheet.write(1, 2, "Product Name",column_heading_style)        
        worksheet.write(1, 3, "Product Category",column_heading_style)
        worksheet.write(1, 4, "UOM",column_heading_style)
        worksheet.write(1, 5, "Lot/Serial Number",column_heading_style)
        worksheet.write(1, 6, "Lot Create Date",column_heading_style)     
        return 6



    def button_download_xlsx_report(self):
        self.retrieve_aging_report()
        self.env.cr.commit()
        period_1_to = self.period_1_to
        period_2_to = self.period_2_to
        period_3_to = self.period_3_to
        period_4_to = self.period_4_to
        period_5_to = self.period_5_to
        period_6_to = self.period_6_to
        period_7_to = self.period_7_to

        aging_days_list = [(0,period_1_to),
                           (period_1_to + 1, period_2_to),
                           (period_2_to + 1, period_3_to),
                           (period_3_to + 1, period_4_to),
                           (period_4_to + 1, period_5_to),
                           (period_5_to + 1, period_6_to),
                           (period_6_to + 1, period_7_to),
                        ]
        quantity_aging_periods = []
        value_aging_periods = []
        for period_val in aging_days_list:
            quantity_aging_periods.append('{}-{} Qty'.format(period_val[0],period_val[1]))
            value_aging_periods.append('{}-{} Value'.format(period_val[0],period_val[1]))


        quantity_aging_periods.append('{}-Older Qty'.format(period_7_to + 1))
        value_aging_periods.append('{}-Older Value'.format(period_7_to + 1))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Inventory Ageing Report As On {}".format(self.date_start))
        worksheet.freeze_panes(2,3)
        column_heading_style = workbook.add_format({'bold': True,
            'font_color': 'black',
            'bg_color': 'deebf7',
            'font_name':'Arial',
            'font_size': 10,
            'border':1,
            'border_color':'black',
            'align': 'center',
            'valign': 'vcenter'
        })
        left_alignment = workbook.add_format({
            'font_color': 'black',
            'font_name':'Arial',
            'font_size': 10,
            'border':1,
            'border_color':'black',
            'align': 'left',
            'valign': 'vcenter'
        })
        center_alignment = workbook.add_format({
            'font_color': 'black',
            'font_name':'Arial',
            'font_size': 10,
            'border':1,
            'border_color':'black',
            'align': 'center',
            'valign': 'vcenter'
        })

        right_alignment = workbook.add_format({
            'font_color': 'black',
            'font_size': 10,
            'font_name':'Arial',
            'border':1,
            'border_color':'black',
            'align': 'right',
            'valign': 'vcenter'
        })

        total_values_color_values = workbook.add_format({
            'font_color': 'black',
            'font_name':'Arial',
            'bg_color': 'dbdbdb',
            'font_size': 10,
            # 'border':1,
            'border_color':'black',
            'align': 'right',
            'valign': 'vcenter'
        })
        col = self.action_prepare_xlsx_heading_values(worksheet,column_heading_style)

        # worksheet.write(1, 5, "Sales Person",column_heading_style)
        # worksheet.write(1, 6, "Supplier Lot Number",column_heading_style)
        # worksheet.write(1, 7, "Lot Create Date",column_heading_style)
        # worksheet.write(1, 8, "Producer Name",column_heading_style)

        if self.env.user.has_group('inventory_aging_report_flexible_dates.aging_value_access_group'):
            worksheet.write(1, col+1, "Average Cost",column_heading_style)
            col+=1
            worksheet.write(1, col+1, "Quantity",column_heading_style)
            worksheet.write(1, col+2, "Value",column_heading_style)
            worksheet.write(1, col+3, "{}".format(quantity_aging_periods[0]),column_heading_style)
            worksheet.write(1, col+4, "{}".format(value_aging_periods[0]),column_heading_style)
            worksheet.write(1, col+5, "{}".format(quantity_aging_periods[1]),column_heading_style)
            worksheet.write(1, col+6, "{}".format(value_aging_periods[1]),column_heading_style)
            worksheet.write(1, col+7, "{}".format(quantity_aging_periods[2]),column_heading_style)
            worksheet.write(1, col+8, "{}".format(value_aging_periods[2]),column_heading_style)
            worksheet.write(1, col+9, "{}".format(quantity_aging_periods[3]),column_heading_style)
            worksheet.write(1, col+10, "{}".format(value_aging_periods[3]),column_heading_style)
            worksheet.write(1, col+11, "{}".format(quantity_aging_periods[4]),column_heading_style)
            worksheet.write(1, col+12, "{}".format(value_aging_periods[4]),column_heading_style)
            worksheet.write(1, col+13, "{}".format(quantity_aging_periods[5]),column_heading_style)
            worksheet.write(1, col+14, "{}".format(value_aging_periods[5]),column_heading_style)
            worksheet.write(1, col+15, "{}".format(quantity_aging_periods[6]),column_heading_style)
            worksheet.write(1, col+16, "{}".format(value_aging_periods[6]),column_heading_style)
            worksheet.write(1, col+17, "{}".format(quantity_aging_periods[7]),column_heading_style)
            worksheet.write(1, col+18, "{}".format(value_aging_periods[7]),column_heading_style)
            worksheet.write(1, col+19, "Company",column_heading_style)

            row = 2
            for line in self.env['inventory.aging.qty.value.report'].search(['|',('quantity','!=',0),('value','!=',0),('product_id.is_storable', '=', True)]):
                data_col = self.action_prepare_xlsx_data_values(worksheet,row,line,left_alignment,center_alignment,right_alignment)
                worksheet.write(row, data_col+1, line.avg_cost,center_alignment)
                data_col+=1
                worksheet.write(row, data_col+1, line.quantity,  center_alignment)
                worksheet.write(row, data_col+2, line.value,  center_alignment)
                worksheet.write(row, data_col+3, line.period_1_qty,  center_alignment)
                worksheet.write(row, data_col+4, line.period_1_value,  center_alignment)
                worksheet.write(row, data_col+5, line.period_2_qty,  center_alignment)
                worksheet.write(row, data_col+6, line.period_2_value,  center_alignment)
                worksheet.write(row, data_col+7, line.period_3_qty,  center_alignment)
                worksheet.write(row, data_col+8, line.period_3_value,  center_alignment)
                worksheet.write(row, data_col+9, line.period_4_qty,  center_alignment)
                worksheet.write(row, data_col+10, line.period_4_value,  center_alignment)
                worksheet.write(row, data_col+11, line.period_5_qty,  center_alignment)
                worksheet.write(row, data_col+12, line.period_5_value,  center_alignment)
                worksheet.write(row, data_col+13, line.period_6_qty,  center_alignment)
                worksheet.write(row, data_col+14, line.period_6_value,  center_alignment)
                worksheet.write(row, data_col+15, line.period_7_qty,  center_alignment)
                worksheet.write(row, data_col+16, line.period_7_value,  center_alignment)
                worksheet.write(row, data_col+17, line.older_qty,  center_alignment)
                worksheet.write(row, data_col+18, line.older_value,  center_alignment)
                worksheet.write(row, data_col+19, line.company_id.name,  left_alignment)
                row+=1

        else:
            worksheet.write(1, col+1, "Average Cost",column_heading_style)
            col+=1
            worksheet.write(1, col+1, "Quantity",column_heading_style)
            worksheet.write(1, col+2, "Value",column_heading_style)
            worksheet.write(1, col+3, "{}".format(quantity_aging_periods[0]),column_heading_style)
            worksheet.write(1, col+4, "{}".format(quantity_aging_periods[1]),column_heading_style)
            worksheet.write(1, col+5, "{}".format(quantity_aging_periods[2]),column_heading_style)
            worksheet.write(1, col+6, "{}".format(quantity_aging_periods[3]),column_heading_style)
            worksheet.write(1, col+7, "{}".format(quantity_aging_periods[4]),column_heading_style)
            worksheet.write(1, col+8, "{}".format(quantity_aging_periods[5]),column_heading_style)
            worksheet.write(1, col+9, "{}".format(quantity_aging_periods[6]),column_heading_style)
            worksheet.write(1, col+10, "{}".format(quantity_aging_periods[7]),column_heading_style)
            worksheet.write(1, col+11, "Company",column_heading_style)

            row = 2
            for line in self.env['inventory.aging.qty.value.report'].search(['|',('quantity','!=',0),('value','!=',0),('product_id.is_storable', '=', True)]):
                data_col = self.action_prepare_xlsx_data_values(worksheet,row,line,left_alignment,center_alignment,right_alignment)
                worksheet.write(row, data_col+1, line.avg_cost,center_alignment)
                data_col+=1
                worksheet.write(row, data_col+1, line.quantity,  center_alignment)
                worksheet.write(row, data_col+2, line.value,  center_alignment)
                worksheet.write(row, data_col+3, line.period_1_qty,  center_alignment)
                worksheet.write(row, data_col+4, line.period_2_qty,  center_alignment)
                worksheet.write(row, data_col+5, line.period_3_qty,  center_alignment)
                worksheet.write(row, data_col+6, line.period_4_qty,  center_alignment)
                worksheet.write(row, data_col+7, line.period_5_qty,  center_alignment)
                worksheet.write(row, data_col+8, line.period_6_qty,  center_alignment)
                worksheet.write(row, data_col+9, line.period_7_qty,  center_alignment)
                worksheet.write(row, data_col+10, line.older_qty,  center_alignment)
                worksheet.write(row, data_col+11, line.company_id.name,  left_alignment)
                row+=1

        
        worksheet.set_column(2, 1, 5)  # Column B
        worksheet.set_column(2, 2, 50)  # Column C
        worksheet.set_column(2, 4, 30)  # Column E
        worksheet.set_column(2, 5, 30)  # Column F
        worksheet.set_column(2, 6, 5)  # Column G
        worksheet.set_column(2, 7, 5)  # Column H
        worksheet.set_column(2, 8, 5)  # Column I
                
        workbook.close()
        output.seek(0)

        file_name = 'Inventory Ageing Report.xlsx'
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': file_name,
            'res_model': 'inventory.aging.value.wizard',
            'res_id': self.id,
        })

        # Return the action to download the report
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}'.format(attachment_id.id),
            'target': 'self',
            }