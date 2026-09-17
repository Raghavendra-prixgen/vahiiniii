from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('location_id', 'location_dest_id')
    def _check_restricted_locations(self):
        for picking in self:
            user = self.env.user
            restricted_locations = user.restricted_location_ids

            if not restricted_locations:
                continue # Admins and users with no restrictions are exempt

            if picking.location_id in restricted_locations:
                raise UserError(_("You are not allowed to use the source location '%s'. Please contact your administrator.") % picking.location_id.display_name)
            
            if picking.location_dest_id in restricted_locations:
                raise UserError(_("You are not allowed to use the destination location '%s'. Please contact your administrator.") % picking.location_dest_id.display_name)