from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class BranchTransferShortCloseReason(models.Model):
    _name = 'barch.transfer.short.close.reason'
    _description = 'Branch To Branch Transfer Short Close Reason'
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")

class BranchTransferShortClose(models.TransientModel):
    _name = 'barch.transfer.short.close'
    _description = 'BTB Short Close Wizard'

    y_btb_id = fields.Many2one('branch.to.branch.transfer',string="Branch Transfer")
    y_reason_id = fields.Many2one('barch.transfer.short.close.reason',string="Reason")

    def action_done(self):
        if self.y_reason_id:
            self.y_btb_id.y_closed = True
            self.y_btb_id.y_short_close_reason_id = self.y_reason_id.id
        else:
            raise ValidationError(_('''Please provide a valid reason'''))