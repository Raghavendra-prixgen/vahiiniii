from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from datetime import datetime, timedelta,date
from odoo.tools import html2plaintext

class MoToleranceApprove(models.TransientModel):
    _name = 'mo.tolerance.approve'
    _description = 'mo.tolerance.approve'

    y_reason = fields.Char( string='Reason', required=True)
    y_mrp_production_id = fields.Many2one('mrp.production')
    y_message = fields.Char(string="Message")

    def get_approve(self):
        mo_obj = self.y_mrp_production_id or self.env['mrp.production'].browse(self._context.get('active_id'))
        for each in mo_obj:
            each.y_is_approval_required = True
            if each.y_mrp_approval_line_ids.filtered(lambda x:x.y_is_approval_completed):
                raise UserError (_("Oops!!!!You cannot request once approved"))
            else:
                each.y_mrp_approval_line_ids = False
        
            domain = [('y_company_id','=',each.company_id.id),('y_product_category_id','=',each.product_id.categ_id.id)]
            approval_ids = each.env['manufacturing.tolerance.approval'].search(domain)
            if not approval_ids:
                if each.company_id.sudo().parent_id:
                    domain = ['|',('y_company_id','=',each.company_id.sudo().parent_id.id),('y_company_id','=',each.company_id.id),('y_product_category_id','=',each.product_id.categ_id.id)]
                    approval_ids = each.env['manufacturing.tolerance.approval'].sudo().search(domain)
            if not approval_ids:
                raise ValidationError("""Approvals Not Configured""")

            filtered_approval_ids = approval_ids.y_lvl_amt_approval_lines[0]
            if filtered_approval_ids:
                level_approval_amount_obj = each.env['mrp.product.approval']
                for each_line in filtered_approval_ids:
                    if each_line.y_approval_level == '1stlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':each_line.y_approval_level,
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        
                    elif each_line.y_approval_level == '2ndlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                    elif each_line.y_approval_level == '3rdlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })                            
                    elif each_line.y_approval_level == '4thlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })                            
                        level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                    elif each_line.y_approval_level == '5thlvlapproval':
                        level_approval_amount_obj.create({'y_approval_level':'1stlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl1_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'2ndlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl2_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })
                        level_approval_amount_obj.create({'y_approval_level':'3rdlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl3_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })                            
                        level_approval_amount_obj.create({'y_approval_level':'4thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl4_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })                            
                        level_approval_amount_obj.create({'y_approval_level':'5thlvlapproval',
                                'y_lvl_user_id': each_line.y_lvl5_user_id.id,
                                'y_mrp_approval_id':each.id,
                                })                            
                each.y_to_approve_states = 'to_approve_state1'
                each.message_post(body=_("Tolerance Approval Reason :%s ")% (self.y_reason))

            else:
                raise ValidationError("""Approval Lines Not Avialable !""")


            if each.y_mrp_approval_line_ids:
                each.y_is_approval_show = True
                # Activity for First Approval
                first_approval = each.y_mrp_approval_line_ids[:1]
                if first_approval:
                    res_model = self.env['ir.model'].sudo().search([('model','=',each._name)])
                    subject = 'Manufacturing Tolerance Approval Request'
                    company_ids = each.company_id + each.company_id.sudo().parent_id
                    user_ids = self.env['res.users'].sudo().search([('y_user_code_ids','=',first_approval.y_lvl_user_id.id),('company_id','in',company_ids.ids)])
                    for user in user_ids:
                        body = f'The "{self.env.user.name}" has requested approval for the manufacturing tolerance"{each.name}"'
                        vals={
                            'res_model_id':res_model.id,
                            'res_model':each._name,
                            'res_id':each.id,
                            'activity_type_id': first_approval.y_lvl_user_id.y_activity_type_id.id,
                            'user_id':user.id,
                            'date_deadline':date.today(),
                            'summary': subject,
                            'note': html2plaintext(body)                            
                        }
                        activity = self.env['mail.activity'].sudo().create(vals)
                # Activity END



