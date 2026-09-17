from odoo import fields, models, api,_,tools
from operator import itemgetter
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from lxml import etree
from datetime import datetime, timedelta,date
from xlwt import easyxf
import xlwt
import io
import base64
import datetime
import math
import pdb
import json
import xlsxwriter

def get_selection_label(self, object, field_name, field_value):
    try:
        return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])
    except:
        return field_value


class CompanyPropertyValuesReportWizard(models.TransientModel):
    _name = "company.property.values.report.wizard"
    _description = ""

    model_ids = fields.Many2many('ir.model','Model')
    property_field_ids = fields.Many2many('ir.model.fields','field_company_setting_rel',sting="Fields",domain="[('model_id','in',model_ids),('company_dependent','=',True)]")
    field_ids = fields.Many2many('ir.model.fields','field_database_setting_rel',sting="Fields",domain="[('model_id','in',model_ids),('ttype','in',('boolean','char','float','integer','json','many2one','reference','selection','text')),('name','!=','id'),('company_dependent','!=',True)]")
    is_company_settings = fields.Boolean(string="Company Settings")
    is_database_settings = fields.Boolean(string="Database Settings")

    @api.onchange('is_company_settings')
    def _onchange_company_settings(self):
        for wizard in self:
            if wizard.is_company_settings:
                wizard.is_database_settings = False
            

    @api.onchange('is_database_settings')
    def _onchange_database_settings(self):
        for wizard in self:
            if wizard.is_database_settings:
                wizard.is_company_settings = False          


    def dict_to_insert_query(self,table_name, filter_data):
        for data in filter_data:
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
                else:
                    raise ValueError(f"Unsupported data type: {type(value)}")

            # Extract columns and values
            columns = ', '.join(data.keys())
            values = ', '.join([format_value(v) for v in data.values()])
            
            # Construct the query
            if data.get('company_id'):
                company_id = data.get('company_id')
                field_id = data.get('field_id')
                rec_id = data.get('rec_id')
                sub_query = f"SELECT * FROM {table_name} WHERE company_id = {company_id} and field_id = {field_id} and rec_id = {rec_id}"
                self._cr.execute(sub_query)
                exist_ids = self._cr.dictfetchall()
                if not exist_ids:
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
                    self._cr.execute(query)
    
            else:
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
                self._cr.execute(query)


    def action_create_table_data(self):
        self._cr.execute("""DELETE FROM company_property_values_report""")
        if self.is_company_settings:
            for model in self.model_ids:
                for com_dep_field in self.property_field_ids.filtered(lambda x:x.model_id == model):
                    field_name = com_dep_field.name
                    field_model = com_dep_field.model
                    model_name = model.model.replace('.', '_')
                    query = """ SELECT
                                    field.id AS field_id,
                                    {model_name}.name AS record,
                                    {model_name}.id AS rec_id,
                                    company AS company_id,
                                    value AS value
                                FROM 
                                    {model_name}
                                    ,LATERAL jsonb_each({model_name}.{field_name}) AS key_value(company, value) 
                                LEFT JOIN 
                                    ir_model_fields field on field.name = '{field_name}'
                                """.format(model_name=model_name,field_name=field_name,field_model=field_model)

                    print(query,"TTTT")

                    self._cr.execute(query)
                    filter_ids = self._cr.dictfetchall()
                    if len(filter_ids):
                        if isinstance(filter_ids[0],dict):
                            for data in filter_ids:
                                data_record = self.env[model.model].sudo().search([('id','=',data.get('rec_id'))])
                                if data_record:
                                    data.update({'record':data_record.display_name})

                            if com_dep_field.ttype == 'many2one':
                                field_model_name = com_dep_field.relation
                                for model_data in filter_ids:
                                    record = model_data.get('value')
                                    if record:
                                        # Use Search to feach record details
                                        record_id = self.env[field_model_name].sudo().search([('id','=',record)])
                                        if record_id:
                                            model_data.update({'value':record_id.display_name})

                            if com_dep_field.ttype == 'selection':
                                for model_data in filter_ids:
                                    record_value = model_data.get('value')
                                    new_value = get_selection_label(self.env[field_model],field_model,field_name,record_value)
                                    model_data.update({'value':new_value})
                                        
                                        # Query to feach record details
                                        # query = """ SELECT ({model_name}.name->>'en_US') AS value FROM {model_name} WHERE id = {record}""".format(model_name=model_name,record=record)
                                        # self._cr.execute(query)
                                        # field_filter_ids = self._cr.dictfetchall()
                                        # if field_filter_ids:
                                        #     if isinstance(field_filter_ids[0],dict):
                                        #         model_data.update({'value':field_filter_ids[0].get('value')})

                        query = self.dict_to_insert_query('company_property_values_report',filter_ids)

                    query = """ SELECT 
                                    field.id AS field_id,
                                    defa.company_id AS company_id,
                                    defa.json_value AS value
                                FROM 
                                    ir_default defa
                                LEFT JOIN 
                                    ir_model_fields field ON field.id = defa.field_id
                                WHERE field.name = '{field_name}' and field.model = '{field_model}' and defa.json_value != 'false'
                            """.format(field_name=field_name,field_model=field_model)

                    new_record_list = []
                    self._cr.execute(query)
                    default_filter_ids = self._cr.dictfetchall()
                    if len(default_filter_ids):
                        if isinstance(default_filter_ids[0],dict):
                            
                            for data in default_filter_ids:
                                for record in self.env[field_model].sudo().search([]):
                                    new_record_list.append({'field_id': data.get('field_id'),
                                                            'company_id': data.get('company_id'),
                                                            'value': data.get('value'),
                                                            'record':record.name,
                                                            'rec_id':record.id})

                            if com_dep_field.ttype == 'many2one':
                                field_model_name = com_dep_field.relation
                                for model_data in new_record_list:
                                    record = model_data.get('value')
                                    if record:
                                        # Use Search to feach record details
                                        record_id = self.env[field_model_name].sudo().search([('id','=',record)])
                                        if record_id:
                                            model_data.update({'value':record_id.display_name})

                            if com_dep_field.ttype == 'selection':
                                field_model_name = com_dep_field.relation
                                for model_data in new_record_list:
                                    record_value = model_data.get('value')
                                    new_value = get_selection_label(self.env[field_model],field_model,field_name,record_value)
                                    model_data.update({'value':new_value})

                                                            
                    if new_record_list:
                        query = self.dict_to_insert_query('company_property_values_report',new_record_list)

        else:
            for model in self.model_ids:
                for com_dep_field in self.field_ids.filtered(lambda x:x.model_id == model):
                    field_name = com_dep_field.name
                    field_model = com_dep_field.model
                    record_ids = self.env[field_model].sudo().search([])
                    for record_val in record_ids:
                        if com_dep_field.ttype == 'many2one':
                            data = [{'field_id' : com_dep_field.id,
                                     'record' : record_val.display_name,
                                     'rec_id' : record_val.id,
                                     'value' : record_val[field_name].display_name,
                                     }]

                        elif com_dep_field.ttype == 'selection':
                            new_value = get_selection_label(self.env[field_model],field_model,field_name,record_val[field_name])
                            data = [{'field_id' : com_dep_field.id,
                                     'record' : record_val.display_name,
                                     'rec_id' : record_val.id,
                                     'value' : new_value,
                                     }]

                        else:
                            data = [{'field_id' : com_dep_field.id,
                                     'record' : record_val.display_name,
                                     'rec_id' : record_val.id,
                                     'value' : record_val[field_name],
                                     }]

                        query = self.dict_to_insert_query('company_property_values_report',data)

                    # model_name = model.model.replace('.', '_')
                    # query = """ SELECT
                    #                     field.id AS field_id,
                    #                     {model_name}.name AS record,
                    #                     {model_name}.id AS rec_id,
                    #                     {model_name}.{field_name} AS value
                    #                 FROM 
                    #                     {model_name}
                    #                 LEFT JOIN 
                    #                     ir_model_fields field on field.name = '{field_name}'
                    #                 """.format(model_name=model_name,field_name=field_name,field_model=field_model)

                    # print(query)
                    # self._cr.execute(query)
                    # filter_ids = self._cr.dictfetchall()
                    # if len(filter_ids):
                    #     if isinstance(filter_ids[0],dict):
                    #         for data in filter_ids:
                    #             data_record = self.env[model.model].sudo().search([('id','=',data.get('rec_id'))])
                    #                 if data_record:
                    #                     data.update({'record':data_record.display_name})

                    #     query = self.dict_to_insert_query('company_property_values_report',filter_ids)


                    
            


    # Calling report method
    def retrieve_company_property_tree_report(self):
        self.action_create_table_data()
        view_id = self.env.ref("company_property_values.company_property_values_report_view_tree_view").id,
        action = {
            'name': _("Company Property Values"),
            'type': 'ir.actions.act_window',
            'res_model': 'company.property.values.report',
            'view_mode': 'list',
            'view_type': 'list,pivot',
            'view_id': view_id,
            'views': [[view_id, 'list'],[False, 'pivot']],
            'domain': [('field_id.model','in',self.model_ids.mapped('model'))],
            'target': 'current',
            # 'context': context,
            }
        return action

    def retrieve_company_property_xlsx_report(self):
        self.action_create_table_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Company Property Values")
        worksheet.freeze_panes(2,1)
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

        worksheet.write(1, 1, "Model Name",column_heading_style)        
        worksheet.write(1, 2, "Field Name",column_heading_style)
        worksheet.write(1, 3, "Record",column_heading_style)
        worksheet.write(1, 4, "Company",column_heading_style)
        worksheet.write(1, 5, "Value",column_heading_style)
        row = 2
        for pro_val in self.env['company.property.values.report'].search([('field_id.model_id','in',self.model_ids.ids)]):
            worksheet.write(row, 1, pro_val.field_id.model_id.name,  left_alignment)
            worksheet.write(row, 2, pro_val.field_id.field_description,  left_alignment)
            worksheet.write(row, 3, pro_val.record,  left_alignment)
            worksheet.write(row, 4, pro_val.company_id.name,  left_alignment)
            worksheet.write(row, 5, pro_val.value,  left_alignment)
            row+=1
        
        worksheet.set_column(0, 0, 2)  # Column A   
        worksheet.set_column(1, 1, 5)  # Column B
        worksheet.set_column(1, 2, 30)  # Column C
        worksheet.set_column(1, 3, 30)  # Column D
        worksheet.set_column(1, 4, 30)  # Column E
        worksheet.set_column(1, 5, 30)  # Column F
        
        workbook.close()
        output.seek(0)

        file_name = 'Company Property Values.xlsx'
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': file_name,
            'res_model': 'company.property.values.report.wizard',
            'res_id': self.id,
        })

        # Return the action to download the report
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}'.format(attachment_id.id),
            'target': 'self',
            }