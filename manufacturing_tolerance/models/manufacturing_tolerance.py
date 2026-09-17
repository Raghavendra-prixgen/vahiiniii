from odoo import fields, models,api, exceptions, _
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from datetime import datetime, timedelta,date
from odoo.tools import html2plaintext

def get_selection_label(self, object, field_name, field_value):
    return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])


class ProductTemplateNew(models.Model):
    _inherit='product.template'

    y_manufacturing_tolerance = fields.Float(string='Manufacturing Tolerance %',default=0.0)
    y_is_manufacturing_tolerance = fields.Boolean(string='Manufacturing Tolerance')

class UserApprovalCode(models.Model):
    _inherit = 'user.approval.code'

    def unlink(self):
        domain = [('y_lvl_user_id','=',self.id)]
        existing_ids = self.env['mrp.product.approval'].search(domain)
        if existing_ids:
            raise ValidationError("Once the approval code is used, it cannot be deleted.")
        return super().unlink()

    def write(self,vals):
        if vals.get('y_code'):
            domain = [('y_lvl_user_id','=',self.id)]
            existing_ids = self.env['mrp.product.approval'].search(domain)
            if existing_ids:
                raise ValidationError("Once the approval code is used, it cannot be modified.")
        return super().write(vals)

class ManufacturingToleranceAppproval(models.Model):
    _name = "manufacturing.tolerance.approval"
    _description ="Manufacturing Tolerance Approval"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _rec_name = 'y_name'

    active = fields.Boolean(default=True)
    y_parent_company_id = fields.Many2one(related="y_company_id.parent_id")
    y_name = fields.Char("Name")

    y_product_category_id = fields.Many2one('product.category',string="Product Category")
    y_lvl_amt_approval_lines = fields.One2many("manufacturing.tolerance.approval.line","y_lvl_approval_id",string="Level Amount Approval Lines")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
            
    @api.constrains('y_name','y_company_id','active')
    def check_manufacturing_tolerance_approval_name(self):
        for rec in self:
            docs=rec.env['manufacturing.tolerance.approval'].search([('y_name','=',rec.y_name),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""name already exists!"""))

    @api.constrains('y_product_category_id','active','y_company_id')
    def _check_duplicate(self):
        domain = [('y_product_category_id','=',self.y_product_category_id.id),('y_company_id','=',self.y_company_id.id)]
        existing_id=self.env['manufacturing.tolerance.approval'].search(domain)
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
                                        # new_approval_level = newval[-1].get('y_approval_level')
                                        new_approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',newval[-1].get('y_approval_level'))
                                        old_approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',dicts.y_approval_level)
                                        new_dist.append('{}{} ---> {}'.format("Approval Level : ",old_approval_level,new_approval_level))
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
        
        return super(ManufacturingToleranceAppproval,self).write(vals)



class ManufacturingToleranceAppprovalLine(models.Model):
    _name = "manufacturing.tolerance.approval.line"
    _description ="Manufacturing Tolerance Approval Line"
    _rec_name = "y_lvl_approval_id"


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
    y_lvl1_user_id = fields.Many2one("user.approval.code",string="Level 1 Code",domain="[('y_model_ids.model','=','mrp.production')]")
    y_lvl2_user_id = fields.Many2one("user.approval.code",string="Level 2 Code",domain="[('y_model_ids.model','=','mrp.production')]")
    y_lvl3_user_id = fields.Many2one("user.approval.code",string="Level 3 Code",domain="[('y_model_ids.model','=','mrp.production')]")
    y_lvl4_user_id = fields.Many2one("user.approval.code",string="Level 4 Code",domain="[('y_model_ids.model','=','mrp.production')]")
    y_lvl5_user_id = fields.Many2one("user.approval.code",string="Level 5 Code",domain="[('y_model_ids.model','=','mrp.production')]")
    y_lvl_approval_id = fields.Many2one('manufacturing.tolerance.approval',string="Lvl and Approval")

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
                    approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
            if line.y_approval_level == '2ndlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))

            if line.y_approval_level == '3rdlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
            if line.y_approval_level == '4thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
            
            if line.y_approval_level == '5thlvlapproval':
                duplicates = line.y_lvl_approval_id.y_lvl_amt_approval_lines.filtered(lambda x:x.y_approval_level == line.y_approval_level and x.y_lvl1_user_id == line.y_lvl1_user_id and x.y_lvl2_user_id == line.y_lvl2_user_id and x.y_lvl3_user_id == line.y_lvl3_user_id and x.y_lvl4_user_id == line.y_lvl4_user_id and x.y_lvl5_user_id == line.y_lvl5_user_id)
                if len(duplicates) > 1:
                    approval_level = get_selection_label(self,'manufacturing.tolerance.approval.line','y_approval_level',line.y_approval_level)
                    raise UserError("{} Already Exists".format(approval_level))
    
                


class MrpProductionApproval(models.Model):
    _name = "mrp.product.approval"
    _description  = "Mrp Product Approval"
    _rec_name = "y_mrp_approval_id"

    y_mrp_approval_id = fields.Many2one('mrp.production',string="Production Order")
    y_approved_id = fields.Many2one("res.users",string="Approved By")
    y_approval_level = fields.Selection(selection=[
            ('1stlvlapproval', '1'),
            ('2ndlvlapproval', '2'),
            ('3rdlvlapproval', '3'),
            ('4thlvlapproval', '4'),
            ('5thlvlapproval', '5'),
            ],string='Approval Level',copy=False)
    y_lvl_user_id = fields.Many2one("user.approval.code",string="Code")
    y_is_approval_completed = fields.Boolean(default=False,string="IS Approval Completed")
    y_approval_status = fields.Selection([('approval_pending','Approval Pending'),('approved','Approved'),('rejected','Rejected')],default="approval_pending",string="Approval Status")
    y_approved_date = fields.Datetime("Approved Date")
    y_remarks = fields.Char(string="Remarks")
    y_approver_id = fields.Many2one('res.users',string="Approved By")

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

class MrpProductionNew(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection(selection_add=[
        ('to_approved', 'To Approve'),
        ('approved', 'Approved'),
        ('to_close','To Close')
        ],ondelete={'to_approved': 'cascade','approved':'cascade'})

    @api.depends('state', 'product_qty', 'qty_producing')
    def _compute_show_produce(self):
        for production in self:
            state_ok = production.state in ('confirmed', 'progress', 'to_close','approved')
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            production.show_produce_all = state_ok and qty_none_or_all
            production.show_produce = state_ok and not qty_none_or_all

    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing', 'move_raw_ids.picked','y_mrp_approval_line_ids.y_is_approval_completed')
    def _compute_state(self):
        super()._compute_state()
        for production in self:
            if production.y_mrp_approval_line_ids:
                if production.y_mrp_approval_line_ids.filtered(lambda x:x.y_is_approval_completed == False):
                    production.state = 'to_approved'
                elif production.y_mrp_approval_line_ids.filtered(lambda x:x.y_is_approval_completed) and production.state not in ('done','cancel'):
                    production.state = 'approved'

    y_is_approved = fields.Boolean(string='Approval',copy=False)
    y_approve_reason = fields.Char(string="Approve Reason")
 
    y_mrp_approval_line_ids = fields.One2many("mrp.product.approval",'y_mrp_approval_id')
    y_is_approval_required = fields.Boolean(copy=False, default=False,string="Is Approval Required")
    y_is_approval_show = fields.Boolean(copy=False, default=False,string="Is Approval Show Page")
    y_to_approve_states = fields.Selection(selection=[            
            ('to_approve_state1', '1st Approval Pending'),
            ('to_approve_state2', '2nd Approval Pending'),
            ('to_approve_state3', '3rd Approval Pending'),
            ('to_approve_state4', '4th Approval Pending'),
            ('to_approve_state5', '5th Approval Pending'),
            ('approved', 'Approved'),
            ('na','N/A'),
            ('reject','Rejected')
            ],string='Approval Status',default='na',store=True,copy=False)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if self.product_id.product_tmpl_id.y_is_manufacturing_tolerance == False:
                self.y_is_approval_required = False
                self.y_to_approve_states = 'na'
                self.y_is_approval_show = False
                return {'warning': {
                            'title': 'Warning!',
                            'message': 'MO Tolerance Not Mapped for this Product !'}
                            }
            else:
                self.y_is_approval_required = True
                self.y_is_approval_show = True
                domain = [('y_company_id','=',self.company_id.id),('y_product_category_id','=',self.product_id.product_tmpl_id.categ_id.id)]
                approval_ids = self.env['manufacturing.tolerance.approval'].search(domain,limit=1)
                if not approval_ids:
                    if self.company_id.sudo().parent_id:
                        domain = ['|',('y_company_id','=',self.company_id.sudo().parent_id.id),('y_company_id','=',self.company_id.id),('y_product_category_id','=',self.product_id.product_tmpl_id.categ_id.id)]
                        approval_ids = self.env['manufacturing.tolerance.approval'].sudo().search(domain,limit=1)
                if not approval_ids:
                    raise ValidationError("""Approvals Not Configured""")
                self.y_to_approve_states = 'to_approve_state1'


    def button_mark_done(self):
        for mrp in self:
            if mrp.product_id.product_tmpl_id.y_is_manufacturing_tolerance and mrp.state != 'approved' and mrp.product_id.product_tmpl_id.y_toggle_button==True:
                if mrp.product_id.product_tmpl_id.y_toggle_button==True and mrp.y_fg_actual_weight == 0:
                    raise UserError (_("The actual weight of the FG cannot be zero."))
                manufacturing_tolerance = mrp.product_id.product_tmpl_id.y_manufacturing_tolerance
                should_consume_quantity  =  mrp.y_actual_ideal_weight # need to update
                fg_actual_weight = mrp.y_fg_actual_weight
                percentage_mt = (manufacturing_tolerance / 100) * should_consume_quantity
                lower_bound = should_consume_quantity - percentage_mt
                upper_bound = should_consume_quantity + percentage_mt
                total_quantity_done = sum(mrp.move_raw_ids.mapped('quantity'))
                if not (lower_bound <= fg_actual_weight <= upper_bound) :
                    msg = _("The '{}' must be in the range {} - {}.quantity".format(mrp.product_id.name,lower_bound,upper_bound))
                    action = self.env["ir.actions.actions"]._for_xml_id("manufacturing_tolerance.button_approve_view_action")
                    action['context'] = {'default_y_mrp_production_id': mrp.id,'default_y_message':msg}
                    return action
        return super(MrpProductionNew, self).button_mark_done()

    def request_for_approval(self):
        action = self.env["ir.actions.actions"]._for_xml_id("manufacturing_tolerance.button_approve_view_action")
        action['context'] = {'default_y_mrp_production_id': self.id}
        return action
       
    def confirm_approval(self):
        user = self.env.user
        if self.y_is_approval_required == True:
            for lvl_amt_line in self.y_mrp_approval_line_ids:
                if lvl_amt_line.y_is_approval_completed == False:
                    if lvl_amt_line.y_lvl_user_id.id in user.y_user_code_ids.ids:
                        lvl_amt_line.write({'y_approval_status':'approved',
                                            'y_approved_date':datetime.now(),
                                            'y_is_approval_completed': True,
                                            'y_approved_id': self.env.user.id,
                                            })
                        
                        activity_ids = self.activity_ids.filtered(lambda x:x.state != 'done' and x.summary == 'Manufacturing Tolerance Approval Request')
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

            for lvl_amt_line in self.y_mrp_approval_line_ids:
                if lvl_amt_line.y_is_approval_completed == False:
                    # Activity for Next Approval
                    next_approval = lvl_amt_line
                    if next_approval:
                        res_model = self.env['ir.model'].sudo().search([('model','=',self._name)])
                        subject = 'Manufacturing Tolerance Approval Request'
                        company_ids = self.company_id + self.company_id.sudo().parent_id
                        user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',next_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                        for user in user_ids:
                            body = f'The "{self.env.user.name}" has requested approval for the manufacturing tolerance"{self.name}"'
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


            data = self.y_mrp_approval_line_ids.mapped('y_is_approval_completed')  
            if all(data) == True:
                self.write({'y_to_approve_states':'approved',
                            'y_is_approval_required':False,
                            })

                

# class MrpConsumptionWarning(models.TransientModel):
#     _inherit = 'mrp.consumption.warning'

#     # def action_confirm(self):
#     #     for production in self.mrp_production_ids.filtered(lambda x:x.state != 'approved'):
#     #         if production.product_id.product_tmpl_id.y_is_manufacturing_tolerance:
#     #             for line in self.mrp_consumption_warning_line_ids:
#     #                 manufacturing_tolerance = production.product_id.product_tmpl_id.y_manufacturing_tolerance
#     #                 total_mrp_ideal_weight = production.y_ac
#     #                 consumed_qty = line.product_consumed_qty_uom
#     #                 lower_bound = total_mrp_ideal_weight - ((total_mrp_ideal_weight / 100) * manufacturing_tolerance)
#     #                 upper_bound = total_mrp_ideal_weight + ((total_mrp_ideal_weight / 100) * manufacturing_tolerance)
#     #                 if production.y_is_approved == True:
#     #                     return super(MrpConsumptionWarning, self).action_confirm()
#     #                 if not (lower_bound <= consumed_qty <= upper_bound):
#     #                     msg = _("The '{}' must be in the range {} - {}.quantity".format(line.product_id.name,lower_bound,upper_bound))
#     #                     action = self.env["ir.actions.actions"]._for_xml_id("manufacturing_tolerance.button_approve_view_action")
#     #                     action['context'] = {'default_y_mrp_production_id': production.id,'default_y_message':msg}
#     #                     return action
#     #     return super(MrpConsumptionWarning, self).action_confirm()


class MrpConsumptionWarning(models.TransientModel):
    _inherit = 'mrp.consumption.warning'


    def action_confirm(self):
        if self.mrp_production_ids.product_id.product_tmpl_id.y_is_manufacturing_tolerance and not self.mrp_production_ids.product_id.product_tmpl_id.y_toggle_button:
            for line in self.mrp_consumption_warning_line_ids:
                manufacturing_tolerance = self.mrp_production_ids.product_id.product_tmpl_id.y_manufacturing_tolerance
                total_mrp_ideal_weight = self.mrp_production_ids.qty_producing
                consumed_qty = line.product_consumed_qty_uom

                lower_bound = total_mrp_ideal_weight - ((total_mrp_ideal_weight / 100) * manufacturing_tolerance)
                upper_bound = total_mrp_ideal_weight + ((total_mrp_ideal_weight / 100) * manufacturing_tolerance)
                if  not (lower_bound <= consumed_qty <= upper_bound):
                    
                    raise UserError(
                            "The '{}' must be in the range {} - {}.quantity"
                            .format(line.product_id.name,lower_bound,upper_bound)
                        )
                else:
                    return super(MrpConsumptionWarning, self).action_confirm()
        return super(MrpConsumptionWarning, self).action_confirm()



    def action_cancel(self):
        res = super(MrpConsumptionWarning, self).action_cancel()
        self.mrp_production_ids.write({'state': 'progress'})
        return res



class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    @api.model
    def default_get(self, fields):
        result = super(MrpUnbuild, self).default_get(fields)
        active_id = self.env.context.get('default_mo_id')
        record = self.env['mrp.production'].sudo().browse(active_id)
        if record:
            result['product_qty'] = record.product_qty        
        return result 
