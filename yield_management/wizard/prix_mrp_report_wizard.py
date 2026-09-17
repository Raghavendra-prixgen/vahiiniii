from odoo import models, fields, api, _
from datetime import datetime, timedelta,date
import calendar
from xlwt import easyxf
import xlwt
import io
import base64
import datetime
import math
import pdb
import json
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

class MrpOrderReportWizard(models.TransientModel):
    _name = "prix.mrp.report.wizard"
    _description = "Yield Analysis"
        
    y_date_from = fields.Date(string="Start Date")
    y_date_to = fields.Date(string="End Date")
    y_company_id = fields.Many2one('res.company',string="Company")

    @api.constrains('y_date_from','y_date_to')
    def _code_constrains(self):
        if self.y_date_from > self.y_date_to:
            raise ValidationError(_("'From Date' must be before 'To Date'"))

    def _prepare_domain(self):        
        domain = [
            ('y_mo_date', '>=', self.y_date_from),
            ('y_mo_date', '<=', self.y_date_to),
            ('y_mo_id.state', '=', 'done')
            ]

        company_ids = self.env['res.company']
        if not self.sudo().y_company_id.child_ids:
            domain+= [('y_mo_id.company_id','=',self.y_company_id.id)]
        else:
            company_ids = self.env.user.company_ids
            access_company_ids = (company_ids.filtered(lambda x:x.parent_id == self.y_company_id) + self.y_company_id)
            if len(access_company_ids) == 1:
                domain+=[('y_mo_id.company_id','=',access_company_ids[0].id)]
            else:
                domain+=[('y_mo_id.company_id','in',access_company_ids.ids)]

        return domain
        
    def action_manufucaturing_report_wiz(self):
        domain = self._prepare_domain()
        view_id = self.env.ref('yield_management.manufacturing_report_list_view').id
        return {
            'name': 'Yield Analysis',
            'view_mode': 'list,pivot,graph',
            'views': [[view_id, 'list'],[False, 'pivot'],[False, 'graph']],
            'res_model': 'prix.mrp.report',
            'type': 'ir.actions.act_window',
            'domain': domain,
            }

    def action_manufucaturing_report_xlsx(self):
        """Generate Excel report for yield management"""
        self.ensure_one()
        
        # Get manufacturing orders within the date range
        domain = self._prepare_domain()

        # Create Excel workbook
        workbook = xlwt.Workbook()
        
        # Define styles
        column_heading_style = easyxf('font:height 210; font:bold True;align: horiz center;pattern: pattern solid, fore_colour gray25;borders: left thin, right thin, top thin, bottom thin;')
        # column_heading_style = easyxf('font:height 210; font:bold True;align: horiz center; pattern: pattern solid, fore_colour gray25; borders: left thin, right thin, top thin, bottom thin;border-left-color black;border-right-color black;border-top-color black; border-bottom-color black;')
        value_heading_style = easyxf('font:height 210;font:bold True;align: horiz right;')
        right_alignment = easyxf('font:height 200; align: horiz right;')
        center_alignment = easyxf('font:height 200; align: horiz center;')
        left_alignment = easyxf('font:height 200; align: horiz left;')
        
        current_company_name = self.y_company_id.name
        report_heading = (
                    "Yield Management Report "
                    + datetime.strftime(self.y_date_from, '%m-%d-%Y')
                    + " To "
                    + datetime.strftime(self.y_date_to, '%m-%d-%Y')
                )
        worksheet = workbook.add_sheet('Yield Management Excel Sheet', cell_overwrite_ok=True)
        
        # Write headers
        worksheet.write_merge(1, 1, 2, 7, current_company_name, easyxf('font:height 250;font:bold True;align: horiz center;'))
        worksheet.write_merge(2, 2, 2, 7, report_heading, easyxf('font:height 250;font:bold True;align: horiz center;'))
        worksheet.write_merge(3, 3, 0, 11, '', easyxf('font:height 250;font:bold True;align: horiz center;'))

        # Column headers
        worksheet.write(4, 0, _('Manufacturing Order'), column_heading_style)
        worksheet.write(4, 1, _('MO Date'), column_heading_style)

        worksheet.write(4, 2, _('FG Product'), column_heading_style)
        worksheet.write(4, 3, _('Component'), column_heading_style)
        worksheet.write(4, 4, _('Planned Qty'), column_heading_style)
        worksheet.write(4, 5, _('Planned Cost'), column_heading_style)
        worksheet.write(4, 6, _('Actual Qty'), column_heading_style)
        worksheet.write(4, 7, _('Actual Cost'), column_heading_style)
        worksheet.write(4, 8, _('Variance Qty'), column_heading_style)
        worksheet.write(4, 9, _('Variance Cost'), column_heading_style)
        worksheet.write(4, 10, _('Variance Qty(%)'), column_heading_style)
        worksheet.write(4, 11, _('Variance Cost(%)'), column_heading_style)
        
        # Set column widths
        for col in range(12):
            worksheet.col(col).width = 5500
            worksheet.col(0).width = 7500
            worksheet.col(2).width = 7500
            worksheet.col(3).width = 7500
            worksheet.row(1).height = 400  # Row index 0 (1st line)
            worksheet.row(2).height = 400  # Row index 1 (2nd line)
            worksheet.row(4).height = 300
        row = 5
        
        # Write data rows
        for yeild_val in self.env['prix.mrp.report'].search(domain):
            worksheet.write(row, 0, yeild_val.y_mo_id.name or '', center_alignment)
            worksheet.write(row, 1, yeild_val.y_mo_date.date().strftime("%m-%d-%Y") if yeild_val.y_mo_date else '', center_alignment)
            worksheet.write(row, 2, yeild_val.y_fgproduct_id.name or '')
            worksheet.write(row, 3, yeild_val.y_product_id.name or '')
            worksheet.write(row, 4, yeild_val.y_planned_qty or 0, center_alignment)
            worksheet.write(row, 5, yeild_val.y_planned_cost or 0, center_alignment)
            worksheet.write(row, 6, yeild_val.y_actual_qty or 0, center_alignment)
            worksheet.write(row, 7, yeild_val.y_actual_cost or 0, center_alignment)
            worksheet.write(row, 8, yeild_val.y_variance_qty or 0, center_alignment)
            worksheet.write(row, 9, yeild_val.y_variance_cost or 0, center_alignment)
            worksheet.write(row, 10, yeild_val.y_variance_qty_percent or 0, center_alignment)
            worksheet.write(row, 11, yeild_val.y_variance_cost_percent or 0, center_alignment)
            row += 1

        # Save workbook to BytesIO
        output = io.BytesIO()
        workbook.save(output)
        
        # Encode to base64
        excel_file = base64.b64encode(output.getvalue())
        # Create attachment
        ir_values = {
            'name': 'Yield Management Excel Report',
            'type': 'binary',
            'datas': excel_file,
            'store_fname': 'Yield_Management_Report.xlsx',
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'prix.mrp.report.wizard',
            'res_id': self.id,
        }
        
        attachment = self.env['ir.attachment'].sudo().create(ir_values)
        
        # Send email with attachment
        try:
            group_name = self.env.ref('yield_management.group_for_mail_address')

            email_to_list = group_name.users.mapped('login')
            _logger.info(f"Preparing to send email to users: {email_to_list}")
            email_to = ', '.join(email_to_list)
            
            if email_to:
                email_template = self.env.ref('yield_management.yield_analysis_email_template')
                if email_template:
                    email_values = {
                        'email_to': email_to,
                        'email_from': self.env.user.email,
                    }
                    
                    email_template.attachment_ids = [(4, attachment.id)]
                    email_template.send_mail(self.id, email_values=email_values)
                    email_template.attachment_ids = [(5, 0, 0)]

                    
        except Exception as e:
            _logger.error(f"Failed to send email: {e}")

        output.close()
        _logger.info(f"Email was sent to: {email_to}")
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }