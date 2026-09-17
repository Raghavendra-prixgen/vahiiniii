from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.tools import date_utils, groupby as groupbyelem
from operator import itemgetter

class SaleDocType(models.Model):
    _inherit = 'sale.doc.type'

    y_is_dicount_calculation = fields.Boolean(string="Is Discount Calculated",tracking=True,copy=False)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    y_discount_line_ids = fields.One2many('sale.discount.lines', 'y_sale_discount_id', string=' Discount Lines', copy=True, auto_join=True)
    y_gross_amount = fields.Monetary(string='Gross Amount', store=True, readonly=True,compute='_tot_gross_amt') 
    y_cal_done = fields.Boolean(string="Calculation Done",default=False,copy=False)
    y_total_discount_amt = fields.Monetary(string='Discount Amount', store=True,compute='_tot_discount_amount')
    y_round_off_value = fields.Monetary(store=True,compute='_amount_all_dis', string='Round off Amount')
    y_discount_note = fields.Char("Note")
    y_is_cancel_invisible = fields.Boolean(compute='_compute_is_cancel_invisible')

    @api.depends('order_line.qty_delivered','order_line.qty_invoiced')
    def _compute_is_cancel_invisible(self):
        for rec in self:
            rec.y_is_cancel_invisible = False
            if any(rec.order_line.mapped('qty_delivered')) > 0:
                rec.y_is_cancel_invisible = True
                break
            if any(rec.order_line.mapped('qty_invoiced')) > 0:
                rec.y_is_cancel_invisible = True
                break

    def check_order_discount(self):
        for order in self:
            categ_lines = order.y_discount_line_ids.filtered('y_manual')
            for each in order.order_line:
                if each.discount > 0 and each.y_discount_amount > 0:
                    each.discount = 0.0
                    each.y_discount_amount = 0.0
            categ_grouped = order.get_product_discount_values()
            for lines in categ_grouped.values():
                categ_lines += categ_lines.new(lines)
            order.y_discount_line_ids = categ_lines
    
    def write(self,vals):
        for rec in self:
            if vals.get('order_line') or vals.get('y_discount_line_ids'):
                vals.update({'y_cal_done':False})
        res = super(SaleOrder,self).write(vals) 
        for order in self:
            self.ensure_one()
            if order.state == 'sale':
                if vals.get('order_line') or vals.get('y_discount_line_ids'):
                    order.merge_product_discount()       
        return res


    @api.depends('order_line.price_total')
    def _amount_all_dis(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            totalamt  = order.amount_untaxed + order.amount_tax
            rounded_total = round(order.amount_untaxed,2) + order.amount_tax
            curr_round_off_value = round(rounded_total -totalamt ,2)
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'y_round_off_value': curr_round_off_value,
                'amount_total':  abs(rounded_total),
            })


    #Compute the gross total amounts of the all the products and display in Sales order main form.
    @api.depends('order_line.product_uom_qty','order_line.price_unit')
    def _tot_gross_amt(self):
        for order in self:
            order.y_gross_amount = sum([line.product_uom_qty * line.price_unit for line in order.order_line])
            
    @api.depends("order_line.y_discount_amount")
    def _tot_discount_amount(self):
        for order in self:
            order.y_total_discount_amt = round(sum(order.order_line.mapped('y_discount_amount')),2)

    #Combining the categories to group and moving them to discount tab
    @api.onchange('order_line')
    def _create_discount_ids(self):
        for l in self:
            categ_lines = l.y_discount_line_ids.filtered('y_manual')
            for each in self.order_line:
                if each.discount > 0 and each.y_discount_amount > 0:
                    each.discount = 0.0
                    each.y_discount_amount = 0.0
            categ_grouped = l.get_product_discount_values()
            for lines in categ_grouped.values():
                categ_lines += categ_lines.new(lines)
            l.y_discount_line_ids = categ_lines

    @api.onchange('y_doc_type_id')
    def _update_discount_ids(self): 
        for each in self:
            each.check_order_discount()
            doc_type_id = each.y_doc_type_id or each._origin.y_doc_type_id
            for each_discount in each.y_discount_line_ids:
                if not each.partner_id.y_price_group_id:
                    raise UserError(_('Price Group is not mapped to %s.', each.partner_id.name))
                curr_ds_id = self.env['discount.structure'].search([('y_doc_type_id','=',doc_type_id.id),('y_price_id','=',each.partner_id.y_price_group_id.id),('y_item_group_id','=',each_discount.y_category.id)])
                if not curr_ds_id and doc_type_id.y_is_dicount_calculation:
                    raise UserError(_('%s is not mapped in the discount structure .', each_discount.y_category.y_name))
                discount_structure_id = self.env['discount.structure'].search([('y_doc_type_id','=',doc_type_id.id),('y_price_id','=',each.partner_id.y_price_group_id.id),('y_item_group_id','=',each_discount.y_category.id),('y_end_date','>=',each.date_order.date()),('y_start_date','<=',each.date_order.date())])
                if discount_structure_id:
                    each_discount.write({
                        'y_trade_discounts': discount_structure_id.y_trade_discounts,
                        'y_quantity_discount': discount_structure_id.y_qty_disc,
                        'y_special_discount': discount_structure_id.y_spec_discount,
                        })
                else:
                    raise UserError("Discount Structure Not Avilable for '{}'".format(doc_type_id.y_name))

    
    def get_product_discount_values(self):
        categ_grouped = {}
        for line in self.order_line:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            categ = line.y_item_group.compute_all_prod_discount(price_unit, self.currency_id, line.product_uom_qty, line.product_id, self.partner_id)['categ']
            for categ_line in categ:
                val = self._prepare_categ_line_vals(line, categ_line)
                key = self.env['item.group'].browse(categ_line['id']).get_grouping_key_categ(val)
                if key not in categ_grouped:
                    categ_grouped[key] = val
                else:
                    categ_grouped[key]['y_amount'] += val['y_amount']
        return categ_grouped
    
    def _prepare_categ_line_vals(self, line, categ_line):
        # sale_discount_obj = self.env['sale.discount']
        company_id = self.company_id.id
        if self.company_id.sudo().parent_id:
            company_id = self.company_id.sudo().parent_id.id
        # trade_id = sale_discount_obj.search([('y_discount_type','=','trade'),('y_company_id','=',company_id)],limit=1)
        # special_id = sale_discount_obj.search([('y_discount_type','=','special'),('y_company_id','=',company_id)],limit=1)
        # quatity_id = sale_discount_obj.search([('y_discount_type','=','quantity'),('y_company_id','=',company_id)],limit=1)
        # if not trade_id:
        #     raise UserError(_('Please define  Trade Discount in the Discount Masters'))
        # if not special_id:
        #     raise UserError(_('Please define  Special Discount in the Discount Masters'))
        # if not quatity_id:
        #     raise UserError(_('Please define  Quantity Discount in the Discount Masters'))
        if not self.partner_id.y_price_group_id and self.y_doc_type_id.y_is_dicount_calculation:
            raise UserError(_('Price Group is not mapped to %s.', self.partner_id.name))
        
        if self.partner_id.y_price_group_id and self.y_doc_type_id.y_is_dicount_calculation and self.date_order and line.y_item_group:
            discount_structure_id = self.env['discount.structure'].search([('y_doc_type_id','=',self.y_doc_type_id.id),('y_price_id','=',self.partner_id.y_price_group_id.id),('y_item_group_id','=',line.y_item_group.id),('y_end_date','>=',self.date_order.date()),('y_start_date','<=',self.date_order.date())])
            if not  discount_structure_id:
                raise UserError(_(' No Records Found for %s,%s,%s,%s in Discount Structure',self.partner_id.y_price_group_id.y_name,self.y_doc_type_id.y_name,line.y_item_group.y_name,self.date_order.date()))

        vals = {
            'y_sale_discount_id': self.id,
            'y_category': categ_line['id'],
            # 'y_quantity_discount_id': quatity_id.id,
            'y_trade_discounts': discount_structure_id.y_trade_discounts if self.y_doc_type_id.y_is_dicount_calculation and discount_structure_id else 0.0,
            'y_quantity_discount': discount_structure_id.y_qty_disc if self.y_doc_type_id.y_is_dicount_calculation and  discount_structure_id else 0.0,
            'y_special_discount': discount_structure_id.y_spec_discount if self.y_doc_type_id.y_is_dicount_calculation and discount_structure_id else 0.0,
            # 'y_special_discount_id': special_id.id,
            # 'y_trade_discount_id': trade_id.id,
            'sequence': categ_line['sequence'],
            'y_manual': False,
            'y_amount': categ_line['y_amount'],
    
        }

        return vals

    def _create_invoices(self, grouped=False, final=False, date=None):
        rec = super(SaleOrder, self)._create_invoices()
        if self.y_discount_line_ids:
            grouped_disc_lines  = [g for k, g in groupbyelem(self.y_discount_line_ids, itemgetter('y_category'))]
            for each in grouped_disc_lines:
                if len(set([x.y_trade_discounts for x in each])) > 1 or len(set([x.y_quantity_discount for x in each])) > 1 or len(set([x.y_special_discount for x in each])) > 1:
                    raise UserError(_('There should uniq discount for the category'))

            for each_discount in grouped_disc_lines:
                curr_so_ids = rec.invoice_line_ids.filtered(lambda line:  line.y_category_id.id == each_discount[0].y_category.id)
                amount = sum([x.quantity * x.price_unit for x in curr_so_ids])
                discount_obj=self.env['account.discount.line']
                curr_vals ={    
                            "y_category": each_discount[0].y_category.id,
                            "y_amount": round(amount,2),
                            "y_trade_discounts": each_discount[0].y_trade_discounts,
                            "y_quantity_discount": each_discount[0].y_quantity_discount,
                            "y_special_discount": each_discount[0].y_special_discount,
                            "y_invoice_categ_dis_id": rec.id
                             }
                discount_obj.create(curr_vals)
        return rec

    def update_disc_line(self):
        for sale in self:
            for each_dis in sale.y_discount_line_ids:
                curr_cate_ids = filter(lambda x: x.y_item_group.id == each_dis.y_category.id, sale.order_line)
                each_dis.update({'y_amount':sum([each_line.price_unit * each_line.product_uom_qty for each_line in curr_cate_ids])})

    #adding the total value of discount to the sale order line and the calculation is made on each line.
    def merge_product_discount(self):
        self.y_cal_done = False
        if not self.y_doc_type_id:
            raise UserError("Document Type Required for Calculate Discount.")
        self.update_disc_line()
        for categ in self.y_discount_line_ids:
            for order in self.order_line:
                if order.y_item_group.id == categ.y_category.id:
                    total_discount_amt = 0.0
                    final_discount = 0.0
                    sub_tot = 0.0
                    sub_tot = round(order.price_unit*order.product_uom_qty,4)
                    total_discount_amt = (categ.y_total_discount_amount/ round(categ.y_amount,2) ) * sub_tot if categ.y_amount > 0 else 0
                    order.y_discount_amount = total_discount_amt
                    final_discount= round((total_discount_amt/sub_tot)*100,4) if sub_tot > 0 else 0
                    order.discount =  final_discount
                    order.y_trade_amount =   round(categ.y_trade_amount/ categ.y_amount * sub_tot,4) if categ.y_amount > 0 else 0
                    order.y_quantity_discount =  round(categ.y_quantity_amount/ categ.y_amount * sub_tot,4) if categ.y_amount > 0 else 0
                    order.y_special_amount =  round(categ.y_special_amount/ categ.y_amount * sub_tot,4) if categ.y_amount > 0 else 0
           
            if sum([x.y_total_discount_amount for x in self.y_discount_line_ids]) == 0.0:
                categ.y_sale_discount_id.y_discount_note = "No Discount found"
            else:
                categ.y_sale_discount_id.y_discount_note = " "
            order.order_id._compute_amounts()
        self.y_cal_done = True

    def action_confirm(self):
        if sum([x.y_total_discount_amount for x in self.y_discount_line_ids]) != 0.0 and self.y_cal_done != True:
            raise UserError(_('Discount calculation is not done'))
        return super(SaleOrder,self).action_confirm()

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    y_trade_amount = fields.Float('Trade Disc(₹)', digits=(12,2), default=0.0,store=True)
    y_quantity_discount = fields.Float(string='Quantity Disc(%)', digits=(12,2), default=0.0)
    y_special_amount = fields.Float('Special Disc(₹)', digits=(12,2), default=0.0,store=True)
    y_alt_uom = fields.Many2one('uom.uom',string='Alt.Uom',readonly=True,related="product_id.product_tmpl_id.y_alternate_uom",store=True)
    y_discount_amount = fields.Float(string='Discount Amount',digits=(12,4))

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['y_trade_discount_amt'] = self.y_trade_amount
        res['y_specual_discount_amt'] =  self.y_special_amount
        res['y_quantity_discount_amt'] = self.y_quantity_discount
        res['y_category_id'] = self.y_item_group.id
        return res
