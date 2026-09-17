from odoo import api,fields, models
from datetime import datetime
import pytz

class CheckStockValuationWizard(models.TransientModel):
    _name = 'check.stock.valuation.wizard'
    _description = 'Check Stock Valuation Wizard'

    y_company_id = fields.Many2one('res.company', 'Company',required=True)
    y_start_date = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    y_end_date = fields.Date(string="End Date", required=True, default=fields.Date.today)

    @api.constrains('y_start_date','y_end_date')
    def date_constrains(self):
        for record in self: 
            if record.y_start_date and record.y_end_date:
                if record.y_start_date > record.y_end_date:
                    raise ValidationError(_("'Start Date' must be before 'End Date'"))
    
    def dict_to_insert_query(self,table_name, data):
        def format_value(value):
            if isinstance(value, str):
                return f"$${value}$$"
            elif isinstance(value, (int, float)):
                return str(value)
            elif isinstance(value, bool):
                return 'TRUE' if value else 'FALSE'
            elif value is None:
                return 'NULL'
            elif isinstance(value, list):
                return f"'{{{','.join(map(str, value))}}}'"  # Converts Python list to PostgreSQL array
            elif isinstance(value, datetime):
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif isinstance(value, date):
                return f"'{value.strftime('%Y-%m-%d')}'"
            else:
                raise ValueError(f"Unsupported data type: {type(value)}")

        # Extract columns and values
        columns = ', '.join(data.keys())
        values = ', '.join([format_value(v) for v in data.values()])
        
        # Construct the query
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
        return query

    def get_positive_stock_valuation_query(self,lot_id,company_clause,start_date,end_date):
        tz_name = self._context.get('tz') or self.env.user.tz
        query = """SELECT 
                        CASE WHEN SUM(svl.quantity) = 0 THEN 0
                            ELSE SUM(svl.value)/SUM(svl.quantity)
                            END AS quantity
                    FROM 
                        stock_valuation_layer svl
                    LEFT JOIN 
                        product_product pp ON pp.id = svl.product_id
                    LEFT JOIN 
                        product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE 
                        svl.create_date BETWEEN (TIMESTAMP '{start_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{end_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                        AND pt.type = 'consu'
                        AND pt.is_storable
                        AND svl.value > 0
                        AND svl.lot_id = {lot_id}
                        {company_clause}
                """.format(company_clause=company_clause,lot_id=lot_id,start_date=start_date,end_date=end_date,tz_name=tz_name)
        return query

    def get_negative_stock_valuation_query(self,lot_id,company_clause,start_date,end_date):
        tz_name = self._context.get('tz') or self.env.user.tz
        query = """SELECT 
                        CASE WHEN SUM(svl.quantity) = 0 THEN 0
                            ELSE SUM(svl.value)/SUM(svl.quantity)
                            END AS quantity
                    FROM 
                        stock_valuation_layer svl
                    LEFT JOIN 
                        product_product pp ON pp.id = svl.product_id
                    LEFT JOIN 
                        product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE 
                        svl.create_date BETWEEN (TIMESTAMP '{start_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '{end_date}' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC')
                        AND pt.type = 'consu'
                        AND pt.is_storable
                        AND svl.value < 0
                        AND svl.lot_id = {lot_id}
                        {company_clause}
                """.format(company_clause=company_clause,lot_id=lot_id,start_date=start_date,end_date=end_date,tz_name=tz_name)
        return query

    def get_table_lot_data(self,lot_id,company_clause,start_date,end_date):
        vals = {'y_lot_id':lot_id.id,
                'y_product_id':lot_id.product_id.id,
                'y_positive_quantity':0,
                'y_negative_quantity':0,
                'y_difference':0
                }

        lot_id = lot_id.id
        positive_query = self.get_positive_stock_valuation_query(lot_id,company_clause,start_date,end_date)
        self._cr.execute(positive_query)
        positive_data = self._cr.dictfetchall()
        for data in positive_data:
            if data.get('quantity'):
                vals.update({'y_positive_quantity':data.get('quantity')})

        negative_query = self.get_negative_stock_valuation_query(lot_id,company_clause,start_date,end_date)
        self._cr.execute(negative_query)
        negative_data = self._cr.dictfetchall()
        for data in negative_data:
            if data.get('quantity'):
                vals.update({'y_negative_quantity':data.get('quantity')})

        vals.update({'y_difference':vals.get('y_positive_quantity') - vals.get('y_negative_quantity')})
        return vals

    def action_open_valuation_values_report(self):
        start_date = str(self.y_start_date) + ' 00:00:00'
        end_date = str(self.y_end_date) + ' 23:59:59'
        domain = [('lot_id','!=',False),('product_id.is_storable', '=', True),("create_date", ">=", start_date), ("create_date", "<=", end_date)]
        if not self.sudo().y_company_id.child_ids:
            domain += [('company_id','=',self.y_company_id.id)]
            company_clause = " AND svl.company_id = {}".format(self.y_company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id).ids
            if len(access_company_ids) == 1:
                domain += [('company_id','=',access_company_ids[0])]
                company_clause = " AND svl.company_id = {}".format(access_company_ids[0])
            else:
                domain += [('company_id','in',access_company_ids)]
                company_clause = " AND svl.company_id in {}".format(tuple(access_company_ids))

        
        self._cr.execute("""DELETE FROM check_stock_valuation""")
        stock_valuation_obj = self.env['stock.valuation.layer'].sudo().search(domain)
        lot_ids = stock_valuation_obj.mapped('lot_id')
        for lot in lot_ids:
            data = self.get_table_lot_data(lot,company_clause,start_date,end_date)
            query = self.dict_to_insert_query('check_stock_valuation',data)
            self._cr.execute(query)
            


        

            
        return {
                'name':'Lot Cost Reconciliation',
                'type': 'ir.actions.act_window',
                'res_model': 'check.stock.valuation',
                'view_mode': 'list',
                'views': [[self.env.ref('lot_cost_reconciliation.view_check_stock_valuation_tree').id, 'list']],
                'target': 'current',
            }
        
class CheckStockValuation(models.Model):
    _name = 'check.stock.valuation'
    _description = "Check Stock Valuation"
    _rec_name = 'y_lot_id'
    

    y_lot_id = fields.Many2one('stock.lot',string="Lots / Serial Number")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_positive_quantity = fields.Float(string="Increased Cost Per Unit")
    y_negative_quantity = fields.Float(string="Decreased Cost Per Unit")
    y_difference = fields.Float(string="Difference")
