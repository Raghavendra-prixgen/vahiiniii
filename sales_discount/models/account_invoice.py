from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError


class AccountMoveReversal(models.TransientModel): 
    _inherit = 'account.move.reversal'

    def reverse_moves(self, is_modify=False):
        action = super().reverse_moves(is_modify)

        move_ids = []
        if action.get('res_id'):
            move_ids.append(action['res_id'])
        elif action.get('domain'):
            # Ensure the domain has the expected structure: [('id', 'in', [ids])]
            domain = action['domain']
            if isinstance(domain, list) and domain and domain[0][0] == 'id' and domain[0][1] == 'in':
                move_ids.extend(domain[0][2])

        if move_ids:
            new_moves = self.env['account.move'].browse(move_ids)
            discount_lines = new_moves.line_ids.filtered(lambda l: l.y_is_discount_record)
            discount_lines.unlink()

        return action


class AccountInvoice(models.Model):
    _inherit="account.move"

    #establishing relationship with account discount line to display the page.
    y_invoice_dis_line_ids = fields.One2many('account.discount.line', 'y_invoice_categ_dis_id', string='Discount Lines', copy=False, auto_join=True)
    y_tot_inv_discount_amt = fields.Float("Total Discount Amount",compute='_update_tot_inv_amount',store=True)
    y_cal_done = fields.Boolean(string="Calculation Done",default=False)
    y_account_enty_id = fields.Many2one("account.move", readonly='1',string="Discount Entry")
    
    @api.depends("invoice_line_ids.y_total_discount_amt")
    def _update_tot_inv_amount(self):
        for each_in in self:
            each_in.y_tot_inv_discount_amt = sum(each_in.invoice_line_ids.mapped('y_total_discount_amt'))

    def update_disc_line(self):
        for each_dis in self.y_invoice_dis_line_ids:
            curr_cate_ids = filter(lambda x: x.y_category_id.id == each_dis.y_category.id, self.invoice_line_ids)
            each_dis.update({'y_amount':sum([each_line.price_unit * each_line.quantity for each_line in curr_cate_ids])})
            for categ in self.y_invoice_dis_line_ids:
                for order in self.invoice_line_ids:
                    if order.y_category_id.id == categ.y_category.id:
                        tot_discount_amt = 0.0
                        sub_tot = order.price_unit * order.quantity
                        tot_discount_amt = (categ.y_total_discount_amount/ categ.y_amount ) *sub_tot if categ.y_amount > 0 else 0
                        order.y_total_discount_amt = tot_discount_amt

                        order.y_trade_discounts = categ.y_trade_discounts
                        order.y_quantity_discount = categ.y_quantity_discount
                        order.y_special_discount = categ.y_special_discount
                        
                        final_discount= (tot_discount_amt / sub_tot ) * 100 if sub_tot > 0 else 0
                        # do not uncomment the below code
                        # order.discount = round(final_discount,2)
                        order.y_trade_discount_amt = (categ.y_trade_amount / categ.y_amount ) * sub_tot if categ.y_amount > 0 else 0
                        order.y_quantity_discount_amt = (categ.y_quantity_amount / categ.y_amount ) * sub_tot if categ.y_amount > 0 else 0
                        order.y_specual_discount_amt = (categ.y_special_amount / categ.y_amount ) * sub_tot if categ.y_amount > 0 else 0
            
            
    def merge_product_discount(self):
        if self.y_cal_done == False:
            for line in self.invoice_line_ids.filtered(lambda x:x.product_id):
                if not line.y_stock_move_id and line.product_id.type != 'consu' and line.product_id.is_storable:
                    raise UserError(_("kindly  select the Picking Id from Get Picking button"))
            self.update_disc_line()
                    
            # new_lines = []
            # inv_tot_special_dis_amt = sum([x.y_specual_discount_amt for x in self.invoice_line_ids])
            # inv_tot_trade_dis_amt = sum([x.y_trade_discount_amt for x in self.invoice_line_ids])
            # inv_tot_quantity_dis_amt = sum([x.y_quantity_discount_amt for x in self.invoice_line_ids])
            # sale_discount_obj = self.env['sale.discount']
            # company_id = self.company_id.id
            # if self.company_id.sudo().parent_id:
            #     company_id = self.company_id.sudo().parent_id.id
            # trade_sales_discount_id = sale_discount_obj.search([('y_discount_type','=','trade'),('y_company_id','=',company_id)])
            # special_sales_discount_id = sale_discount_obj.search([('y_discount_type','=','special'),('y_company_id','=',company_id)])
            # quantity_sales_discount_id = sale_discount_obj.search([('y_discount_type','=','quantity'),('y_company_id','=',company_id)])

            # self.line_ids.filtered(lambda x:x.display_type == 'discount' and x.y_is_discount_record == True).unlink()
            
            # if inv_tot_special_dis_amt:
            #         new_lines.append((0,0,{
            #             'account_id':special_sales_discount_id.y_account_id.id,
            #             'name':special_sales_discount_id.y_name,
            #             'debit':inv_tot_special_dis_amt,
            #             'balance': inv_tot_special_dis_amt if inv_tot_special_dis_amt > 0 else abs(inv_tot_special_dis_amt),
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))
            # if inv_tot_trade_dis_amt:
            #         new_lines.append((0,0,{
            #             'account_id':trade_sales_discount_id.y_account_id.id,
            #             'name':trade_sales_discount_id.y_name,
            #             'debit':inv_tot_trade_dis_amt,
            #             'balance': inv_tot_trade_dis_amt if inv_tot_trade_dis_amt > 0 else abs(inv_tot_trade_dis_amt),
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))

            # if inv_tot_quantity_dis_amt:
            #         new_lines.append((0,0,{
            #             'account_id':quantity_sales_discount_id.y_account_id.id,
            #             'name':quantity_sales_discount_id.y_name,
            #             'debit':inv_tot_quantity_dis_amt ,
            #             'balance': inv_tot_quantity_dis_amt if inv_tot_quantity_dis_amt > 0 else abs(inv_tot_quantity_dis_amt),
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))
            
            # journal_line_ids = self.invoice_line_ids.mapped('account_id')
            # for each_account in journal_line_ids:
            #     current_journal_ids = self.invoice_line_ids.filtered(lambda x: x.account_id.id == each_account.id) 
            #     inv_tot_trade_dis_amt_journal = round(sum([x.y_trade_discount_amt for x in current_journal_ids]),2)
            #     inv_tot_special_dis_amt_journal = round(sum([x.y_specual_discount_amt for x in current_journal_ids]),2)
            #     inv_tot_quantity_dis_amt_journal = round(sum([x.y_quantity_discount_amt for x in current_journal_ids]),2)

            #     if inv_tot_trade_dis_amt_journal:
            #         new_lines.append((0,0,{
            #             'account_id':each_account.id,
            #             'name':'',
            #             'credit':inv_tot_trade_dis_amt_journal,
            #             'balance': -(inv_tot_trade_dis_amt_journal) if inv_tot_trade_dis_amt_journal > 0 else inv_tot_trade_dis_amt_journal,
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))
            #     if inv_tot_special_dis_amt_journal:
            #         new_lines.append((0,0,{
            #             'account_id':each_account.id,
            #             'name':'',
            #             'credit':inv_tot_special_dis_amt_journal,
            #             'balance': -(inv_tot_special_dis_amt_journal) if inv_tot_special_dis_amt_journal > 0 else inv_tot_special_dis_amt_journal,
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))
            #     if inv_tot_quantity_dis_amt_journal:
            #         new_lines.append((0,0,{
            #             'account_id':each_account.id,
            #             'name':'',
            #             'credit':inv_tot_quantity_dis_amt_journal,
            #             'balance': -(inv_tot_quantity_dis_amt_journal) if inv_tot_quantity_dis_amt_journal > 0 else inv_tot_quantity_dis_amt_journal,
            #             'y_is_discount_record': True,
            #             'display_type': 'discount',
            #             }))

            # # import pdb;
            # # pdb.set_trace()

            # if new_lines:
            #     self.line_ids = new_lines
            self.y_cal_done = True

    def action_post(self):
        if sum([x.y_total_discount_amount for x in self.y_invoice_dis_line_ids]) != 0.0 and self.y_cal_done != True and self.move_type == 'out_invoice':
            raise UserError(_('Discount calculation is not done'))
        return super(AccountInvoice,self).action_post()

    def write(self,vals):
        if 'invoice_line_ids' in vals:
            vals.update({'y_cal_done':False})
        return super().write(vals)

class AccountInvoiceLine(models.Model):
    _inherit ="account.move.line"

    y_trade_discount_amt = fields.Float("Trade Discount Amount")
    y_trade_discounts = fields.Float(string='Trade Discount (%)',digits=(12,3), default=0.0)
    
    y_specual_discount_amt = fields.Float("Special Discount Amount")
    y_special_discount = fields.Float(string='Special Discount (%)', digits=(12,3), default=0.0)

    y_quantity_discount_amt = fields.Float("Quantity Discount Amount")
    y_quantity_discount = fields.Float(string='Quantity Discount (%)', digits=(12,3), default=0.0)

    y_alt_uom = fields.Many2one('uom.uom',string='Alt.Uom',readonly=True,related="product_id.product_tmpl_id.y_alternate_uom",store=True)

    y_category_id = fields.Many2one('item.group',string="Item Category",compute='get_group_id',store=True)
    y_total_discount_amt = fields.Float("Total Discount Amount")
    y_is_discount_record = fields.Boolean("Is a discount")

    @api.depends('product_id')
    def get_group_id(self):
        for each in self:
            if each.product_id.y_item_group.id:
                each.y_category_id = each.product_id.y_item_group.id
            else:
                each.y_category_id = False

class SaleOrderNew(models.Model):
    _inherit = "sale.order.line"

    @api.depends('qty_delivered_method', 'analytic_line_ids.so_line', 'analytic_line_ids.unit_amount', 'analytic_line_ids.product_uom_id')
    def _compute_qty_delivered(self):
        for rec in self:
            res = super(SaleOrderNew,self)._compute_qty_delivered()
            if rec.qty_delivered > rec.product_uom_qty or rec.qty_invoiced > rec.product_uom_qty:
                raise ValidationError(_("""Delivery Qty Is More Than Order Qty"""))
                
    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'untaxed_amount_to_invoice')
    def _get_invoice_qty(self):
        for rec in self:
            res = super(SaleOrderNew,self)._get_invoice_qty()
            if rec.qty_delivered > rec.product_uom_qty or rec.qty_invoiced > rec.product_uom_qty:
                raise ValidationError(_("""Invoice Qty Is More Than Delivery Qty"""))