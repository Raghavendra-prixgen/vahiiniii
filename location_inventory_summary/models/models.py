# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo import tools
from lxml import etree
import json
import pytz
from datetime import datetime, time


class InvBalSumReport(models.Model):
    _name = 'location.inv.sum.report.view'
    _auto = False
    _description = 'Location Inventory Summary'

    y_product_id = fields.Many2one('product.product',string="Product")
    y_location_id = fields.Many2one('stock.location',string="Location")
    y_lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")
    y_company_id = fields.Many2one('res.company' ,string="Company")
    y_uom_id = fields.Many2one('uom.uom', store=True, string="UOM")
    y_default_code = fields.Char(store=True, string="Code")
    y_opening_stock = fields.Float('Opening(Qty)')
    y_stock_increase = fields.Float('Inward(Qty)')
    y_stock_decrease = fields.Float('Outward(Qty)')
    y_closing_stock = fields.Float('Closing(Qty)')
    y_product_group_1_id= fields.Many2one('product.group.1',string="Product Group 1")
    y_product_group_2_id = fields.Many2one('product.group.2',string="Product Group 2")
    y_product_group_3_id = fields.Many2one('product.group.3',string="Product Group 3")
    y_categ_id = fields.Many2one('product.category',string="Product Category")    

    @api.model
    def init(self):
        tz_name = self._context.get('tz') or self.env.user.tz
        tools.drop_view_if_exists(self._cr, 'location_inv_sum_report_view')
        self._cr.execute("""CREATE OR REPLACE VIEW location_inv_sum_report_view AS (
                                WITH all_moves AS (
                        SELECT
                            line.product_id,
                            line.lot_id,
                            line.company_id,
                            line.location_dest_id AS location_id, -- Incoming moves credit the destination location
                            line.date,
                            line.quantity
                        FROM
                            stock_move_line line
                        JOIN
                            stock_location sl ON line.location_dest_id = sl.id
                        
                        UNION ALL

                        SELECT
                            line.product_id,
                            line.lot_id,
                            line.company_id,
                            line.location_id AS location_id, -- Outgoing moves debit the source location
                            line.date,
                            -line.quantity -- The quantity is negative because it's leaving
                        FROM
                            stock_move_line line
                        JOIN
                            stock_location sl ON line.location_id = sl.id
                    )
                    -- Step 2: Aggregate the unified moves using conditional aggregation.
                    SELECT
                        ROW_NUMBER() OVER () AS id,
                        result.y_product_id,
                        result.y_lot_id,
                        result.y_location_id,
                        result.y_categ_id,
                        result.y_product_group_1_id,
                        result.y_product_group_2_id,
                        result.y_product_group_3_id,
                        result.y_company_id,
                        result.y_uom_id,
                        result.y_default_code,
                        result.y_opening_stock,
                        result.y_stock_increase,
                        result.y_stock_decrease,
                        -- Closing stock is calculated from the aggregated values
                        (result.y_opening_stock + result.y_stock_increase + result.y_stock_decrease) AS y_closing_stock
                    FROM (
                        SELECT
                            pp.id AS y_product_id,
                            moves.lot_id AS y_lot_id,
                            moves.location_id AS y_location_id,
                            pt.categ_id AS y_categ_id,
                            pp.y_product_group_1 AS y_product_group_1_id,
                            pp.y_product_group_2 AS y_product_group_2_id,
                            pp.y_product_group_3 AS y_product_group_3_id,
                            moves.company_id AS y_company_id,
                            pt.uom_id AS y_uom_id,
                            pp.default_code AS y_default_code,

                            -- Opening Stock: Sum of all moves (positive and negative) before the start date
                            SUM(CASE WHEN moves.date < (TIMESTAMP '2025-01-01 00:00:00' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') THEN moves.quantity ELSE 0 END) AS y_opening_stock,

                            -- Stock Increase (Inward): Sum of positive moves within the date range
                            SUM(CASE WHEN moves.date BETWEEN (TIMESTAMP '2025-01-01 00:00:00' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '2025-02-02 23:59:59' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND moves.quantity > 0 THEN moves.quantity ELSE 0 END) AS y_stock_increase,

                            -- Stock Decrease (Outward): Sum of negative moves within the date range
                            SUM(CASE WHEN moves.date BETWEEN (TIMESTAMP '2025-01-01 00:00:00' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND (TIMESTAMP '2025-02-02 23:59:59' AT TIME ZONE '{tz_name}' AT TIME ZONE 'UTC') AND moves.quantity < 0 THEN moves.quantity ELSE 0 END) AS y_stock_decrease

                        FROM
                            all_moves moves
                        JOIN
                            product_product pp ON moves.product_id = pp.id
                        JOIN
                            product_template pt ON pp.product_tmpl_id = pt.id
                        WHERE
                            pt.type = 'consu'
                            AND pt.is_storable
                        GROUP BY
                            pp.id,
                            moves.lot_id,
                            moves.location_id,
                            pt.categ_id,
                            pp.y_product_group_1,
                            pp.y_product_group_2,
                            pp.y_product_group_3,
                            moves.company_id,
                            pt.uom_id,
                            pp.default_code
                    ) result
                    WHERE
                        -- Filter out rows with no stock at all
                        result.y_opening_stock != 0 OR result.y_stock_increase != 0 OR result.y_stock_decrease != 0
                                
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
    _name = 'location.inv.sum.report.view.wiz'
    _description = 'Location Inventory Summary Wizard'

    y_open_date = fields.Date(string='Start Date')
    y_close_date = fields.Date(string='End Date')
    y_company_id = fields.Many2one('res.company',string='Company')
    y_location_ids = fields.Many2many('stock.location', string="Location")
    
    @api.onchange('y_close_date')
    def _onchange_y_close_date(self):
        if self.y_close_date < self.y_open_date:
            raise ValidationError(_("""End Date should not be less than Start Date"""))   

    def prepare_domain(self):
        if not self.y_location_ids.ids:
            return ' AND 1 = 1',' AND 1 = 1'
        if len(self.y_location_ids.ids) > 1:
            src_domain_clause = " AND line.location_id IN {locations}".format(locations=tuple(self.y_location_ids.ids))
            dest_domain_clause = " AND line.location_dest_id IN {locations}".format(locations=tuple(self.y_location_ids.ids))
        elif len(self.y_location_ids.ids) == 1:
            src_domain_clause = " AND line.location_id = {location}".format(location=self.y_location_ids.ids[0])    
            dest_domain_clause = " AND line.location_dest_id = {location}".format(location=self.y_location_ids.ids[0])
        return src_domain_clause,dest_domain_clause

    def prepare_company_clause(self):
        company_clause = " AND line.company_id = {}".format(self.y_company_id.id)
        if not self.sudo().y_company_id.child_ids:
            company_clause = " AND line.company_id = {}".format(self.y_company_id.id)
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id).ids
            if len(access_company_ids) == 1:
                company_clause = " AND line.company_id = {}".format(access_company_ids[0])
            else:
                company_clause = " AND line.company_id in {}".format(tuple(access_company_ids))

        return company_clause
            
    def action_open_report(self):
        tz_name = self._context.get('tz') or self.env.user.tz
        context_timezone = pytz.timezone(tz_name)
        open_date = context_timezone.localize(datetime.combine(self.y_open_date, time.min)).astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        close_date = context_timezone.localize(datetime.combine(self.y_close_date, time.max)).astimezone(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        company_clause = self.prepare_company_clause()
        src_domain_clause,dest_domain_clause = self.prepare_domain()
        tools.drop_view_if_exists(self._cr, 'location_inv_sum_report_view')
        query = """
                CREATE OR REPLACE VIEW location_inv_sum_report_view AS (
                    WITH all_moves AS (
                        SELECT
                            line.product_id,
                            line.lot_id,
                            line.company_id,
                            line.location_dest_id AS location_id, -- Incoming moves credit the destination location
                            line.location_dest_id AS location_dest_id,
                            line.date,
                            line.quantity
                        FROM
                            stock_move_line line
                        LEFT JOIN
                            product_product pp ON line.product_id = pp.id
                        LEFT JOIN
                            product_template pt ON pp.product_tmpl_id = pt.id
                        WHERE 
                            pt.type = 'consu'
                            AND pt.is_storable
                            AND line.state = 'done'
                            {company_clause}
                            {dest_domain_clause}
                        
                        UNION ALL

                        SELECT
                            line.product_id,
                            line.lot_id,
                            line.company_id,
                            line.location_id AS location_id, -- Outgoing moves debit the source location
                            line.location_dest_id AS location_dest_id,
                            line.date,
                            -line.quantity -- The quantity is negative because it's leaving
                        FROM
                            stock_move_line line
                        LEFT JOIN
                            product_product pp ON line.product_id = pp.id
                        LEFT JOIN
                            product_template pt ON pp.product_tmpl_id = pt.id
                        WHERE 
                            pt.type = 'consu'
                            AND pt.is_storable
                            AND line.state = 'done'
                            {company_clause}
                            {src_domain_clause}
                    )
                    -- Step 2: Aggregate the unified moves using conditional aggregation.
                    SELECT
                        ROW_NUMBER() OVER () AS id,
                        result.y_product_id,
                        result.y_lot_id,
                        result.y_location_id,
                        result.y_categ_id,
                        result.y_product_group_1_id,
                        result.y_product_group_2_id,
                        result.y_product_group_3_id,
                        result.y_company_id,
                        result.y_uom_id,
                        result.y_default_code,
                        result.y_opening_stock,
                        result.y_stock_increase,
                        result.y_stock_decrease,
                        -- Closing stock is calculated from the aggregated values
                        (result.y_opening_stock + result.y_stock_increase + result.y_stock_decrease) AS y_closing_stock
                    FROM (
                        SELECT
                            pp.id AS y_product_id,
                            line.lot_id AS y_lot_id,
                            line.location_id AS y_location_id,
                            pt.categ_id AS y_categ_id,
                            pp.y_product_group_1 AS y_product_group_1_id,
                            pp.y_product_group_2 AS y_product_group_2_id,
                            pp.y_product_group_3 AS y_product_group_3_id,
                            line.company_id AS y_company_id,
                            pt.uom_id AS y_uom_id,
                            pp.default_code AS y_default_code,

                            -- Opening Stock: Sum of all moves (positive and negative) before the start date
                            SUM(CASE WHEN line.date < '{open_date}' THEN line.quantity ELSE 0 END) AS y_opening_stock,

                            -- Stock Increase (Inward): Sum of positive moves within the date range
                            SUM(CASE WHEN line.date BETWEEN '{open_date}' AND '{close_date}' AND line.quantity > 0 THEN line.quantity ELSE 0 END) AS y_stock_increase,

                            -- Stock Decrease (Outward): Sum of negative moves within the date range
                            SUM(CASE WHEN line.date BETWEEN '{open_date}' AND '{close_date}' AND line.quantity < 0 THEN line.quantity ELSE 0 END) AS y_stock_decrease

                        FROM
                            all_moves line
                        LEFT JOIN
                            product_product pp ON line.product_id = pp.id
                        LEFT JOIN
                            product_template pt ON pp.product_tmpl_id = pt.id
                        
                            
                        GROUP BY
                            pp.id,
                            line.lot_id,
                            line.location_id,
                            pt.categ_id,
                            pp.y_product_group_1,
                            pp.y_product_group_2,
                            pp.y_product_group_3,
                            line.company_id,
                            pt.uom_id,
                            pp.default_code
                    ) result
                    WHERE
                        -- Filter out rows with no stock at all
                        result.y_opening_stock != 0 OR result.y_stock_increase != 0 OR result.y_stock_decrease != 0
                )""".format(open_date=open_date,
                            close_date=close_date,
                            company_clause=company_clause,
                            tz_name=tz_name,
                            src_domain_clause=src_domain_clause,
                            dest_domain_clause=dest_domain_clause)

        # print('\n'*10)
        # print(query)
        # print('\n'*10)
        self._cr.execute(query)
        tree_view_id = self.env.ref('location_inventory_summary.location_inventory_balance_summmary_tree_view').id
        y_open_date = self.y_open_date.strftime('%d-%m-%Y')
        y_close_date = self.y_close_date.strftime('%d-%m-%Y')
        return {
            'name': 'Locatation Inventory Summary ({} To {}) '.format(y_open_date,y_close_date),
            'view_mode': 'list,pivot',
            'views': [[tree_view_id, 'list']],
            'res_model': 'location.inv.sum.report.view',
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