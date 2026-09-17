from odoo import models, fields, api, _
import xlsxwriter   #import xlwt #help http://nullege.com/codes/search/xlwt.Style.easyxf    http://nullege.com/codes/search/xlwt
import base64
import io
import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

from dateutil.relativedelta import relativedelta
import calendar
import pdb


class ProductionReportLine(models.TransientModel):
    _name = 'production.report.line'
    _description = 'Production Report Line'


    # Fields matching the Excel report columns
    date = fields.Date(string='Date')
    mo_id = fields.Many2one('mrp.production',string='MO Number')
    work_center = fields.Char(string='Work Center')
    product_code = fields.Char(string='Product Code')
    product_description = fields.Char(string='Product Description')
    category_id = fields.Many2one('product.category',string='Category')
    actual_quantity_produced = fields.Float(string='Actual Quantity Produced')
    standard_weight = fields.Float(string='Standard Weight (kg)')
    actual_weight = fields.Float(string='Actual Weight (kg)')
    consumed_material = fields.Char(string='Consumed Material')
    standard_material_consumption = fields.Float(string='Standard Material Consumption')
    actual_material_consumption = fields.Float(string='Actual Material Consumption')
    company_id = fields.Many2one('res.company',string="Company")

class ProductionReportWiz(models.TransientModel):
    _name = 'production.report.wiz'
    _description = "production.report.wiz"
    
    start_date = fields.Date(string="From")
    end_date = fields.Date(string="To")

    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name", default='Production Report.xls')
    exported = fields.Boolean(string="Exported", default=False)

    product_categ_ids = fields.Many2many('product.category',string="Product Category")
    company_id = fields.Many2one('res.company',string="Company")

    @api.onchange('start_date','end_date')
    def onchange_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_("Start Date must be smaller than End Date"))
            if self.end_date > self.start_date and (self.end_date - self.start_date).days > 365:
                raise ValidationError(_("You can not have an overlap between two Financial years, please correct the start and/or end dates"))
    

    def _prepeare_production_report_domain(self):
        domain = [
                ('date_start', '>=', self.start_date),
                ('date_finished', '<=', self.end_date),
                ('state', '=', 'done'),
                ('product_id.categ_id', 'in', self.product_categ_ids.ids)
                ]

        company_ids = self.env['res.company']
        if not self.sudo().company_id.child_ids:
            domain+=[('company_id','=',self.company_id.id)]
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.company_id) + self.company_id)
            if len(access_company_ids) == 1:
                domain+=[('company_id','=',access_company_ids[0].id)]
            else:
                domain+=[('company_id','in',access_company_ids.ids)]
        
        return domain
    def generate_production_report(self):
            # Clear existing lines
            self.env['production.report.line'].search([]).unlink()

            # Search for production orders
            domain = self._prepeare_production_report_domain()

            production_orders = self.env['mrp.production'].search(domain)
            # Create report lines
            for production in production_orders:
                # Get work center
                work_center = production.workorder_ids[0].workcenter_id.name if production.workorder_ids else ''

                # Create report line for each raw material
                for each_line in production.move_raw_ids.filtered(lambda move:move.state == 'done'):
                    # Find BOM line for the current component
                    bom_line = each_line.bom_line_id
                    if not bom_line:
                        bom_lines = production.bom_id.bom_line_ids.filtered(lambda bom_line:bom_line.product_id == each_line.product_id)
                        if bom_lines:
                            bom_line = bom_lines[0]
                    
                    # Calculate standard consumption
                    standard_consumption = production.product_qty
                    if bom_line:
                        standard_consumption = ((bom_line.product_qty / bom_line.bom_id.product_qty if bom_line.bom_id.product_qty > 0 else 1) * production.product_qty)

                    self.env['production.report.line'].create({
                        'date': production.date_finished,
                        'mo_id': production.id,
                        'work_center': work_center,
                        'product_code': production.product_id.default_code,
                        'product_description': production.product_id.name,
                        'category_id': production.product_id.categ_id.id,
                        'actual_quantity_produced': production.product_qty,
                        'standard_weight': production.product_id.weight * production.product_qty,
                        'actual_weight': production.y_fg_actual_weight,
                        'consumed_material': each_line.product_id.name,
                        'standard_material_consumption': standard_consumption,
                        'actual_material_consumption': each_line.quantity,
                        'company_id':production.company_id.id,
                    })
            tree_view_id = self.env.ref('px_production_status_report.production_report_line_tree').id
            y_start_date = self.start_date.strftime('%d-%m-%Y')
            y_end_date = self.end_date.strftime('%d-%m-%Y')
            # Open tree view
            return {
                'name': 'Production Report ({} To {}) '.format(y_start_date, y_end_date),
                'type': 'ir.actions.act_window',
                'res_model': 'production.report.line',
                'view_mode': 'list,pivot',
                'views': [[tree_view_id, 'list']],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def print_xls_report(self):
        fl = io.BytesIO()
        wb = xlsxwriter.Workbook(fl)
        style_text = wb.add_format({'font_name':'Times New Roman', 'bold':False, 'border':1,'num_format':'#,##0.00;-#,##0.00;""'})
        style_float = wb.add_format({'font_name':'Times New Roman', 'bold':False, 'border':1,'num_format':'###0.00;-###0.00;""'})
        style_heading = wb.add_format({'font_name':'Times New Roman', 'bold':True, 'border':1,'font_size':14, 'bg_color':'#ffff00', 'font_size':14, 'align':'center', 'num_format':'#,##0.00;-#,##0.00;"-"'})
        style_heading2 = wb.add_format({'font_name':'Times New Roman', 'bold':True, 'border':1,'font_size':13, 'align':'center', 'num_format':'#,##0.00;-#,##0.00;"-"'})
        style_title = wb.add_format({'font_name':'Times New Roman', 'bold':True, 'border':1,'font_size':13,'bg_color':'#ffdb4d','num_format':'#,##0.00;-#,##0.00;"-"'})
        style_title1 = wb.add_format({'font_name':'Times New Roman', 'bold':True, 'border':1,'font_size':13,'bg_color':'#ffdb4d','num_format':'#,##0;-#,##0;"-"'})
        style_title2 = wb.add_format({'font_name':'Times New Roman', 'bold':True, 'border':1,'font_size':13,'bg_color':'#ffff00','num_format':'###0.00;-###0.00;""'})
        
        ws = wb.add_worksheet('Production Report')
        # ws.set_column('A:B', 25)
        ws.set_column('B:Z', 15)
        
        # start_date = self.start_date
        # end_date = self.end_date
        # date = start_date + relativedelta(years=1)
        ws.merge_range(0, 0, 0, 12, "PRODUCTION REPORT BASED ON MANUFACTURING ORDER " + str(self.start_date) + "To" + str(self.end_date),style_heading)
        
        row = 1
        ws.write(row, 0, "DATE",style_title1)
        ws.write(row, 1, "MO-NO'S",style_title)
        ws.write(row, 2, "WORK CENTER",style_title)
        ws.write(row, 3, "PRODUCT CODE",style_title)
        ws.write(row, 4, "PRODUCT DESCRIPTION ",style_title)
        ws.write(row, 5, "CATEGORY",style_title)
        ws.write(row, 6, "ACTUAL QUANTITY PRODUCED",style_title)
        ws.write(row, 7, "STANDARD WEIGHT IN KG's",style_title)
        ws.write(row, 8, "ACTUAL WEIGHTIN KG's",style_title)
        ws.write(row, 9, "CONSUME MATERIAL ",style_title)
        ws.write(row, 10, "STANDARD MATERIAL CONSUMPTION ",style_title)
        ws.write(row, 11, "ACTUAL MATERIAL CONSUMPTION",style_title)
        ws.write(row, 12, "COMPANY",style_title)


      
        domain = self._prepeare_production_report_domain()
        production_obj = self.env['mrp.production'].search(domain)

        # sl_num =1
        row =2

        for production in production_obj:
            ws.write(row, 0, datetime.datetime.strftime(production.date_finished, '%d-%m-%Y') )
            ws.write(row, 1, production.name)

            for x in production.workorder_ids:
                var = x.workcenter_id.name
                ws.write(row, 2, var)
            ws.write(row, 3, production.product_id.default_code)
            ws.write(row, 4, production.product_id.name)
            ws.write(row, 5, production.product_id.categ_id.display_name)
            ws.write(row, 6, production.product_qty)
            ws.write(row, 7, production.product_id.weight*production.product_qty)
            ws.write(row, 8, production.y_fg_actual_weight)
            ws.write(row, 12, production.company_id.name or '')
            for each_line in production.move_raw_ids.filtered(lambda move:move.state == 'done'):
                ws.write(row, 9, each_line.product_id.name)

                curr_comp_id = each_line.bom_line_id
                if not curr_comp_id:
                    bom_lines = production.bom_id.bom_line_ids.filtered(lambda bom_line:bom_line.product_id == each_line.product_id)
                    if bom_lines:
                        curr_comp_id = bom_lines[0]
                        
                standard_consumption = production.product_qty
                if curr_comp_id:
                    standard_consumption = ((curr_comp_id.product_qty / curr_comp_id.bom_id.product_qty if curr_comp_id.bom_id.product_qty >= 1 else 1 ) *  production.product_qty)
                    
                ws.write(row, 10, standard_consumption)
                ws.write(row, 11, each_line.quantity)

                row += 1


        wb.close()
        fl.seek(0)
        file_name = f'Production Report{self.start_date}_{self.end_date}.xlsx'
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(fl.read()),
            'store_fname': file_name,
            'res_model': 'production.report.wiz',
            'res_id': self.id,
        })
        # Return the action to download the report
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}'.format(attachment_id.id),
            'target': 'self',
        }
