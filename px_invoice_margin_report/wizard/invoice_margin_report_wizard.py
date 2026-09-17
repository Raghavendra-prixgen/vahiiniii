from odoo import models, fields, api
import xlsxwriter
import io
import base64

class InvoiceMarginReportWizard(models.TransientModel):
    _name = 'invoice.margin.report.wizard'
    _description = 'Invoice Margin Report Wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    company_ids = fields.Many2many('res.company', string="Companies", required=True,
                                    default=lambda self: self.env.company)
    # Generate Excell View
    def action_generate_invoice_margin_report(self):
        for company in self.company_ids:
            invoices = self.env['account.move'].search([
                ('invoice_date', '>=', self.from_date),
                ('invoice_date', '<=', self.to_date),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice'),
                ('company_id', '=', company.id),
            ])
            invoice_line_data = {}
            transportation_cost = 0.00
            # Process each invoice
            for inv in invoices:
                for line in inv.invoice_line_ids:
                    if not line.y_stock_move_id:
                        continue
                    line_transportation_cost = 0
                    # Convert the invoiced amount to Company Currency if the currency is not Company Currency
                    invoiced_amount_inr = line.price_subtotal
                    if inv.currency_id.id != inv.company_currency_id.id and line.price_subtotal != 0:
                        invoiced_amount_inr = (
                                    line.price_subtotal / line.currency_rate) if line.currency_rate != 0 else line.price_subtotal
                    # Calculate COGS
                    cogs_lines = self.env['account.move.line'].search([
                        ('product_id', '=', line.product_id.id),
                        ('move_id', '=', inv.id),
                        ('cogs_origin_id', '=', inv.id),
                        ('account_id', '=', line.product_id.categ_id.property_account_expense_categ_id.id)
                    ])
                    total_cogs = sum(cogs_line.debit - cogs_line.credit for cogs_line in cogs_lines)

                    # Calculate Transportation Cost
                    transportation_orders = self.env['transportation.order.intent.line'].search(
                        [('y_picking_id', '=', line.y_stock_move_id.picking_id.id)]
                    )
                    if transportation_orders:
                        total_cost = sum(transportation_orders.y_transportation_order_id.mapped(
                            'y_transportation_costing_ids.y_cost'))
                    else:
                        total_cost = 0

                    if total_cost:
                        total_weight = sum([line.quantity * line.product_id.weight for line in inv.invoice_line_ids])
                        if total_weight > 0:
                            line_transportation_cost = round(((line.product_id.weight * line.quantity) * total_cost) / total_weight)


                    # transportation_cost = sum(
                    #     order.y_transportation_order_id.y_transportation_costing_ids.amount_untaxed for order in
                    #     transportation_orders)

                    # Prepare invoice line data
                    invoice_line_id = line.id
                    invoice_line_data[invoice_line_id] = {
                        'product_id': line.product_id.name,
                        'product_code': line.product_id.default_code if line.product_id.default_code else '',
                        'product_categ_id': line.product_id.categ_id.name if line.product_id.categ_id.name else '',
                        'invoice_id': inv.name,
                        'y_account_id': line.y_account_id.name,
                        'invoice_date': inv.invoice_date,
                        'partner_id': inv.partner_id.name,
                        'partner_categ': inv.partner_id.y_partner_category.y_name if inv.partner_id.y_partner_category.y_name else '',
                        'payment_term_id': inv.invoice_payment_term_id.name if inv.invoice_payment_term_id.name else '',
                        # 'delivery_terms': inv.y_delivery_terms,
                        'invoiced_qty': line.quantity,
                        'invoiced_amount': invoiced_amount_inr,
                        'cogs': total_cogs,
                        'transportation_cost': line_transportation_cost,
                        'return_qty': 0,
                        'return_amount': 0,
                        'sales_person': inv.invoice_user_id.name,
                        'company': company.name,
                    }
                    if line.y_stock_move_id.returned_move_ids:
                        reversed_qty = 0
                        reversed_amount = 0
                        for move in line.y_stock_move_id.returned_move_ids:
                            if move.state == 'done':  # Only process moves in done state
                                reversed_qty += move.quantity
                                # Aggregate over all account move lines for this move
                                if inv.currency_id.id != inv.company_currency_id.id and line.price_subtotal != 0:
                                    for inv_line in move.y_account_move_line_ids:
                                        if inv_line.currency_rate != 0:
                                            reversed_amount += inv_line.price_subtotal / inv_line.currency_rate
                                        else:
                                            reversed_amount += inv_line.price_subtotal
                                else:
                                    reversed_amount += sum(move.y_account_move_line_ids.mapped('price_subtotal'))

                        invoice_line_data[invoice_line_id]['return_qty'] = reversed_qty
                        invoice_line_data[invoice_line_id]['return_amount'] = reversed_amount

        # Create an Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Lot Products Report")
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '666666',  # Green background
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'})
        header_format_1 = workbook.add_format({     # for table head
            'bold': True,'font_color': 'white',
            'bg_color': '666666',  # Green background
            'font_size': 12,'align': 'center', 'valign': 'vcenter'})
        header_format_2 = workbook.add_format({      # for from and to date
            'bold': True,
            'font_color': 'black',
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter'})
        sl_format_2 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter'})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})  # Date format in Excel
        number_format = workbook.add_format({'align': 'right','num_format': '0.000'})  # Number format in Excel
        worksheet.merge_range('A1:T2', 'Invoice Margin Analysis Report', header_format)  # Merge cells B1 to L2 for title
        worksheet.write('B4', 'Date From',header_format_2)  # From Date
        worksheet.write('C4', self.from_date ,date_format)
        worksheet.write('E4', 'Date To',header_format_2) # To Date
        worksheet.write('F4', self.to_date,date_format)
        # Define the headers
        headers = ['Sl No','Invoice #','Invoice Date', 'Customer', 'Partner Category', 'Product Code','Product', 'Product Category','Payment Term','Delivery Term','Invoiced Qty', 'Price/Unit', 'Invoiced Amount', 'COGS', 'Transport Cost','Return Amount', 'GM', 'GM(%)','Salesperson','Company']
        worksheet.set_column(5, 0, 8)  # Column A: 'Sl No' - 10 characters wise
        worksheet.set_column(5, 1, 15)  # Column B: 'Invoice #' - 20 characters wise
        worksheet.set_column(5, 2, 15)  # Column C: 'Invoice Date' - 20 characters wise
        worksheet.set_column(5, 3, 30)  # Column D: 'Customer' - 30 characters wide
        worksheet.set_column(5, 4, 25)  # Column E: 'Partner Category' - 35 characters wise
        worksheet.set_column(5, 5, 15)  # Column F: 'Product Code' - 15 characters wise
        worksheet.set_column(5, 6, 40)  # Column G: 'Product' - 35 characters wise
        worksheet.set_column(5, 7, 20)  # Column H: 'Product Category' - 15 characters wise
        worksheet.set_column(5, 8, 15)  # Column I: 'Payment Term' - 15 characters wise
        worksheet.set_column(5, 9, 15)  # Column J: 'Delivery Term' - 15 characters wise
        worksheet.set_column(5, 10, 15)  # Column K: 'Invoiced Qty' - 15 characters wise

        worksheet.set_column(5, 11, 12)  # Column L: 'Price PU' - 12 characters wise
        worksheet.set_column(5, 12, 12)  # Column M: 'Invoiced Amount' - 15 characters wise

        worksheet.set_column(5, 13, 12)  # Column N: 'COGS' - 12 characters wide
        worksheet.set_column(5, 14, 13)  # Column O: 'Transportation Cost' - 19 characters wide
        worksheet.set_column(5, 15, 13)  # Column P: 'Return Value' - 15 characters wide
        worksheet.set_column(5, 16, 12)  # Column Q: 'GM' - 12 characters wide
        worksheet.set_column(5, 17, 12)  # Column R: 'GM %' - 12 characters wide
        worksheet.set_column(5, 18, 15)  # Column S: 'Salesperson' - 15 characters wide
        worksheet.set_column(5, 19, 25)  # Column T: 'Company' - 25 characters wide
        worksheet.write_row(5, 0, headers, header_format_1)
        # Write the data
        col_num = 0    # Set for column number
        sl_no = 0      # Set for serial number
        row = 6
        for invoice_line_id, data in invoice_line_data.items():
            margin = round(data['invoiced_amount'] - data['cogs']-data['transportation_cost']-data['return_amount'], 3)
            margin_percentage = round((margin / data['invoiced_amount'] * 100), 3) if data['invoiced_amount'] else 0
            sale_price_per_unit = round(data['invoiced_amount']/data['invoiced_qty'] ,3)
            worksheet.write(row, col_num, sl_no+1,sl_format_2)
            worksheet.write(row, col_num+1, data['invoice_id'])
            worksheet.write(row, col_num+2, data['invoice_date'])
            worksheet.write(row, col_num+3, data['partner_id'])
            worksheet.write(row, col_num+4, data['partner_categ'])
            worksheet.write(row, col_num+5, data['product_code'])
            worksheet.write(row, col_num+6, data['product_id'])
            worksheet.write(row, col_num+7, data['product_categ_id'])
            worksheet.write(row, col_num+8, data['payment_term_id'])
            worksheet.write(row, col_num+9, data['delivery_terms'])
            worksheet.write(row, col_num+10, data['invoiced_qty'],sl_format_2)
            worksheet.write(row, col_num+11, sale_price_per_unit, number_format)
            worksheet.write(row, col_num+12, data['invoiced_amount'], number_format)
            worksheet.write(row, col_num+13, data['cogs'], number_format)
            worksheet.write(row, col_num+14, data['transportation_cost'], number_format)
            worksheet.write(row, col_num+15, data['return_amount'], number_format)
            worksheet.write(row, col_num+16, margin, number_format)
            worksheet.write(row, col_num+17, margin_percentage, number_format)
            worksheet.write(row, col_num+18, data['sales_person'])
            worksheet.write(row, col_num+19, data['company'])
            sl_no += 1
            row += 1

        workbook.close()
        output.seek(0)

        # Create an attachment to download the report
        file_name = f'Invoice Margin Report{self.from_date}_{self.to_date}.xlsx'
        attachment_id = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': file_name,
            'res_model': 'invoice.margin.report.wizard',
            'res_id': self.id,
        })

        # Return the action to download the report
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}'.format(attachment_id.id),
            'target': 'self',
        }

    # Generate Tree View
    def action_view_invoice_margin_report(self):
        self.env['invoice.margin.report.line'].search([]).unlink()
        # Initialize the cursor
        for company in self.company_ids:
            invoices = self.env['account.move'].search([
                ('invoice_date', '>=', self.from_date),
                ('invoice_date', '<=', self.to_date),
                ('state', '=', 'posted'),
                ('y_btb_id','=',False),
                ('move_type', '=', 'out_invoice'),
                ('company_id', '=', company.id),
            ])
            invoice_line_data = {}
            transportation_cost = 0.00
            # Process each invoice
            for inv in invoices:
                for line in inv.invoice_line_ids:
                    if not line.y_stock_move_id:
                        # Convert the invoiced amount to Company Currency if the currency is not Company Currency
                        invoiced_amount_inr = line.price_subtotal
                        if inv.currency_id.id != inv.company_currency_id.id and line.price_subtotal != 0:
                            invoiced_amount_inr = (
                                        line.price_subtotal / line.currency_rate) if line.currency_rate != 0 else line.price_subtotal
                        # Calculate COGS
                        cogs_lines = inv.line_ids.filtered(lambda x:x.cogs_origin_id.id == line.id and x.account_id.id == line.product_id.categ_id.property_account_expense_categ_id.id)
                        total_cogs = sum(cogs_line.debit - cogs_line.credit for cogs_line in cogs_lines)
                        invoice_line_id = line.id
                        invoice_line_data[invoice_line_id] = {
                            'y_weight': line.product_id.weight,
                            'product_id': line.product_id.id,
                            'product_code': line.product_id.default_code,
                            'product_categ_id': line.product_id.categ_id.id,
                            'invoice_id': inv.id,
                            'y_account_id': line.account_id.id,
                            'invoice_date': inv.invoice_date,
                            'y_product_group_1': line.product_id.y_product_group_1.id,
                            'y_product_group_2': line.product_id.y_product_group_2.id,
                            'y_product_group_3': line.product_id.y_product_group_3.id,
                            # 'y_manufacturer_name_id': line.product_id.y_manufacturer_name_id.id,
                            # 'y_family_desc_id': line.product_id.y_family_desc_id.id,
                            # 'y_group_desc_id': line.product_id.y_group_desc_id.id,
                            # 'y_subgroup_desc_id': line.product_id.y_subgroup_desc_id.id,
                            # 'y_gsr_type_id': line.product_id.y_gsr_type_id.id,
                            # 'y_producer_name_id': line.product_id.y_producer_name_id.id,
                            'y_currency_id': line.currency_id.id,
                            'y_invoice_currency_rate': line.currency_rate,
                            'y_location_id': False,
                            'y_lot_ids': False,
                            'y_lot_create_date': False,
                            'y_lr_number': False,
                            'y_lr_date': False,
                            'partner_id': inv.partner_id.id,
                            'partner_categ': inv.partner_id.y_partner_category.id,
                            'payment_term_id': inv.invoice_payment_term_id.id,
                            # 'delivery_terms': line.y_stock_move_id.picking_id.y_delivery_terms,
                            'invoiced_qty': line.quantity,
                            'invoiced_amount': invoiced_amount_inr,
                            'cogs': total_cogs,
                            'transportation_cost': 0,
                            'return_qty': 0,
                            'return_amount': 0,
                            'sales_person': inv.invoice_user_id.id,
                            'company': company.id,
                        }
                    else:
                        line_transportation_cost = 0
                        # Convert the invoiced amount to Company Currency if the currency is not Company Currency
                        invoiced_amount_inr = line.price_subtotal
                        if inv.currency_id.id != inv.company_currency_id.id and line.price_subtotal !=0:
                            invoiced_amount_inr = (line.price_subtotal / line.currency_rate) if line.currency_rate != 0 else line.price_subtotal
                        # Calculate COGS
                        cogs_lines = inv.line_ids.filtered(lambda x:x.cogs_origin_id.id == line.id and x.account_id.id == line.product_id.categ_id.property_account_expense_categ_id.id)
                        total_cogs = sum(cogs_line.debit - cogs_line.credit for cogs_line in cogs_lines)


                        # Calculate Transportation Cost
                        transportation_orders = self.env['transportation.order.intent.line'].search(
                            [('y_picking_id', '=', line.y_stock_move_id.picking_id.id)]
                        )
                        if transportation_orders:
                            total_cost = sum(transportation_orders.y_transportation_order_id.mapped(
                                'y_transportation_costing_ids.y_cost'))
                        else:
                            total_cost = 0

                        if total_cost:
                            total_weight = sum([line.quantity * line.product_id.weight for line in transportation_orders.y_transportation_order_id.y_invoice_ids.filtered(lambda x:x.state == 'posted').invoice_line_ids])
                            if total_weight > 0:
                                line_transportation_cost = round(((line.product_id.weight * line.quantity) * total_cost) / total_weight)



                        # # Calculate Transportation Cost
                        # transportation_orders = self.env['transportation.order.intent.line'].search(
                        #     [('y_picking_id', '=', line.y_stock_move_id.picking_id.id),('y_transportation_order_id.y_state','!=','draft')]
                        # )
                        # account_move_new_obj = transportation_orders.y_transportation_order_id.y_invoice_ids
                        # if len(account_move_new_obj) >1:
                        #     if transportation_orders:
                        #         total_cost = sum(transportation_orders.y_transportation_order_id.mapped('y_transportation_costing_ids.y_cost'))
                        #     else:
                        #         total_cost = 0

                        #     if total_cost:
                        #         total_quantity = sum(account_move_new_obj.invoice_line_ids.mapped('quantity'))
                        #         if total_quantity != 0:
                        #             line_transportation_cost = (line.quantity*total_cost)/total_quantity

                        # else:
                        #     if transportation_orders:
                        #         total_cost = sum(transportation_orders.y_transportation_order_id.mapped('y_transportation_costing_ids.y_cost'))
                        #     else:
                        #         total_cost = 0

                        #     if total_cost:
                        #         total_quantity = sum(inv.invoice_line_ids.mapped('quantity'))
                        #         if total_quantity != 0:
                        #             line_transportation_cost = round((line.quantity*total_cost)/total_quantity)

                        # transportation_cost = sum(
                        #     order.y_transportation_order_id.y_purchase_order_id.amount_untaxed for order in transportation_orders)

                        # Prepare invoice line data
                        invoice_line_id = line.id
                        invoice_line_data[invoice_line_id] = {
                            'y_weight': line.product_id.weight * line.quantity,
                            'product_id': line.product_id.id,
                            'product_code': line.product_id.default_code,
                            'product_categ_id': line.product_id.categ_id.id,
                            'invoice_id': inv.id,
                            'y_account_id': line.account_id.id,
                            'invoice_date': inv.invoice_date,
                            'y_product_group_1': line.product_id.y_product_group_1.id,
                            'y_product_group_2': line.product_id.y_product_group_2.id,
                            'y_product_group_3': line.product_id.y_product_group_3.id,
                            # 'y_manufacturer_name_id': line.product_id.y_manufacturer_name_id.id,
                            # 'y_family_desc_id': line.product_id.y_family_desc_id.id,
                            # 'y_group_desc_id': line.product_id.y_group_desc_id.id,
                            # 'y_subgroup_desc_id': line.product_id.y_subgroup_desc_id.id,
                            # 'y_gsr_type_id': line.product_id.y_gsr_type_id.id,
                            # 'y_producer_name_id': line.product_id.y_producer_name_id.id,
                            'y_currency_id': line.currency_id.id,
                            'y_invoice_currency_rate': line.currency_rate,
                            'y_location_id': line.y_stock_move_id.location_id.id,
                            'y_lot_ids': line.y_stock_move_id.lot_ids.ids,
                            'y_lot_create_date': line.y_stock_move_id.lot_ids.create_date if len(line.y_stock_move_id.lot_ids) == 1 else False,
                            'y_lr_number': line.y_stock_move_id.picking_id.y_lr_number,
                            'y_lr_date': line.y_stock_move_id.picking_id.y_lr_date,
                            'partner_id': inv.partner_id.id,
                            'partner_categ': inv.partner_id.y_partner_category.id,
                            'payment_term_id': inv.invoice_payment_term_id.id,
                            # 'delivery_terms': line.y_stock_move_id.picking_id.y_delivery_terms,
                            'invoiced_qty': line.quantity,
                            'invoiced_amount': invoiced_amount_inr,
                            'cogs': total_cogs,
                            'transportation_cost': line_transportation_cost,
                            'return_qty': 0,
                            'return_amount': 0,
                            'sales_person': inv.invoice_user_id.id,
                            'company': company.id,
                        }
                        if line.y_stock_move_id.returned_move_ids:
                            reversed_qty = 0
                            reversed_amount = 0
                            for move in line.y_stock_move_id.returned_move_ids:
                                if move.state == 'done':  # Only process moves in done state
                                    reversed_qty += move.quantity
                                    # Aggregate over all account move lines for this move
                                    move_amount = 0
                                    for account_move_line in move.y_account_move_line_ids:
                                        line_amount = account_move_line.price_subtotal

                                        # Handle currency conversion if needed
                                        if inv.currency_id.id != inv.company_currency_id.id and line.price_subtotal != 0:
                                            if account_move_line.currency_rate != 0:
                                                line_amount = account_move_line.price_subtotal / account_move_line.currency_rate
                                            else:
                                                line_amount = account_move_line.price_subtotal
                                        move_amount += line_amount
                                    reversed_amount += move_amount
                            invoice_line_data[invoice_line_id]['return_qty'] = reversed_qty
                            invoice_line_data[invoice_line_id]['return_amount'] = reversed_amount

            # # Write to `invoice.margin.report.line`
            for invoice_line_id, data in invoice_line_data.items():
                margin = round(data['invoiced_amount'] - data['cogs'] - data['return_amount'],3)
                # if data['delivery_terms'] != 'to_pay':
                #     margin = margin - data['transportation_cost']

                margin_2 = round(data['invoiced_amount'] - data['cogs'] - data['transportation_cost'] - data['return_amount'],3) 

                margin_percentage = round((margin / data['invoiced_amount'] * 100), 3) if (data['invoiced_amount'] != 0 and margin != 0)  else 0

                margin2_percentage = round((margin_2 / data['invoiced_amount'] * 100), 3) if (data['invoiced_amount'] != 0 and margin_2 != 0)  else 0

                price_per_unit = round(data['invoiced_amount'] / data['invoiced_qty'], 3) if (data['invoiced_qty'] !=0 and data['invoiced_amount'] != 0) else 0
                self.env['invoice.margin.report.line'].create({
                    'y_weight': data['y_weight'],
                    'y_product_id': data['product_id'],
                    'y_account_id': data['y_account_id'],
                    'y_product_code': data['product_code'],
                    'y_product_categ_id': data['product_categ_id'],
                    'y_invoice_id': data['invoice_id'],
                    'y_invoice_date': data['invoice_date'],
                    'y_partner_id': data['partner_id'],
                    'y_partner_categ_id': data['partner_categ'],
                    'y_product_group_1': data['y_product_group_1'],
                    'y_product_group_2': data['y_product_group_2'],
                    'y_product_group_3': data['y_product_group_3'],
                    # 'y_manufacturer_name_id': data['y_manufacturer_name_id'],
                    # 'y_family_desc_id': data['y_family_desc_id'],
                    # 'y_group_desc_id': data['y_group_desc_id'],
                    # 'y_subgroup_desc_id': data['y_subgroup_desc_id'],
                    # 'y_gsr_type_id': data['y_gsr_type_id'],
                    # 'y_producer_name_id': data['y_producer_name_id'],
                    'y_currency_id': data['y_currency_id'],
                    'y_invoice_currency_rate': data['y_invoice_currency_rate'],
                    'y_location_id': data['y_location_id'],
                    'y_lot_ids': data['y_lot_ids'],
                    'y_lot_create_date': data['y_lot_create_date'],
                    'y_lr_number': data['y_lr_number'],
                    'y_lr_date': data['y_lr_date'],
                    'y_payment_term_id': data['payment_term_id'],
                    # 'y_delivery_terms': data['delivery_terms'],
                    'y_invoiced_qty': data['invoiced_qty'],
                    'y_invoiced_amount': data['invoiced_amount'],
                    'y_unit_price': price_per_unit,
                    'y_cogs': data['cogs'],
                    'y_transportation_cost': data['transportation_cost'],
                    'y_return_amount': data['return_amount'],
                    'y_return_qty': data['return_qty'],
                    'y_margin': margin,
                    'y_margin_percentage': margin_percentage,
                    'y_margin_2': margin_2,
                    'y_margin2_percentage': margin2_percentage,
                    'y_sales_person_id': data['sales_person'],
                    'y_company_id': data['company'],
                })
        tree_view_id = self.env.ref('px_invoice_margin_report.view_invoice_margin_report_line_tree').id
        y_start_date = self.from_date.strftime('%d-%m-%Y')
        y_end_date = self.to_date.strftime('%d-%m-%Y')
        return {
            'name': 'Invoice Margin Report ({} To {}) '.format(y_start_date, y_end_date),
            'view_mode': 'list,pivot',
            'views': [[tree_view_id, 'list']],
            'res_model': 'invoice.margin.report.line',
            'type': 'ir.actions.act_window',
            'target': 'current', }