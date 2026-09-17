from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    restricted_location_ids = fields.Many2many(
        'stock.location',
        'res_users_stock_location_rel',
        'user_id',
        'location_id',
        string='Restricted Locations',
        help="Locations that this user is NOT allowed to access or select in transactions."
    )

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'restricted_location_ids' in vals:
            rule = self.env.ref('user_restricted_locations.stock_location_user_restricted_rule', raise_if_not_found=False)
            if rule:
                self.env['ir.rule'].clear_caches()
                self.env['stock.location']._invalidate_cache()
                self.env.cr.execute("COMMIT")
        return res