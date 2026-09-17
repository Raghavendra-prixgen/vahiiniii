# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta,date

class PurchaseRequestremarks(models.TransientModel):
    _name = 'purchase.request.approval.remarks'
    _description = 'purchase.request.approval.remarks'

    remarks = fields.Char( string='Remaks', required=True)
    
    def reject_order(self):
        user = self.env.user
        active_id = self.env.context['active_id']
        current_id = self.env['purchase.request'].search([('id','=',active_id)])
        for each in current_id.y_purchase_request_lvl_amt_approval_line:
            if each.y_is_approval_completed == False:
                if each.y_lvl_user_id.id in user.y_user_code_ids.ids:
                    each.write({'y_approval_status':'rejected',
                                'y_approved_date':datetime.now(),
                                'y_remarks':self.remarks,
                                'y_approved_id': self.env.user.id,
                                })

                    activity_ids = current_id.activity_ids.filtered(lambda x:x.state != 'done' and x.summary == 'Purchase Request Approval Request')
                    user_activity_ids = activity_ids.filtered(lambda x:x.user_id == user)
                    non_user_activity_ids = activity_ids.filtered(lambda x:x.user_id != user)
                    user_activity_ids.action_done()
                    non_user_activity_ids.action_cancel()

                    current_id.write({'state':'rejected',
                                      'y_to_approve_states':'reject',
                                      })
                    
                    current_id.write({'state':'rejected',
                                      'y_to_approve_states':'reject',
                                      })
                    current_id.message_post(body=_("Reject Reason :%s ")% (self.remarks))
                    break
                else:
                    raise UserError (_("You can't reject the order"))
                    break
           