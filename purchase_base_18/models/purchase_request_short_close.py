from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo import SUPERUSER_ID, _, api, fields, models
from markupsafe import Markup

class PurchaseRequestShortCloseWizard(models.TransientModel):
    _name = 'purchase.request.short.close.wizard'
    _rec_name = 'y_purchase_request_id'

    y_pr_lines_ids = fields.Many2many('purchase.request.line',string='Short Close Purchase Request Lines')
    y_purchase_request_id = fields.Many2one('purchase.request',string="Purchase Request")
    
    @api.onchange('y_purchase_request_id')
    def _onchange_so_pr_lines(self):
        for rec in self:
            pr_line = []
            if self._context.get('default_y_pr_lines_ids'):
                pr_line = [(6,0,self._context.get('default_y_pr_lines_ids'))]
            else:
                pr_lines = self.env['purchase.request.line']
                lines = self.env['purchase.request.line'].search([('id','=',self._context.get('active_ids'))])
                pr_line = lines.filtered(lambda line: line.y_is_short_closed == False)
                for line in pr_line:
                    purchase_done_quantity = sum(line.purchase_lines.filtered(lambda x:x.state in ('done','purchase')).mapped('product_qty'))
                    if line.product_qty > purchase_done_quantity:
                        pr_lines += line
                if pr_lines:
                    pr_line = [(6,0,pr_lines.ids)]
            rec.y_pr_lines_ids = pr_line
    
    def button_action_short_close(self):
        lines_ids = self.y_pr_lines_ids.filtered(lambda x:x.y_is_short_closed)
        if not lines_ids:
            raise UserError("No Lines to be short close.")
        request_id = lines_ids.mapped('request_id')
        request_id.write({'y_is_short_closed':True})
        msg = Markup("")
        for line in lines_ids: 
            msg += Markup("{} Short Closed.<br/>    Reason: {} <br/><br/>".format(line.product_id.name,line.y_short_close_reason_id.y_name))

        request_id.message_post(body=msg)
            
class PurchaseOrder(models.Model):
    _inherit = 'purchase.request.line'

    def purchase_request_line_short_close_form_wizard(self):
        pr_lines_ids = self.env['purchase.request.line']
        pr_lines = self.filtered(lambda line: line.y_is_short_closed == False)
        for line in pr_lines:
            purchase_done_quantity = sum(line.purchase_lines.filtered(lambda x:x.state in ('done','purchase')).mapped('product_qty'))
            if line.product_qty > purchase_done_quantity:
                pr_lines_ids += line          
        if all([True if state in ('approved','partial') else False for state in pr_lines_ids.mapped('request_state')]) and 'approved' in pr_lines_ids.mapped('request_state') and pr_lines_ids:    
            return {
                'name': ("Purchase Request Short Close Wizard"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.request.short.close.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('purchase_base_18.view_purchase_request_short_close_wizard_form').id, 'form')],
                'target': 'new',                
                'context': dict(self._context,default_y_purchase_request_id=pr_lines_ids[0].request_id.id,default_y_pr_lines_ids = pr_lines_ids.ids)
            }
        elif any(pr_lines_ids.filtered(lambda x:x.request_state not in ('approved','partial'))):
            raise UserError(_('Purchase Request Short Close can be processed only if the Request is in Purchase Request or Partial State!'))

class PurchaseRequest(models.Model):
    _inherit = "purchase.request" 

    def purchase_request_short_close_form_wizard(self):
        pr_lines_ids = self.env['purchase.request.line']
        pr_lines = self.line_ids.filtered(lambda line: line.y_is_short_closed == False)
        for line in pr_lines:
            purchase_done_quantity = sum(line.purchase_lines.filtered(lambda x:x.state in ('done','purchase')).mapped('product_qty'))
            if line.product_qty > purchase_done_quantity:
                pr_lines_ids += line                      
        if self.state in ('approved','partial') and pr_lines_ids:    
            return {
                'name': ("Purchase Request Short Close Wizard"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.request.short.close.wizard',
                'view_mode': 'form',
                'views': [(self.env.ref('purchase_base_18.view_purchase_request_short_close_wizard_form').id, 'form')],
                'target': 'new',                
                'context': dict(self._context,default_y_purchase_request_id=self.id,default_y_pr_lines_ids = pr_lines_ids.ids)
            }
        elif self.state not in ['approved','partial']:
            raise UserError(_('Purchase Request Short Close can be processed only if the Request is in Purchase Request or Partial State!'))
