from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    company_id = fields.Many2one('res.company','Company',required=False)
    y_is_branch_to_branch_operation = fields.Boolean(string='Branch To Branch Transfer Operation',copy=False)

    @api.constrains('y_is_branch_to_branch_operation','company_id')
    def check_is_stock_transfer_operation(self):
        for rec in self:
            docs = rec.env['stock.picking.type'].search([('y_is_branch_to_branch_operation','=',True)])
            if len(docs) > 1:
                raise ValidationError(_("""Branch To Branch Transfer Operation already exists!"""))

    def unlink(self):
        for rec in self:
            if rec.y_is_branch_to_branch_operation == True:
                raise UserError("Branch To Branch Transfer Operation cannot be Deleted")
        res = super(StockPickingType,self).unlink()
        return res