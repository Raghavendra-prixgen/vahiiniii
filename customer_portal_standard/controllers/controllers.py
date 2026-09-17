from odoo import fields, http, _
from odoo.http import request,Response
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
from datetime import datetime
import json

class CustomerPortal(CustomerPortal):

    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo()

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['draft','sent'])
        ]
     
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = SaleOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/quotes",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'date': date_begin,
            'quotations': quotations.sudo(),
            'page_name': 'quote',
            'pager': pager,
            'default_url': '/my/quotes',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'quotation_count': quotation_count,
        })
        values.update({'quot_create':True})
        return request.render("sale.portal_my_quotations", values)

    @http.route(['/quotes/new/view',], type='http', auth="user", website=True)
    def portal_create_quotes(self):
        user_id = http.request.env.uid
        name = request.env.user.partner_id.name
        address = request.env.user.partner_id.contact_address_complete
        # product = request.env['product.product'].sudo().search([('sale_ok','=',True)])
        
        group_product_variant = request.env['ir.config_parameter'].sudo().get_param('group_product_variant', False)
        print("group_product_variant---------------------",group_product_variant)
        
        products = request.env["product.product"].sudo()
        
        if not group_product_variant:
            products = products.search([
                ("sale_ok", "=", True),
                ('product_tmpl_id.y_product_portal_boolean', '=', True)
            ])
        else:
            products = products.search([
                ("sale_ok", "=", True),
                ('y_product_portal_boolean', '=', True)
            ])
        
        return request.render('customer_portal_standard.quotation_form',{'name':name,
                                                                'address':address,
                                                                'product':products,
                                                                'date':datetime.now().date()})

    @http.route('/get_template_lines', type='json', auth='user')
    def get_template_lines(self, **kwargs):        
        template_id = None
        product_id_ref = None
        if kwargs.get('template_id'):
            template_id = kwargs.get('template_id')
        if kwargs.get('product_id_ref'):
            product_id_ref = kwargs.get('product_id_ref')
        try:
            if template_id:
                template = request.env['sale.order.template'].sudo().browse(int(template_id))
                lines_data = []
                if template.exists():
                    for line in template.sale_order_template_line_ids:
                        product = line.product_id
                        taxes = product.taxes_id

                        # Calculate the total tax amount
                        tax_amount = 0
                        if taxes:
                            tax_result = taxes.compute_all(
                                price_unit=product.list_price,  
                                quantity=line.product_uom_qty,  
                                product=product,               
                            )
                            # Sum the tax amounts
                            tax_amount = sum(tax['amount'] for tax in tax_result['taxes'])

                        # Fetch product packaging details
                        packaging = product.packaging_ids
                        packaging_data = []
                        for package in packaging:
                            packaging_data.append({
                                'id' : package.id,
                                'name': package.name,
                                'qty': package.qty,  
                            })

                        # Add all data to lines_data
                        lines_data.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'quantity': line.product_uom_qty,
                            'uom': line.product_uom_id.name,
                            'price': product.list_price,
                            'tax_name': taxes.mapped('name'),
                            'tax_amount': tax_amount,  
                            'packaging': packaging_data,
                        })
                print('lines_data:', lines_data)
                return lines_data  

            if product_id_ref:

                product_packaging = request.env['product.packaging'].sudo().search([('product_id', '=', int(product_id_ref))])          
                result = [
                    {'id': pkg.id, 'name': pkg.name, 'qty': pkg.qty}
                    for pkg in product_packaging
                ]
                return result                

        except Exception as e:
            print('Error in get_template_lines:', str(e))
            return []  

    @http.route(['/post/data'], type='http', auth="user",csrf=False ,website=True)
    def get_product_details(self,**kw):
        product_list = json.loads(kw.get('product'))
        if request.httprequest.method == 'POST':
            if product_list:
                promise = self.Create_quotation(product_list)
                if promise:
                    return Response("Quotation Created Successfully",content_type='text/html;charset=utf-8',status=200)
        return Response("Cant able to create Quotation!",content_type='text/html;charset=utf-8',status=400)

    # def Create_quotation(self, vals):
    #     customer_id = http.request.env.uid
    #     sale = {}
    #     if vals:            
    #         if customer_id:
    #             customer_id = int(customer_id)
    #             user = request.env['res.users'].browse(customer_id)

    #             quotation_id = next((line.get('quotation_id') for line in vals if 'quotation_id' in line), False)

    #             if quotation_id:
    #                 sale_id = request.env['sale.order'].sudo().browse(quotation_id)
    #                 sale_id.write({
    #                     'partner_id': user.partner_id and user.partner_id.id,
    #                     'partner_invoice_id': user.partner_id and user.partner_id.id,
    #                     'partner_shipping_id': user.partner_id and user.partner_id.id,
    #                     'state': 'draft',
    #                     'signature': False
    #                 })

    #                 for line in vals:
    #                     if line.get('product_tmpl_id'):
    #                         sale_line = request.env['sale.order.line'].sudo().search([('order_id', '=', sale_id.id), ('product_id', '=', int(line.get('product_tmpl_id')))], limit=1)
    #                         if sale_line:
    #                             sale_line.write({
    #                                 'product_uom_qty': line.get('quantity'),
    #                                 'discount': 0.0,
    #                                 'tax_id': [(6, 0, [tax.id for tax in sale_line.product_id.taxes_id if tax.type_tax_use == 'sale'])]
    #                             })
    #                         else:
    #                             # Creating new sale order line
    #                             prod_prod = request.env['product.product'].sudo().search([('id', '=', int(line.get('product_tmpl_id')))], limit=1)
    #                             sale_line_vals = {
    #                                 'name': prod_prod.product_tmpl_id.name,
    #                                 'product_id': prod_prod.id,
    #                                 'product_uom_qty': line.get('quantity'),
    #                                 'state': 'sent',
    #                                 'discount': 0.0,
    #                                 'tax_id': [(6, 0, [tax.id for tax in prod_prod.taxes_id if tax.type_tax_use == 'sale'])],
    #                                 'order_id': sale_id.id
    #                             }
    #                             request.env['sale.order.line'].sudo().create(sale_line_vals)
    #             else:
                    
    #                 # Create a new sale order record
    #                 sale = {
    #                     'partner_id': user.partner_id and user.partner_id.id,
    #                     'partner_invoice_id': user.partner_id and user.partner_id.id,
    #                     'partner_shipping_id': user.partner_id and user.partner_id.id,
    #                     'state': 'draft',
    #                     'signature': False
    #                 }
    #                 sale_id = request.env['sale.order'].sudo().create(sale)
                    

    #                 # Create new sale order lines
    #                 for line in vals:
    #                     if line.get('product_tmpl_id'):
    #                         prod_prod = request.env['product.product'].sudo().search([('id', '=', int(line.get('product_tmpl_id')))], limit=1)
    #                         sale_line_vals = {
    #                             'name': prod_prod.product_tmpl_id.name,
    #                             'product_id': prod_prod.id,
    #                             'product_uom_qty': line.get('quantity'),
    #                             'product_packaging_qty': line.get('packaging_qty'),
    #                             'product_packaging_id': line.get('packaging_id'),
    #                             'state': 'sent',
    #                             'discount': 0.0,
    #                             'tax_id': [(6, 0, [tax.id for tax in prod_prod.taxes_id if tax.type_tax_use == 'sale'])],
    #                             'order_id': sale_id.id
    #                         }
    #                         request.env['sale.order.line'].sudo().create(sale_line_vals)

    #     return True
    def Create_quotation(self, vals):
        customer_id = http.request.env.uid
        if not vals or not customer_id:
            return False

        user = request.env['res.users'].browse(customer_id)
        grouped_lines_by_company = {}

        y_deliver_to = next((val.get('y_delivered_to') for val in vals if 'y_delivered_to' in val), None)

        # 1. Group product lines by y_company_id from product's category
        for line in vals:
            product_tmpl_id = line.get('product_tmpl_id')
            if not product_tmpl_id:
                continue  # Skip if product ID is missing

            product = request.env['product.product'].sudo().browse(int(product_tmpl_id))

            category_company = product.categ_id.y_company_id

            if not category_company:
                continue  # Skip if no company is set on category

            company_id = category_company.id
            grouped_lines_by_company.setdefault(company_id, []).append((product, line))

        # 2. For each company, create a quotation in that company's environment
        for company_id, product_lines in grouped_lines_by_company.items():
            sale_vals = {
                'partner_id': user.partner_id.id,
                'partner_invoice_id': user.partner_id.id,
                'partner_shipping_id': user.partner_id.id,
                'company_id': company_id,
                'state': 'draft',
                'signature': False,
                'y_delivered_to': y_deliver_to,

            }
            sale_order = request.env['sale.order'].sudo().with_company(company_id).create(sale_vals)

            # 3. Create order lines
            for product, line in product_lines:
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'name': product.product_tmpl_id.name,
                    'product_uom_qty': line.get('quantity'),
                    'product_packaging_qty': line.get('packaging_qty'),
                    'product_packaging_id': line.get('packaging_id'),
                    'discount': 0.0,
                    'tax_id': [(6, 0, [tax.id for tax in product.taxes_id if tax.type_tax_use == 'sale'])],
                    'state': 'sent',
                }
                request.env['sale.order.line'].sudo().with_company(company_id).create(line_vals)

        return True


    @http.route(['/get/tax'], type='http', auth="user",csrf=False ,website=True)
    def get_product_tax(self,**kw):
        product_dict= json.loads(kw.get('product'))
        if request.httprequest.method == 'POST' and product_dict:
            product_id = product_dict[0].get('product_id')
            product_qty= product_dict[0].get('quantity')
            partner_obj = request.env.user.partner_id
            currency_obj = request.env.company.currency_id
            product_obj = request.env['product.product'].sudo().search([('product_tmpl_id','=',(product_id))])
            if product_obj and product_qty:
                price_tax = 0.0
                price_total = 0.0
                price_subtotal = 0.0
                price = float(product_obj.product_tmpl_id.list_price if product_obj.product_tmpl_id.list_price else 0.0)
                taxes_obj = product_obj.product_tmpl_id.taxes_id
                for itm in taxes_obj:
                    if itm.company_id.id == request.env.company.id:
                        taxes = itm.compute_all(price, currency_obj, float(product_qty), product=product_obj, partner=partner_obj)
                        price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                price_total = price_tax + price
                price_subtotal = price * float(product_qty)
                values = json.dumps({'price_tax':price_tax,
                                     'price_subtotal':price_subtotal,
                                     'price_total':price_total})
                return Response(values,content_type='text/html;charset=utf-8',status=200)
            else:
                return Response("Values Missing",content_type='text/html;charset=utf-8',status=203)

    @http.route(['/get/tax/list'], type='http', auth="user",csrf=False ,website=True)
    def get_product_tax_list(self,**kw):
        product_id = kw.get('tmpl_id')
        if request.httprequest.method == 'POST' and product_id:
            product_taxes = request.env['product.product'].sudo().search([('id','=',product_id)])
            taxes_id = product_taxes.taxes_id
            tax_d = {}
            for tax in taxes_id:
                if tax.amount_type == 'group':
                    amount = sum(tax.children_tax_ids.mapped('amount'))
                    tax_d.update({tax.name:amount})
                else:
                    tax_d.update({tax.name:tax.amount})

            json_dict = json.dumps(tax_d)
            return json_dict

    
    @http.route('/get_product_taxes', type='json', auth='user')
    def get_product_taxes(self, **kw):
        product_id = kw.get('product_id')
        print("product_id",product_id)
        try:
            if product_id:
                # Get product and its taxes
                product = request.env['product.product'].sudo().browse(int(product_id))
                if not product.exists():
                    return {'success': False, 'error': 'Product not found'}

                # Get tax rates
                taxes = []
                for tax in product.taxes_id:
                    taxes.append({
                        'rate': tax.amount,
                        'name': tax.name
                    })

                return [{
                    'success': True,
                    'taxes': taxes
                }]
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
        