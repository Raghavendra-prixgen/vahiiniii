from odoo import api, fields,models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date
from lxml.etree import Element
from odoo.tools import html2plaintext
# ===========================# Purchase Approval Configuration #======================================================================================

def get_selection_label(self, object, field_name, field_value):
	return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])

class UserApprovalCode(models.Model):
    _inherit = 'user.approval.code'

    def unlink(self):
        domain = [('y_lvl_user_id','=',self.id)]
        existing_ids = self.env['purchase.request.approval.lvlsamt'].search(domain)
        if existing_ids:
            raise ValidationError("Once the approval code is used, it cannot be deleted.")
        return super().unlink()

    def write(self,vals):
        if vals.get('y_code'):
            domain = [('y_lvl_user_id','=',self.id)]
            existing_ids = self.env['purchase.request.approval.lvlsamt'].search(domain)
            if existing_ids:
                raise ValidationError("Once the approval code is used, it cannot be modified.")
        return super().write(vals)


class PurchaseDocType(models.Model):
    _inherit = 'request.type'
    
    y_is_approval_required = fields.Boolean(default=True,string="Is Approval Required")


class PurchaseRequestAppproval(models.Model):
    _name = "purchase.request.approval"
    _description ="purchase.request.approval"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'y_name'

    active = fields.Boolean(default=True)
    y_request_type_id = fields.Many2one("request.type","Request Type",tracking=True)
    y_parent_company_id = fields.Many2one(related="y_company_id.parent_id")
    y_name = fields.Char("Name")
    y_lvl_amt_approval_lines = fields.One2many("purchase.request.lvlamt.approval","y_lvl_approval_id",string="Request Level Amount Lines")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    y_procurement_group_id = fields.Many2one('product.procurement.group',string="Procurement Group")
            
    @api.constrains('y_name','y_company_id','active')
    def check_purchase_approval_name(self):
        for rec in self:
            docs=rec.env['purchase.request.approval'].search([('y_name','=',rec.y_name),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""name already exists!"""))

    @api.onchange('y_request_type_id')
    def _update_name(self):
        if self.y_request_type_id:
            self.y_name = self.y_request_type_id.name

    @api.constrains('y_request_type_id','active','y_company_id')
    def _check_duplicate(self):
        domain = [('y_request_type_id','=',self.y_request_type_id.id),('y_company_id','=',self.y_company_id.id)]
        existing_id=self.env['purchase.request.approval'].search(domain)
        if len(existing_id) > 1:
            raise UserError (_("Oops, looks like we've got a duplicate record!"))

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
                                        new_approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',newval[-1].get('y_approval_level'))
                                        old_approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',dicts.y_approval_level)
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
        
        return super(PurchaseRequestAppproval,self).write(vals)

class PurchaseRequestLevelAmmountApproval(models.Model):
    _name = "purchase.request.lvlamt.approval"
    _description = "Purchase Request Lvl&Amt Approval"

    def _group_internal_users(self):
        group = self.env.ref('base.group_user', raise_if_not_found=False)
        return [('groups_id', 'in', group.ids)] if group else []

    y_approval_level = fields.Selection(selection=[
            ('1stlvlapproval', '1'),
            ('2ndlvlapproval', '2'),
            ('3rdlvlapproval', '3'),
            ('4thlvlapproval', '4'),
            ('5thlvlapproval', '5'),
            ],string='Approval Level',copy=False,store=True)
    y_lvl1_user_id = fields.Many2one("user.approval.code",string="Level 1 Code",domain="[('y_model_ids.model','=','purchase.request')]")
    y_lvl2_user_id = fields.Many2one("user.approval.code",string="Level 2 Code",domain="[('y_model_ids.model','=','purchase.request')]")
    y_lvl3_user_id = fields.Many2one("user.approval.code",string="Level 3 Code",domain="[('y_model_ids.model','=','purchase.request')]")
    y_lvl4_user_id = fields.Many2one("user.approval.code",string="Level 4 Code",domain="[('y_model_ids.model','=','purchase.request')]")
    y_lvl5_user_id = fields.Many2one("user.approval.code",string="Level 5 Code",domain="[('y_model_ids.model','=','purchase.request')]")

    y_approval_amount_from = fields.Float("Amount(From)")
    y_approval_amount_to = fields.Float("Amount(To)")
    y_lvl_approval_id = fields.Many2one('purchase.request.approval',string="Lvl and Approval")

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

    @api.constrains('y_approval_level','y_lvl1_user_id','y_lvl2_user_id','y_lvl3_user_id','y_lvl4_user_id','y_lvl5_user_id')
    def _check_levels(self):
        for line in self:
            if line.y_approval_level == '1stlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
            if line.y_approval_level == '2ndlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))

            if line.y_approval_level == '3rdlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
            if line.y_approval_level == '4thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
            
            if line.y_approval_level == '5thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id and x.y_lvl5_user_id == line.y_lvl5_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'purchase.request.lvlamt.approval','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
                


# ===============================# Purchase Approval Configuration End #===============================================================#
# =====================================================================================================================================#
# ===============================#   Purchase Approval in Purchase Order   #===========================================================#


class PurchaseRequestOrderApprovalLvlAmt(models.Model):
    _name="purchase.request.approval.lvlsamt"
    _description  = 'Purchase Request Order Approval Lvl Amt'

    y_purchase_lvl_id = fields.Many2one('purchase.request',string="Purchase Request")
    y_approval_level = fields.Selection(selection=[
            ('1stlvlapproval', '1'),
            ('2ndlvlapproval', '2'),
            ('3rdlvlapproval', '3'),
            ('4thlvlapproval', '4'),
            ('5thlvlapproval', '5'),
            ],string='Approval Level',copy=False)
    y_lvl_user_id = fields.Many2one("user.approval.code",string="Code")
    y_approved_id = fields.Many2one("res.users",string="Approved By")
    y_is_approval_completed = fields.Boolean(default=False,string="Is Approval Completed")
    y_approval_status = fields.Selection([('approval_pending','Approval Pending'),('approved','Approved'),('rejected','Rejected')],default="approval_pending",string="Approval Status")
    y_approved_date = fields.Datetime("Approved Date")
    y_remarks = fields.Char(string="Remarks")

    def view_code_users(self):
        context = dict(self.env.context)
        context.update({'create':False,'edit':False})
        tree_view_id = self.env.ref('user_approval_code.res_users_view_approval_code_tree').id
        return {
                'name': "Users",
                'res_model': 'res.users',
                'type': 'ir.actions.act_window',
                'view_mode': 'list',
                'target': 'new',
                'view_id': self.env.ref("user_approval_code.res_users_view_approval_code_tree").id,
                'views': [[tree_view_id, 'list']],
                'context':context,
                'domain': [('y_user_code_ids', '=', self.y_lvl_user_id.id)],  
            }


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    y_purchase_request_lvl_amt_approval_line = fields.One2many("purchase.request.approval.lvlsamt",'y_purchase_lvl_id',copy=False,string="Request Amount Level Lines")
    y_is_approval_required = fields.Boolean(copy=False, default=False,string="Is Approval Required")
    y_is_approval_show = fields.Boolean(copy=False, default=False,string="Is Approval Show")
    y_to_approve_states = fields.Selection(selection=[            
            ('to_approve_state1', '1st Approval Pending'),
            ('to_approve_state2', '2nd Approval Pending'),
            ('to_approve_state3', '3rd Approval Pending'),
            ('to_approve_state4', '4th Approval Pending'),
            ('to_approve_state5', '5th Approval Pending'),
            ('approved', 'Approved'),
            ('na',''),
            ('reject','Rejected')
            ],string='Approval Status',default='na',store=True,copy=False)
    y_approval_method = fields.Char("Approval Method",copy=False)


    def button_rejected(self):
        tree_view_id = self.env.ref('purchase_request_approval_18.purchase_request_approval_remarks_form').id
        return {
                'name': "Purchase Request Remarks",
                'res_model': 'purchase.request.approval.remarks',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'view_id': self.env.ref("purchase_request_approval_18.purchase_request_approval_remarks_form").id,
                'views': [[tree_view_id, 'form']],
            }

    @api.depends('request_type_id')
    def _compute_is_approval_required(self):
        for order in self:
            order.y_is_approval_required = order.request_type_id.y_is_approval_required

    def copy(self):
        res = super().copy()
        res._onchange_lines_approved()
        return res
    
    @api.onchange('request_type_id')
    def _onchange_lines_approved(self):
        if  self.request_type_id.y_is_approval_required == True:
            self.y_is_approval_required = True
            self.y_is_approval_show = True
            domain = [('y_company_id','=',self.company_id.id),('y_request_type_id','=',self.request_type_id.id)]
            # if self.y_procurement_group_id:
            #     domain+=[('y_procurement_group_id','=',self.y_procurement_group_id.id)]
            approval_ids = self.env['purchase.request.approval'].search(domain,limit=1)
            if not approval_ids:
                if self.company_id.sudo().parent_id:
                    domain = ['|',('y_company_id','=',self.company_id.sudo().parent_id.id),('y_company_id','=',self.company_id.id),('y_request_type_id','=',self.request_type_id.id)]
                    # if self.y_procurement_group_id:
                    #     domain+=[('y_procurement_group_id','=',self.y_procurement_group_id.id)]
                    approval_ids = self.env['purchase.request.approval'].sudo().search(domain,limit=1)
            if not approval_ids:
                raise ValidationError("""Approvals Not Configured""")
            self.y_to_approve_states = 'to_approve_state1'
        else:
            self.y_is_approval_required = False
            self.y_to_approve_states = 'na'
            self.y_is_approval_show = False

    def button_draft(self):
        res = super().button_draft()
        self.y_purchase_request_lvl_amt_approval_line.unlink()
        self._onchange_lines_approved()
        

    def button_to_approve(self):
        for each in self:
            if each.request_type_id and each.request_type_id.y_is_approval_required == True:
                each.y_is_approval_required = True
                if each.y_purchase_request_lvl_amt_approval_line.filtered(lambda x:x.y_is_approval_completed):
                    raise UserError (_("Oops!!!!You cannot change the request type once approved, Kindly Reset To Draft the SO"))
                else:
                    each.y_purchase_request_lvl_amt_approval_line = False
            
                domain = [('y_company_id','=',each.company_id.id),('y_request_type_id','=',each.request_type_id.id)]
                # if self.y_procurement_group_id:
                #     domain+=[('y_procurement_group_id','=',self.y_procurement_group_id.id)]
                approval_ids = each.env['purchase.request.approval'].search(domain)
                if not approval_ids:
                    if each.company_id.sudo().parent_id:
                        domain = ['|',('y_company_id','=',each.company_id.sudo().parent_id.id),('y_company_id','=',each.company_id.id),('y_request_type_id','=',each.request_type_id.id)]
                        # if self.y_procurement_group_id:
                        #     domain+=[('y_procurement_group_id','=',self.y_procurement_group_id.id)]
                        approval_ids = each.env['purchase.request.approval'].sudo().search(domain)
                if not approval_ids:
                    raise ValidationError("""Approvals Not Configured""")
    
                filtered_approval_ids = approval_ids.y_lvl_amt_approval_lines[0]
                if filtered_approval_ids:
                    level_approval_amount_obj = each.env['purchase.request.approval.lvlsamt']
                    for each_line in filtered_approval_ids:
                        if each_line.y_approval_level == '1stlvlapproval':
                            level_approval_amount_obj.create({'y_approval_level':each_line.y_approval_level,
                                    'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            
                        elif each_line.y_approval_level == '2ndlvlapproval':
                            level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                        elif each_line.y_approval_level == '3rdlvlapproval':
                            level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })                            
                        elif each_line.y_approval_level == '4thlvlapproval':
                            level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })                            
                            level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                        elif each_line.y_approval_level == '5thlvlapproval':
                            level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })
                            level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })                            
                            level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })                            
                            level_approval_amount_obj.create({'y_approval_level':'5thlvlapproval',
                                    'y_lvl_user_id': each_line.y_lvl5_user_id.id,
                                    'y_purchase_lvl_id':each.id,
                                    })                            
                    each.y_to_approve_states = 'to_approve_state1'
                else:
                    raise ValidationError("""The PR total amount is out of the Approval Grid""")

                if each.y_purchase_request_lvl_amt_approval_line:
                    each.y_is_approval_show = True
                    each.write({'state':'to_approve'})

                    # Activity for First Approval
                    first_approval = each.y_purchase_request_lvl_amt_approval_line[:1]
                    if first_approval:
                        res_model = self.env['ir.model'].sudo().search([('model','=',self._name)])
                        subject = 'Purchase Request Approval Request'
                        company_ids = self.company_id + self.company_id.sudo().parent_id
                        user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',first_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                        for user in user_ids:
                            body = f'The "{self.env.user.name}" has requested approval for the purchase request "{self.name}"'
                            vals={
                                'res_model_id':res_model.id,
                                'res_model':self._name,
                                'res_id':self.id,
                                'activity_type_id': first_approval.y_lvl_user_id.y_activity_type_id.id,
                                'user_id':user.id,
                                'date_deadline':date.today(),
                                'summary': subject,
                                'note': html2plaintext(body)                            
                            }
                            activity = self.env['mail.activity'].sudo().create(vals)
                    # Activity END



        return super(PurchaseRequest, self).button_to_approve()


    def confirm_approval(self):
        user = self.env.user
        if self.y_is_approval_required == True:
            for lvl_amt_line in self.y_purchase_request_lvl_amt_approval_line:
                if lvl_amt_line.y_is_approval_completed == False:
                    if lvl_amt_line.y_lvl_user_id.id in user.y_user_code_ids.ids:
                        lvl_amt_line.write({'y_approval_status':'approved',
                                            'y_approved_date':datetime.now(),
                                            'y_is_approval_completed': True,
                                            'y_approved_id': self.env.user.id,
                                            })
                        
                        activity_ids = self.activity_ids.filtered(lambda x:x.state != 'done' and x.summary == 'Purchase Request Approval Request')
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

            for lvl_amt_line in self.y_purchase_request_lvl_amt_approval_line:
                if lvl_amt_line.y_is_approval_completed == False:
                    # Activity for Next Approval
                    next_approval = lvl_amt_line
                    if next_approval:
                        res_model = self.env['ir.model'].sudo().search([('model','=',self._name)])
                        subject = 'Purchase Request Approval Request'
                        company_ids = self.company_id + self.company_id.sudo().parent_id
                        user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',next_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                        for user in user_ids:
                            body = f'The "{self.env.user.name}" has requested approval for the purchase request "{self.name}"'
                            vals={
                                'res_model_id':res_model.id,
                                'res_model':self._name,
                                'res_id':self.id,
                                'activity_type_id': next_approval.y_lvl_user_id.y_activity_type_id.id,
                                'user_id':user.id,
                                'date_deadline':date.today(),
                                'summary': subject,
                                'note': html2plaintext(body)                            
                            }
                            activity = self.env['mail.activity'].sudo().create(vals)
                    # Activity END


            data = self.y_purchase_request_lvl_amt_approval_line.mapped('y_is_approval_completed')  
            if all(data) == True:
                self.write({'y_to_approve_states':'approved',
                            'y_is_approval_required':False,
                            })
                self.write({"state": "approved"})
        else:
            if not self.line_ids:
                raise UserError (_("Hey, looks like those products aren't up for confirm."))
            self.write({"state": "approved"})


    def button_approved(self):
        for purchase in self:
            if purchase.y_is_approval_required == True:
                if not purchase.y_purchase_request_lvl_amt_approval_line:
                     raise ValidationError("Please click the 'Request Approval' button to obtain the necessary approvals.")
                
                all_y_approvals = [x.y_is_approval_completed for x in purchase.y_purchase_request_lvl_amt_approval_line]
                if False in all_y_approvals:
                    raise UserError (_("Purchase Request Approval Pending"))
        return True


    