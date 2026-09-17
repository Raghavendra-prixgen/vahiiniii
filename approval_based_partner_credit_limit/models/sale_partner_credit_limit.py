from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError
from datetime import datetime, timedelta,date
import pytz
from markupsafe import Markup
from odoo.tools import html2plaintext

class ResPartner(models.Model):
    _inherit = "res.partner"

    y_payment_term = fields.Integer('Additional Credit Days',tracking=True)

def get_selection_label(self, object, field_name, field_value):
    return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])

class UserApprovalCode(models.Model):
    _inherit = 'user.approval.code'

    def unlink(self):
        domain = [('y_lvl_user_id','=',self.id)]
        existing_ids = self.env['credit.sale.order.approval.lvlsamt'].search(domain)
        if existing_ids:
            raise ValidationError("Once the approval code is used, it cannot be deleted.")
        return super().unlink()

    def write(self,vals):
        if vals.get('y_code'):
            domain = [('y_lvl_user_id','=',self.id)]
            existing_ids = self.env['credit.sale.order.approval.lvlsamt'].search(domain)
            if existing_ids:
                raise ValidationError("Once the approval code is used, it cannot be modified.")
        return super().write(vals)
    
class CreditSaleAppproval(models.Model):
    _name = "credit.sale.approval"
    _description ="Sale Approval"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'y_name'

    active = fields.Boolean(default=True)
    y_name = fields.Char("Name")
    y_document_type_id = fields.Many2one("sale.doc.type","Document Type",tracking=True)
    y_lvl_amt_approval_lines = fields.One2many("credit.sale.lvlamt.approval","y_lvl_approval_id",tracking=True)
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    y_parent_company_id = fields.Many2one(related="y_company_id.parent_id")
    y_currency_id = fields.Many2one('res.currency',string='Currency',tracking=True)

    @api.constrains('y_name','y_company_id','active')
    def check_sale_approval_name(self):
        for rec in self:
            docs = rec.env['credit.sale.approval'].search([('y_name','=',rec.y_name),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""name already exists!"""))

    @api.constrains('y_currency_id','active','y_company_id','y_document_type_id')
    def _check_duplicate(self):
        domain = [('y_document_type_id','=',self.y_document_type_id.id),('y_currency_id','=',self.y_currency_id.id),('y_company_id','=',self.y_company_id.id)]
        existing_ids = self.env['credit.sale.approval'].search(domain)
        if len(existing_ids) > 1:
            raise UserError (_("Oops, looks like we've got a duplicate record!"))

    @api.onchange('y_document_type_id','y_currency_id')
    def _update_name(self):
        if self.y_document_type_id:
            name = self.y_document_type_id.y_name
            if self.y_currency_id:
                name = name + ' ' + '({})'.format(self.y_currency_id.name)
            self.y_name = name


    def write(self,vals):
        new_dist = []
        if vals.get('y_lvl_amt_approval_lines'):
            new_list = []
            for list1 in vals.get('y_lvl_amt_approval_lines'):
                if list1[-1] != False:
                    new_list.append(list1)
                    approval_lvlamt_line_ids = self.y_lvl_amt_approval_lines.filtered(lambda x:x.id in [value[1] for value in new_list])
                    new_dist = []
                    for dicts in approval_lvlamt_line_ids:
                        for newval in new_list:
                            if not isinstance(newval[-1],int):
                                if newval[1] == dicts.id:
                                    if newval[-1].get('y_approval_level'):
                                        # new_approval_level = newval[-1].get('y_approval_level')
                                        new_approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',newval[-1].get('y_approval_level'))
                                        old_approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',dicts.y_approval_level)
                                        new_dist.append('{}{} ---> {}'.format("Approval Level : ",old_approval_level,new_approval_level))
                                    if newval[-1].get('y_approval_amount_from'):
                                        new_quantity = newval[-1].get('y_approval_amount_from')
                                        new_dist.append('{}{} ---> {}'.format("Amount(From) : ",dicts.y_approval_amount_from,new_quantity))
                                    if newval[-1].get('y_approval_amount_to'):
                                        new_quantity = newval[-1].get('y_approval_amount_to')
                                        new_dist.append('{}{} ---> {}'.format("Amount(To) : ",dicts.y_approval_amount_from,new_quantity))
                                    if newval[-1].get('y_lvl1_user_id'):
                                        new_product_id = self.env['user.approval.code'].search([('id','=',newval[-1].get('y_lvl1_user_id'))])
                                        new_dist.append('{}{}--->{}'.format("Level 1 Code :",dicts.y_lvl1_user_id.y_code,new_product_id.y_code))

                                    if newval[-1].get('y_lvl2_user_id'):
                                        new_product_id = self.env['user.approval.code'].search([('id','=',newval[-1].get('y_lvl2_user_id'))])
                                        new_dist.append('{}{}--->{}'.format("Level 2 Code :",dicts.y_lvl2_user_id.y_code,new_product_id.y_code))

                                    if newval[-1].get('y_lvl3_user_id'):
                                        new_product_id = self.env['user.approval.code'].search([('id','=',newval[-1].get('y_lvl3_user_id'))])
                                        new_dist.append('{}{}--->{}'.format("Level 3 Code :",dicts.y_lvl3_user_id.y_code,new_product_id.y_code))

                                    if newval[-1].get('y_lvl4_user_id'):
                                        new_product_id = self.env['user.approval.code'].search([('id','=',newval[-1].get('y_lvl4_user_id'))])
                                        new_dist.append('{}{}--->{}'.format("Level 4 Code :",dicts.y_lvl4_user_id.y_code,new_product_id.y_code))

                                    if newval[-1].get('y_lvl5_user_id'):
                                        new_product_id = self.env['user.approval.code'].search([('id','=',newval[-1].get('y_lvl5_user_id'))])
                                        new_dist.append('{}{}--->{}'.format("Level 5 Code :",dicts.y_lvl5_user_id.y_code,new_product_id.y_code))

            if new_dist:
                msg = ', '.join(dic for dic in new_dist)
                if self.env.user:
                    self.message_post(body=msg)                
        
        return super().write(vals)
            
class SalesLevelAmountApproval(models.Model):
    _name = "credit.sale.lvlamt.approval"
    _description = "Sale Lvl&Amt Approval"

    y_approval_level = fields.Selection(selection=[
            ('1stlvlapproval', '1'),
            ('2ndlvlapproval', '2'),
            ('3rdlvlapproval', '3'),
            ('4thlvlapproval', '4'),
            ('5thlvlapproval', '5'),
            ],string='Approval Level',copy=False)
    y_lvl1_user_id = fields.Many2one("user.approval.code",string="Level 1 Code",domain="[('y_model_ids.model','=','sale.order')]")
    y_lvl2_user_id = fields.Many2one("user.approval.code",string="Level 2 Code",domain="[('y_model_ids.model','=','sale.order')]")
    y_lvl3_user_id = fields.Many2one("user.approval.code",string="Level 3 Code",domain="[('y_model_ids.model','=','sale.order')]")
    y_lvl4_user_id = fields.Many2one("user.approval.code",string="Level 4 Code",domain="[('y_model_ids.model','=','sale.order')]")
    y_lvl5_user_id = fields.Many2one("user.approval.code",string="Level 5 Code",domain="[('y_model_ids.model','=','sale.order')]")
    y_approval_amount_from = fields.Float("Amount(From)")
    y_approval_amount_to = fields.Float("Amount(To)")
    y_lvl_approval_id = fields.Many2one('credit.sale.approval',string="Lvl and Approval")


    @api.constrains('y_approval_amount_from','y_approval_amount_to')
    def approval_lvl_amount_number(self):
        filterd_ids = self.y_lvl_approval_id.y_lvl_amt_approval_lines
        for record in filterd_ids:
            if record != filterd_ids[0]:
                filterd_line_ids = filterd_ids.mapped('id')
                approval_line_id = record.env['credit.sale.lvlamt.approval'].browse(filterd_line_ids[filterd_line_ids.index(record.id)-1])
                if record.y_approval_amount_from <= approval_line_id.y_approval_amount_to:
                    raise UserError(_("Amount From({}) should be greater than previous record Amount To({})".format(record.y_approval_amount_from,approval_line_id.y_approval_amount_to)))
        for rec in self:
            if rec.y_approval_amount_to <= rec.y_approval_amount_from:
                raise UserError(_("Amount To ({}) is less than Amount From ({})".format(rec.y_approval_amount_to,rec.y_approval_amount_from)))

    @api.onchange('y_approval_level')
    def _onchange_approval_level(self):
        for line in self:
            if line.y_approval_level == '1stlvlapproval':
                line.y_lvl2_user_id = False
                line.y_lvl3_user_id = False
                line.y_lvl4_user_id = False
                line.y_lvl5_user_id = False
            elif line.y_approval_level == '2ndlvlapproval':
                line.y_lvl3_user_id = False
                line.y_lvl4_user_id = False
                line.y_lvl5_user_id = False
            elif line.y_approval_level == '3rdlvlapproval':
                line.y_lvl4_user_id = False
                line.y_lvl5_user_id = False
            elif line.y_approval_level == '4thlvlapproval':
                line.y_lvl5_user_id = False

    @api.constrains('y_approval_level','y_lvl1_user_id','y_lvl2_user_id','y_lvl3_user_id')
    def _check_levels(self):
        for line in self:
            if line.y_approval_level == '1stlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
            if line.y_approval_level == '2ndlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))

            if line.y_approval_level == '3rdlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
            if line.y_approval_level == '4thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
            if line.y_approval_level == '5thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id and x.y_lvl5_user_id == line.y_lvl5_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'credit.sale.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    

# ===============================# Sale Approval Configuration End #===============================================================#
# =================================================================================================================================#
# ===============================#   Sale Approval in Sale Order   #===============================================================#

class CustomSaleOrder(models.Model):
    _inherit = 'sale.order'

    y_is_credit_blocked = fields.Boolean(copy=False,default=False,string="Is Credit Blocked")

    def action_check_approval_required(self):
        for sale in self:
            if self._context.get('confirm_sale_credit_approval_required'):
                activity_ids = self.activity_ids.filtered(lambda x:x.state != 'done' and x.summary == 'Sale Order Approval Request')
                user_activity_ids = activity_ids.filtered(lambda x:x.user_id == self.env.user)
                non_user_activity_ids = activity_ids.filtered(lambda x:x.user_id != self.env.user)
                user_activity_ids.action_done()
                non_user_activity_ids.action_cancel()
                return False

            is_credit_blocked = self.action_check_credit_limit()
            if is_credit_blocked:
                return is_credit_blocked

        return super().action_check_approval_required()

    def action_check_credit_limit(self):
        self.ensure_one()
        is_credit_blocked = False
        if self.partner_id.country_id and self.company_id.country_id and self.partner_id.country_id != self.company_id.country_id:
            return is_credit_blocked
        if not self.y_doc_type_id:
            raise ValidationError(_("""Mapping Document type is required to confirm a Sales Quotation"""))
        partner = self.partner_id
        partner_ids = partner + self.partner_id.sudo().child_ids
        is_due = False
        credit_amount = 0
        sale_order_details = dict()
        advance_amount_details = dict()
        due_details = dict()
        unpaid_details = dict()        
        is_partner_credit_limit = partner.sudo().with_company(self.company_id).use_partner_credit_limit
        if not is_partner_credit_limit and self.company_id.sudo().parent_id:
            is_partner_credit_limit = partner.sudo().with_company(self.company_id.sudo().parent_id).use_partner_credit_limit
        if is_partner_credit_limit:
            if self.company_id.sudo().parent_id:
                company_id = self.company_id.sudo().parent_id
            else:
                company_id = self.company_id

            company_ids = self.env['res.company']
            if self.company_id.sudo().parent_id:
                company_ids += self.company_id.sudo().parent_id.child_ids + self.company_id.sudo().parent_id
            else:
                company_ids += self.company_id + self.company_id.child_ids

            # Sum Advance
            advance_ids = self.env['account.move.line'].sudo().search([("parent_state", "=", "posted"),("partner_id", "in", partner_ids.ids),"|", "&", ("account_id.account_type", "=", "liability_payable"), ("account_id.non_trade", "=", False), "&", ("account_id.account_type", "=", "asset_receivable"), ("account_id.non_trade", "=", False),"&", ("amount_residual", "!=", 0), ("account_id.reconcile", "=", True),('company_id','in',company_ids.ids)])
            advance_amount = sum(advance_ids.filtered(lambda x:x.amount_residual < 0).mapped('amount_residual'))

            # Advance Details
            advance_move_ids = advance_ids.filtered(lambda x:x.amount_residual < 0).mapped('move_id')
            for advance_id in advance_move_ids:
                advance_line_ids = advance_ids.filtered(lambda x:x.amount_residual < 0 and x.move_id == advance_id)
                advance_amount_line_amount = sum(advance_line_ids.mapped('amount_residual'))
                advance_amount_details.update({advance_id.name:advance_amount_line_amount})

            # END

            # Sum Sale Order Amount
            confirm_sale_order_ids = self.env['sale.order'].sudo().search([('partner_id', '=', partner.id),('state', 'in', ['sale','to_approve']),('invoice_status','in',('no','to invoice')),('company_id','in',company_ids.ids)])    

            # Open Sale Orders
            amount_total = sum(confirm_sale_order_ids.filtered(lambda x:not x.invoice_ids).order_line.filtered(lambda x:x.y_is_short_close == False).mapped('price_total'))
            for sale_order in confirm_sale_order_ids.filtered(lambda x:not x.invoice_ids):
                sale_order_details.update({sale_order.name:sum(sale_order.order_line.filtered(lambda x:x.y_is_short_close == False).mapped('price_total'))})

            # Short Close Sale Orders
            short_close_ids = confirm_sale_order_ids.filtered(lambda x:not x.invoice_ids).order_line.filtered(lambda x:x.y_is_short_close)
            short_close_sale_order_ids = short_close_ids.mapped('order_id')
            short_close_remaing_amount = 0
            for short_order in short_close_sale_order_ids:
                short_value = 0 
                for short_line in short_order.order_line.filtered(lambda x:x.y_is_short_close):
                    delivered_qty = sum(short_line.move_ids.filtered(lambda x:x.state =='done').mapped('quantity'))
                    if short_line.product_uom_qty > 0:
                        short_close_remaing_amount += (short_line.price_unit * delivered_qty)
                        short_value += (short_line.price_unit * delivered_qty)
                if sale_order_details.get(short_order.name):
                    short_value += sale_order_details.get(short_order.name)
                    sale_order_details.update({short_order.name:short_value})

            nothing_invoice_amount = 0
            # Partial Invoice Orders
            invoice_sale_orders = confirm_sale_order_ids.filtered(lambda x:x.invoice_ids)
            for invoice_order in invoice_sale_orders:
                order_value = 0
                for order_line in invoice_order.order_line.filtered(lambda x:x.product_uom_qty > 0):
                    if order_line.y_is_short_close:
                        delivered_qty = sum(order_line.move_ids.filtered(lambda x:x.state =='done').mapped('quantity'))
                        nothing_invoice_amount += (order_line.price_unit * delivered_qty)
                        order_value += (order_line.price_unit * delivered_qty)
                    else:
                        if order_line.product_uom_qty > order_line.qty_invoiced and order_line.invoice_lines:
                            invoiced_qty = sum(order_line.invoice_lines.filtered(lambda x:x.parent_state == 'posted' and x.move_id.move_type == 'out_invoice').mapped('quantity')) 
                            nothing_invoice_amount += (order_line.price_unit * invoiced_qty) + (sum(order_line.invoice_lines.filtered(lambda x:x.parent_state == 'posted' and x.move_id.move_type == 'out_invoice').mapped('price_total')) - sum(order_line.invoice_lines.filtered(lambda x:x.parent_state == 'posted' and x.move_id.move_type == 'out_invoice').mapped('price_subtotal')))
                            order_value += (order_line.price_unit * invoiced_qty) + (sum(order_line.invoice_lines.filtered(lambda x:x.parent_state == 'posted' and x.move_id.move_type == 'out_invoice').mapped('price_total')) - sum(order_line.invoice_lines.filtered(lambda x:x.parent_state == 'posted' and x.move_id.move_type == 'out_invoice').mapped('price_subtotal')))
                        else:
                            if not order_line.invoice_lines:
                                nothing_invoice_amount += order_line.price_total
                                order_value += order_line.price_total
                sale_order_details.update({invoice_order.name:order_value})

            # END
            amount_total += short_close_remaing_amount
            amount_total += nothing_invoice_amount
            if self.state == 'draft':
                amount_total += self.amount_total
                sale_order_details.update({self.name:self.amount_total})
                            
            moveline_obj = self.env['account.move']
            account_move_ids = moveline_obj.sudo().search([("state", "=", "posted"),("payment_state", "in", ("not_paid", "partial")),("partner_id", "=", partner.id),("move_type", "=", "out_invoice"),('company_id','in',company_ids.ids)])
            
            # Sum Unpaid Amount
            due = sum(account_move_ids.mapped('amount_residual'))

            # Unpaid Details
            if account_move_ids:
                for move in account_move_ids:
                    unpaid_details.update({move.name:move.amount_residual})
            
            # Sum Overdue Amount
            due_total = 0.0 
            for due_line in account_move_ids:
                new_date = due_line.invoice_date_due + timedelta(days=partner.y_payment_term)
                if new_date < date.today():
                    due_total += due_line.amount_residual
                    due_details.update({due_line.name:due_line.amount_residual})

            outstanding_amount = (amount_total + due)

            if outstanding_amount > partner.with_company(company_id).credit_limit:
                if (outstanding_amount + advance_amount) > partner.with_company(company_id).credit_limit:
                    credit_amount = (outstanding_amount + advance_amount) - partner.with_company(company_id).credit_limit
                    is_credit_blocked = True
            if (due_total + advance_amount) > 0.0 and not is_credit_blocked:
                credit_amount = (due_total + advance_amount)
                is_credit_blocked = True
                is_due = True

        if is_due:
            sub_msg = "Sales Order Amount and Advance Amount Exceeds"
        else:
            sub_msg = "credit limit has been exceeds"

        if is_credit_blocked:
            body = " "            
            if sale_order_details:
                body += Markup("""
                            <strong> Confirm Sale Orders : </strong> </br>
                            """)
                for key, value in zip(sale_order_details.keys(), sale_order_details.values()):
                    body += Markup("""
                            
                                <li>
                                     <span> {key}</span> : <span>{value}</span>
                                </li>
                            
                        """).format(key=key,
                                    value=value
                                    )

            if advance_amount_details:
                body += Markup("""
                            <strong> Advances : </strong> </br>
                            """)
                for key, value in zip(advance_amount_details.keys(), advance_amount_details.values()):
                    body += Markup("""
                            
                                <li>
                                    <span>{key}</span> : <span>{value}</span>
                                </li>
                            
                        """).format(key=key,
                                    value=value
                                    )

            if unpaid_details and not is_due:
                body += Markup("""
                            <strong> Unpaid Invoices : </strong> </br>
                            """)
                for key, value in zip(unpaid_details.keys(), unpaid_details.values()):
                    body += Markup("""
                        
                           
                                <li>
                                    <span>{key}</span> : <span>{value}</span>
                                </li>
                           
                        """).format(key=key,
                                    value=value
                                    )

            if due_details and is_due:
                body += Markup("""
                            <strong> Due Invoices : </strong> </br>
                            """)
                for key, value in zip(unpaid_details.keys(), unpaid_details.values()):
                    body += Markup("""
                           
                                <li>
                                    <span>{key}</span> : <span>{value}</span>
                                </li>
                           
                        """).format(key=key,
                                    value=value
                                    )

            if self.env.user.has_group('approval_based_partner_credit_limit.group_bypass_credit_limit'):
                message = "{}' {}. To confirm the sale order, please click the 'Confirm' button.".format(self.partner_id.name,sub_msg)
            else:
                message = "'{}' {}. To request approval, please click the 'Request for Approval' button.".format(self.partner_id.name,sub_msg)


            return  {
                'name':'Confirmation',
                'type': 'ir.actions.act_window',
                'res_model':'confirm.sale.credit.approval.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('approval_based_partner_credit_limit.view_confirm_credit_sale_credit_approval_wizard_message').id,'form')],
                'target': 'new',
                'context': dict(self._context,default_y_sale_id=self.id,default_y_message_html=body,default_y_message=message,default_y_credit_amount=credit_amount)
                }
        else:
            return False
        

    def get_approval_data(self):
        for each in self:
            if not (each.y_doc_type_id and each.y_doc_type_id.y_is_approval_required == True):
                super().get_approval_data()
            else:
                check_credit_limit = self.action_check_credit_limit()
                if not check_credit_limit:
                    super().get_approval_data()
                else:
                    return check_credit_limit

    def get_credit_approval_data(self,credit_amount):
        for each in self:
            each.order_line._validate_analytic_distribution()
            if not each.order_line:
                raise ValidationError("""Order lines requried for request approval""")
            if each.y_sale_lvl_amt_approval_line.filtered(lambda x:x.y_is_approval_completed):
                raise UserError (_("Oops!!!!You cannot change the document type once approved, Kindly Reset To Quotation the SO"))
            else:
                each.y_sale_lvl_amt_approval_line = False
            
            domain = [('y_document_type_id','=',each.y_doc_type_id.id),('y_company_id','=',each.company_id.id),('y_currency_id','=',each.currency_id.id)]
            approval_ids = each.env['credit.sale.approval'].search(domain)
            if not approval_ids:
                if each.company_id.sudo().parent_id:
                    domain = ['|',('y_company_id','=',each.company_id.sudo().parent_id.id),('y_company_id','=',each.company_id.id),('y_document_type_id','=',each.y_doc_type_id.id),('y_currency_id','=',each.currency_id.id)]
                    approval_ids = each.env['credit.sale.approval'].search(domain)
            
            if not approval_ids:
                raise ValidationError("""Approvals Not Configured""")
            filtered_approval_ids = approval_ids.y_lvl_amt_approval_lines.filtered(lambda x:credit_amount >= x.y_approval_amount_from and credit_amount <= x.y_approval_amount_to)
            if filtered_approval_ids:
                level_approval_amount_obj = each.env['sale.order.approval.lvlsamt']
                for each_line in filtered_approval_ids:
                    if each_line.y_approval_level == '1stlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':each_line.y_approval_level,
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        
                    elif each_line.y_approval_level == '2ndlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        
                    elif each_line.y_approval_level == '3rdlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })     

                    elif each_line.y_approval_level == '4thlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })  

                    elif each_line.y_approval_level == '5thlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_sale_lvl_id':each.id,
                                }) 
                        level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'5thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl5_user_id.id,
                                'y_sale_lvl_id':each.id,
                                })                                
                each.y_to_approve_states = 'to_approve_state1'
            else:
                raise ValidationError("""The SO total amount is out of the Approval Grid""")

            if each.y_sale_lvl_amt_approval_line:
                each.y_is_approval_show = True
                each.write({'state':'to_approve','y_is_credit_blocked':True})

                # Activity for First Approval   
                first_approval = each.y_sale_lvl_amt_approval_line[:1]
                if first_approval:
                    res_model = self.env['ir.model'].sudo().search([('model','=',self._name)])
                    company_ids = self.company_id + self.company_id.sudo().parent_id
                    subject = 'Sale Order Approval Request'
                    user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',first_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                    for user in user_ids:
                        body = f'The "{self.env.user.name}" has requested approval for the sale quotation "{each.name}"'
                        vals={
                            'res_model_id':res_model.id,
                            'res_model':self._name,
                            'res_id':each.id,
                            'activity_type_id':first_approval.y_lvl_user_id.y_activity_type_id.id,
                            'user_id':user.id,
                            'date_deadline':date.today(),
                            'summary': subject,
                            'note': html2plaintext(body)                            
                        }
                        activity = self.env['mail.activity'].sudo().create(vals)
                # Activity END



    def confirm_approval(self):
        if self.y_is_credit_blocked:
            user = self.env.user
            for lvl_approval_lines in self.y_sale_lvl_amt_approval_line:
                if lvl_approval_lines.y_is_approval_completed == False:
                    if lvl_approval_lines.y_lvl_user_id.id in user.y_user_code_ids.ids:
                        lvl_approval_lines.write({'y_approval_status':'approved',
                                                  'y_approved_date':datetime.now(),
                                                  'y_is_approval_completed':True,
                                                  'y_approver_id':user.id,
                                                 })   

                        activity_ids = self.activity_ids.filtered(lambda x:x.state != 'done' and x.summary == 'Sale Order Approval Request')
                        user_activity_ids = activity_ids.filtered(lambda x:x.user_id == user)
                        non_user_activity_ids = activity_ids.filtered(lambda x:x.user_id != user)
                        user_activity_ids.action_done()
                        non_user_activity_ids.action_cancel()

                        if self.y_to_approve_states == 'to_approve_state1':
                            self.y_to_approve_states = 'to_approve_state2'
                            first_approval_msg = """First Approval Is Done: %s""" % (user.name)
                            self.message_post(body=first_approval_msg)
                            break

                        elif self.y_to_approve_states == 'to_approve_state2':
                            self.y_to_approve_states = 'to_approve_state3'
                            second_approval_msg = """Second Approval Is Done: %s""" % (user.name)
                            self.message_post(body=second_approval_msg)
                            break

                        elif self.y_to_approve_states == 'to_approve_state3':
                            self.y_to_approve_states = 'to_approve_state4'
                            third_approval_msg = """Third Approval Is Done: %s""" % (user.name)
                            self.message_post(body=third_approval_msg)
                            break

                        elif self.y_to_approve_states == 'to_approve_state4':
                            self.y_to_approve_states = 'to_approve_state5'
                            fourth_approval_msg = """Fourth Approval Is Done: %s""" % (user.name)
                            self.message_post(body=fourth_approval_msg)
                            break

                        elif self.y_to_approve_states == 'to_approve_state5':
                            fifth_approval_msg = """Fifth Approval Is Done: %s""" % (user.name)
                            self.message_post(body=fifth_approval_msg)
                            break
                        
                    else:
                        raise UserError (_("Oops!!!! You can't approve the order"))

            for lvl_approval_lines in self.y_sale_lvl_amt_approval_line:
                if lvl_approval_lines.y_is_approval_completed == False:
                    # Activity for Next Approval   
                    next_approval = lvl_approval_lines
                    if next_approval:
                        company_ids = self.company_id + self.company_id.sudo().parent_id
                        res_model = self.env['ir.model'].sudo().search([('model','=',self._name)])
                        subject = 'Sale Order Approval Request'
                        user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',next_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                        for user in user_ids:
                            body = f'The "{self.env.user.name}" has requested approval for the sale quotation "{self.name}"'
                            vals={
                                'res_model_id':res_model.id,
                                'res_model':self._name,
                                'res_id':self.id,
                                'activity_type_id':next_approval.y_lvl_user_id.y_activity_type_id.id,
                                'user_id':user.id,
                                'date_deadline':date.today(),
                                'summary': subject,
                                'note': html2plaintext(body)                            
                            }
                            activity = self.env['mail.activity'].sudo().create(vals)
                    # Activity END

            data = self.y_sale_lvl_amt_approval_line.mapped('y_is_approval_completed')  
            if all(data) == True:
                self.write({'y_to_approve_states':'approved',
                            })

                self.with_context(confirm_sale_credit_approval_required=True).action_confirm()
        else:
            super().confirm_approval()

    # def action_confirm(self):
    #     for sale in self:
    #         if self._context.get('confirm_sale_credit_approval_required'):
    #             if self._context.get('confirm_sale_credit_approval_required') == False:
    #                 check_credit_limit = self.action_check_credit_limit()
    #                 if not check_credit_limit:
    #                     return super(CustomSaleOrder, self).action_confirm()
    #                 else:
    #                     return check_credit_limit
    #             else:
    #                 return super(CustomSaleOrder, self).action_confirm()
    #         else:
    #             check_credit_limit = self.action_check_credit_limit()
    #             if not check_credit_limit:
    #                 return super(CustomSaleOrder, self).action_confirm()
    #             else:
    #                 return check_credit_limit
                
class ConfirmSaleCreditApprovalWizard(models.Model):
    _name = 'confirm.sale.credit.approval.wizard'
    _description = 'Confirm Credit Approval'

    y_sale_id = fields.Many2one('sale.order')
    y_message = fields.Char()
    y_message_html = fields.Html()
    y_credit_amount = fields.Float(string="Credit Amount")
    y_is_bypass_credit_limit = fields.Boolean(compute="_compute_group_bypass_credit_limit",string="Is Bypass Credit Limit")

    @api.depends('y_sale_id')
    def _compute_group_bypass_credit_limit(self):
        for wizard in self:
            wizard.y_is_bypass_credit_limit = False
            if wizard.env.user.has_group("approval_based_partner_credit_limit.group_bypass_credit_limit"):
                wizard.y_is_bypass_credit_limit = True

    def action_confirm(self):
        self.y_sale_id.y_is_credit_blocked = True
        self.y_sale_id.get_credit_approval_data(self.y_credit_amount)

    def action_sale_order_confirm(self):
        self.y_sale_id.with_context(confirm_sale_credit_approval_required=True).action_confirm()


