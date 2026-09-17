from odoo import models,tools, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from markupsafe import Markup

class RejectResons(models.TransientModel):
    _name = "reject.reason"

    y_reject_reason = fields.Char('Reject Reason')
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_purchase_account_payment_id = fields.Many2one('purchase.account.payment',string="Down Payment")

    def pass_y_reject_reason(self):
        purchase_order_obj = self.y_purchase_id
        self.y_purchase_account_payment_id.y_approved_by = self.env.user.id
        self.y_purchase_account_payment_id.write({'y_approval_status':'rejected'})        
        if purchase_order_obj:
            advance_payment_obj = self.env['purchase.account.payment'].browse(self._context.get('active_id'))
            msg = Markup("<strong>%s</strong>") % \
                    _("Down payment request has been rejected: %s",
                      advance_payment_obj.y_sequence)
            msg += Markup("<li> %s: <br/>") % _("Reject Reason: %s",
                      self.y_reject_reason)
            purchase_order_obj.message_post(body=msg)
            advance_payment_obj.y_reject_reason = self.y_reject_reason

class PaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    y_advance_request_required = fields.Boolean(string="Down Payment Request")

    @api.constrains('y_advance_request_required')
    def check_advance_request_required(self):
        for rec in self:
            value = rec.payment_id.line_ids.filtered(lambda x: x.y_advance_request_required != False)
            if len(value) > 1:
                raise UserError(_("Create Only one down payment request term"))

class AdvanceRequestApprovalForm(models.Model):
    _name = "advance.request.approval.form"
    _description = "Down Payment Request Approval Form"

    y_advance_sequence_id = fields.Many2one('ir.sequence',string="Sequence No.")
    y_company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.company.id)
    y_approval_user_ids = fields.Many2many('res.users',string="Approval User")
    active = fields.Boolean(default=True)
    y_is_approval_required = fields.Boolean(default=True,copy=False,string="Is Approval Required")

    @api.constrains('y_company_id','active')
    def check_company(self):
        for rec in self:
            docs = rec.env['advance.request.approval.form'].search([('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("Oops, looks like we've got a duplicate record!"))


class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    y_purchase_account_payment_ids = fields.One2many('purchase.account.payment','y_purchase_id',string="Purchase Account Payment Lines")
    y_is_payment_completed = fields.Boolean(copy=False,string="Payment Completed")
    y_advance_request_form_approval_id = fields.Many2one('advance.request.approval.form',string="Advance Request Approval")
    y_advace_request_count = fields.Integer(compute="get_count_advace_request_count",string="Advance Request Count")

    @api.depends('y_purchase_account_payment_ids')
    def get_count_advace_request_count(self):
        for order in self:
            order.y_advace_request_count = len(order.y_purchase_account_payment_ids)

    def purchase_account_payment_view(self):
        return  {
                "name":"Down Payment Request",
                "type": "ir.actions.act_window",
                "res_model": "purchase.account.payment",
                "view_mode":'list',
                "context":dict(y_purchase_id=self.id,create=False,edit=False),
                "domain":[('y_purchase_id','=',self.id)],
            }

    # Down Payment Request   
    def create_down_payment(self,object):
        payment_term_id = object.payment_term_id or object.partner_id.property_supplier_payment_term_id
        if not payment_term_id:
            raise UserError(_("Payment Term not Available."))

        if not payment_term_id.line_ids.filtered(lambda x:x.y_advance_request_required != False):
            raise UserError(_("Down Payment Request not Configured for '{}' Payment Term.".format(payment_term_id.name)))

        if payment_term_id.line_ids.filtered(lambda x: x.value_amount <= 0 and x.y_advance_request_required != False):
            raise UserError(_("Due should be grater than zero for '{}' Payment Term.".format(payment_term_id.name)))
        
        if  object.invoice_ids.filtered(lambda x:x.state == 'posted'):
            raise UserError(_("Once Bill has been posted, you cannot raise the down payment!"))
        
        if object.state not in ['purchase','done']:            
            raise UserError(_('Down Payment Request can be processed only if the Order is in Purchase Order or Locked State!'))
        
        domain = [('y_company_id','=',object.company_id.id)]
        advance_request_form_approval_obj = self.env['advance.request.approval.form'].search(domain,limit=1)
        if not advance_request_form_approval_obj and object.company_id.sudo().parent_id:
            domain = [('y_company_id','=',object.company_id.sudo().parent_id.id)]
            advance_request_form_approval_obj = self.env['advance.request.approval.form'].sudo().search(domain,limit=1)
        if not advance_request_form_approval_obj:
            raise UserError(_("Approval Setting Downpayment Not Configured."))

        object.y_advance_request_form_approval_id = advance_request_form_approval_obj.id
        payment_term_line_id = payment_term_id.line_ids.filtered(lambda x:x.y_advance_request_required != False)       
        
        return {
            "name":"Down Payment Request",
            "type": "ir.actions.act_window",
            "res_model": "advance.payment.wizard",
            "views": [[False, "form"]],
            "target": 'new',
            "context":dict(y_purchase_id=object.id,default_y_purchase_id=object.id,default_y_payment_term_id=payment_term_id.id,default_y_payment_term_line_id=payment_term_line_id.id),
            }


    def action_view_advance_payment(self):
        return {
                "name":"Payments",
                "type": "ir.actions.act_window",
                "res_model": "account.payment",
                "views": [[False, "list"], [False, "form"]],
                'view_id': self.env.ref('purchase_down_payment.account_payment_temp_id').id,
                "domain": [["purchase_id", "=", self.id]],
                }

    def message_chatter(self):
        display_msg = """<br>Down Payment Requested By <b>""" + str(self.partner_id.name) + """</b> at """ + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + """."""
        self.message_post(body=display_msg)
        
    def button_cancel(self):
        res = super(PurchaseOrderInherit, self).button_cancel()
        for rec in self:
            if any(rec.y_purchase_account_payment_ids.filtered(lambda x:x.y_approval_status == 'approved')):
                raise UserError("Unable to Cancel the Purchase Order, as Down Payment Request is raised against this Purchase Order")
        return res

class PurchaseAdvancePaymentWizard(models.TransientModel):
    _name = "advance.payment.wizard"
    _description = " "

    def get_amount_percentage(self):
        if self.y_purchase_id.payment_term_id:
            term_line_ids = self.y_purchase_id.payment_term_id.line_ids.filtered(lambda x:x.y_advance_request_required == True)
            if term_line_ids:
                if term_line_ids.value == 'percent':
                    return 'percentage'
                elif term_line_ids.value == 'fixed':
                    return 'amount'


    y_name = fields.Char('Name')
    y_payment_amount = fields.Float('Payment Amount')
    y_payment_status = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft', string="Payment Status")
    y_remark = fields.Text('Remark')
    y_amount_or_percentage = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], default='percentage', string=" ")
    y_percentage = fields.Float(string="Percentage")
    y_company_id = fields.Many2one('res.company', 'Company',related="y_purchase_id.company_id",readonly=True)
    y_currency_id = fields.Many2one('res.currency', string='Currency',related="y_purchase_id.currency_id")
    y_invoice_date_due = fields.Date(string='Request Date')
    y_is_payment_term_value = fields.Boolean(string="Is Payment Term Value")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_payment_term_id = fields.Many2one('account.payment.term',string="Payment Terms")
    y_payment_term_line_id = fields.Many2one('account.payment.term.line',string="Payment Term Line")

    @api.constrains('y_remark')
    def _check_remark_length(self):
        for record in self:
            if record.y_remark:
                if len(record.y_remark) > 250:
                    raise UserError (_("Length of character should be below 250 characters"))
                if len(record.y_remark.split()) > 50:
                    raise ValidationError('The remark cannot exceed 50 words.')


    @api.constrains('y_invoice_date_due')
    def _check_invoice_date_due(self):
        for record in self:
            if record.y_invoice_date_due and self.y_purchase_id.date_order:                
                if record.y_invoice_date_due < self.y_purchase_id.date_order.date():
                    raise ValidationError("Request Date cannot be earlier than the Purchase Order Date.")

    def _calculate_percent(self, y_percentage, value):
        """Calculate the percentage value."""
        return (y_percentage / 100) * value


    @api.onchange('y_amount_or_percentage')
    def _onchange_amount_or_percentage(self):
        if self.y_purchase_id and self.y_payment_term_line_id:
            if self.y_amount_or_percentage == 'amount':
                self.y_payment_amount = self._calculate_percent(self.y_payment_term_line_id.value_amount, self.y_purchase_id.amount_total)
            else:
                self.y_percentage = self.y_payment_term_line_id.value_amount
                self.y_payment_amount = self._calculate_percent(self.y_percentage, self.y_purchase_id.amount_total)
                if self.y_percentage:
                    self.y_is_payment_term_value = True

    @api.constrains('y_payment_amount')
    def _check_value(self):
        if self.y_payment_amount <= 0.0:
            raise ValidationError(_("Please Enter The Valid Amount!"))


    @api.constrains('y_payment_amount','y_purchase_id','y_amount_or_percentage')
    def _check_invoice_total_payments(self):
        total_payments = sum(self.y_purchase_id.y_purchase_account_payment_ids.filtered(lambda x:x.y_is_approved).mapped('y_amount'))
        if self.y_amount_or_percentage == 'amount':
            total_amount = self._calculate_percent(self.y_payment_term_line_id.value_amount, self.y_purchase_id.amount_total)
            if round((total_payments + self.y_payment_amount),2) > round(total_amount,2):
                raise ValidationError("Down Payment Amount Exceeded!")

        if round((self.y_payment_amount + total_payments),2) > round(self.y_purchase_id.amount_total,2):
            raise ValidationError(_("Amount Exceeded to Payable Purchase Amount!"))
        

    def create_advance_payment(self):
        if not self.y_purchase_id:
            return
            
        # self._check_invoice_total_payments()
        payment_dict = {
            'y_partner_id': self.y_purchase_id.partner_id.id,
            'y_amount': self.y_payment_amount,
            'y_currency_id': self.y_currency_id.id,
            'y_company_id': self.y_company_id.id,
            'y_date': datetime.now(),
            'y_ref': f'Adv : {self.y_purchase_id.name}',
            'y_purchase_id': self.y_purchase_id.id,
            'y_remark': self.y_remark,
            'y_transaction_type':'po',
            'y_invoice_date_due': self.y_invoice_date_due,
            'y_sequence': self.y_purchase_id.y_advance_request_form_approval_id.y_advance_sequence_id.next_by_id() or 'New',
        }

        if not self.y_purchase_id.y_advance_request_form_approval_id.y_is_approval_required:
            payment_dict.update({
                'y_approval_status': False,    
                'y_is_approved':True,           
            })
        self.env['purchase.account.payment'].create(payment_dict)

class PurchaseAccount(models.Model):
    _name = "purchase.account.payment"
    _description = "Purchase Account Payment"
    _rec_name = "y_sequence"

    y_remark = fields.Text('Remark',readonly=True)
    y_sequence = fields.Char(string="Request No.",readonly=True)
    y_partner_id = fields.Many2one('res.partner',string="Vendor",readonly=True)
    y_company_id = fields.Many2one('res.company', 'Company',readonly=True)
    y_currency_id = fields.Many2one(comodel_name='res.currency',string='Currency',readonly=True)
    y_amount = fields.Monetary(currency_field='y_currency_id',string="Amount",readonly=True)
    y_date = fields.Date(string="Date",readonly=True)
    y_ref = fields.Char(string="Memo",readonly=True)
    y_reject_reason = fields.Char(string="Reject Reason",readonly=True)
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase",readonly=True)
    y_approved_by = fields.Many2one('res.users',string="Approved/Rejected By",readonly=True)
    y_is_advance_payment_done = fields.Boolean(string="Is Advance Payment Done",readonly=True)
    y_payment_status = fields.Selection([('draft', 'Not Paid'),('confirm', 'Paid'),], 
                                        default="draft", string="Payment Status",readonly=True)
    y_approval_status = fields.Selection([('approval_pending', 'Approval Pending'),
                                        ('approved', 'Approved'),('rejected', 'Reject')],
                                        default="approval_pending", string="Approval Status",readonly=True)
    
    y_invoice_date_due = fields.Datetime(string='Request Date',readonly=True)
    y_is_approved = fields.Boolean(default=False,string="Is Approved",readonly=True)

    y_transaction_type = fields.Selection([('boe', 'BOE'),('po', 'Purchase Order'),], 
                                         string="Transaction Type",readonly=True)

    def name_get(self):
        result = None 
        for rec in self:
            if rec.y_purchase_id:
                result = '%s-%s' % (rec.y_purchase_id.name, rec.y_sequence)
            else:
                result = '%s' % (rec.y_sequence)
        return result

    def copy(self):
        raise ValidationError("You cannot Duplicate the Down Payment Request")
        return super().copy()
    
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name_get()

    def _calculate_percent(self, y_percentage, value):
        """Calculate the percentage value."""
        return (y_percentage / 100) * value
    
    def action_approve(self):
        if self.y_purchase_id:
            payment_term_id = self.y_purchase_id.payment_term_id or self.y_purchase_id.partner_id.property_supplier_payment_term_id
            payment_term_line_id = payment_term_id.line_ids.filtered(lambda x:x.y_advance_request_required != False)

            total_payments = sum(self.y_purchase_id.y_purchase_account_payment_ids.filtered(lambda x:x.y_is_approved).mapped('y_amount'))
            if payment_term_line_id:
                payment_term_amount = payment_term_line_id.value_amount
                total_amount = self._calculate_percent(payment_term_amount, self.y_purchase_id.amount_total)
                if round((total_payments + self.y_amount),2) > round(total_amount,2):
                    raise ValidationError(_("Down Payment Amount Exceeded!"))

            if self.env.user in self.y_purchase_id.y_advance_request_form_approval_id.mapped('y_approval_user_ids'):
                self.y_approved_by = self.env.user.id
                self.write({'y_approval_status':'approved','y_is_approved':True})
            else:
                raise UserError (_("Oops!!!! You can't approve the request"))

    def action_reject(self):
        if self.y_purchase_id:
            if self.env.user in self.y_purchase_id.y_advance_request_form_approval_id.mapped('y_approval_user_ids'):
                return {'name': 'Reject Reason',
                        'type': 'ir.actions.act_window',
                        'res_model': 'reject.reason',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new',
                        'context': dict(default_y_purchase_id=self.y_purchase_id.id,default_y_purchase_account_payment_id=self.id),
                      }
            else:
                raise UserError (_("Oops!!!! You can't reject the request"))

class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    def _get_default_journal(self):
        return self.env['account.move']._search_default_journal(('bank', 'cash'))

    y_purchase_id = fields.Many2one('purchase.order','Purchase Order')
    y_remark = fields.Text('Remark')
    y_purchase_account_payment_id = fields.Many2one('purchase.account.payment',string='Down Payment Request')

    @api.onchange('y_purchase_account_payment_id')
    def _onchange_y_purchase_account_payment_id(self):
        if self.y_purchase_account_payment_id:
            self.amount = self.y_purchase_account_payment_id.y_amount
        else:
            self.amount = 0.00

    @api.onchange('partner_id')
    def _onchange_partner_purchase_account_payment(self):
        for payment in self:
            if payment.y_purchase_account_payment_id and payment.y_purchase_account_payment_id.y_partner_id != payment.partner_id:
                raise ValidationError("Vendor Miss Match")

    def action_post(self):
        res = super().action_post()
        for rec in self:
            if rec.y_purchase_account_payment_id:
                if rec.y_purchase_account_payment_id.y_payment_status == 'confirm':
                    raise ValidationError("Down Payment Request already been posted")
                if rec.y_purchase_account_payment_id.y_partner_id != rec.partner_id:
                    raise ValidationError("Vendor Miss Match")
                if rec.y_purchase_account_payment_id.y_amount != rec.amount:
                    raise UserError("The amount of the down payment does not match the payment amount.")  
            
                rec.y_purchase_account_payment_id.write({'y_is_advance_payment_done': True,
                                                         'y_payment_status': 'confirm'})
                rec.y_purchase_account_payment_id.y_purchase_id.y_is_payment_completed = True
                rec.y_purchase_id = rec.y_purchase_account_payment_id.y_purchase_id.id
        return res

    def action_draft(self):
        res = super().action_draft()
        for rec in self:
            rec.y_purchase_account_payment_id.write({'y_is_advance_payment_done':False,
                                                     'y_payment_status':'draft'})
            rec.y_purchase_account_payment_id.y_purchase_id.y_is_payment_completed = False
        return res

    @api.onchange('y_purchase_account_payment_id')
    def _onchange_sale_auto_complete(self):
        for payment in self:
            if payment.y_purchase_account_payment_id.journal_id:
                self.journal_id = payment.y_purchase_account_payment_id.journal_id.id
        return super()._onchange_sale_auto_complete()

    @api.onchange('y_purchase_account_payment_id')
    def _onchange_sale_auto_complete(self):
        if not self.y_purchase_account_payment_id:
            return
        self.write({'partner_id': self.y_purchase_account_payment_id.y_partner_id.id,
                    'payment_type':'outbound',
                    'partner_type':'supplier',
                    'payment_method_line_id':self.payment_method_line_id.id,
                    'amount':self.y_purchase_account_payment_id.y_amount,
                    'memo':self.y_purchase_account_payment_id.y_ref,
                    'date':self.y_purchase_account_payment_id.y_invoice_date_due,
                    })
    
    @api.constrains('currency_id','y_purchase_account_payment_id')
    def _check_currency_id(self):
        if self.y_purchase_account_payment_id:
            if self.currency_id != self.y_purchase_account_payment_id.y_currency_id:
                raise ValidationError("Currency mismatch")   
            
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.y_purchase_account_payment_id:
            raise ValidationError("You cannot change the payment type")
        
    @api.constrains('y_invoice_date_due','y_purchase_account_payment_id')
    def _check_invoice_date_due(self):
        for record in self:
            if record.date and record.y_purchase_account_payment_id.y_invoice_date_due:
                if record.date < record.y_purchase_account_payment_id.y_invoice_date_due.date():
                    raise ValidationError("Down Payment Date cannot be earlier than the Payment Date.")

    # overide the standard compute function 
    @api.depends('journal_id','y_purchase_account_payment_id')
    def _compute_currency_id(self):   
        super(AccountPaymentInherit,self)._compute_currency_id()
        if self.y_purchase_account_payment_id:
            self.currency_id = self.y_purchase_account_payment_id.y_currency_id.id

    def message_chatter(self, y_remark, purchase_obj):
        display_msg = ""
        if y_remark:
            display_msg += """<b>Remark:</b>  """ + y_remark +"""."""
        self.message_post(body=display_msg)

    def unlink(self):
        for each in self:
            if each.y_purchase_account_payment_id:
                raise UserError(_("Can not delete Purchase Order Advance Payments"))
        return super(AccountPaymentInherit, self).unlink()
