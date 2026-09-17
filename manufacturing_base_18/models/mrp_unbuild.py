from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpUnbuildInherit(models.Model):
    _inherit = "mrp.unbuild"

    @api.onchange("product_qty")
    def quantity_validation(self):
        for rec in self:
            if rec.product_qty > 1 and rec.product_qty > rec.mo_id.product_qty:
                rec.product_qty = rec.mo_id.product_qty
                return {'warning': {'title': _('User Warning'), 'message': _('You cannot Unbuild more than manufactured quantity!'),},
                            }    
    @api.model
    def create(self,vals):
        production = self.env['mrp.production'].search([('id','=',vals.get('mo_id'))])        
        if (vals.get('product_qty')) > production.product_qty:
            raise UserError("You cannot Unbuild more than manufactured quantity!")
        return super(MrpUnbuildInherit,self).create(vals)
