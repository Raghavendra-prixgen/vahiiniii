from odoo import http,models, fields,api
from odoo.exceptions import ValidationError, AccessDenied
from odoo import _, exceptions
from odoo.http import request

# class IrHttp(models.AbstractModel):
#     _inherit = 'ir.http'
#
#     @classmethod
#     def _handle_debug(self):
#         group = request.env['ir.model.access'].search([]).mapped('disable_develop_mode')
#         user_ids = request.env['ir.model.access'].general_get_readonly_users()
#         if group in ['', 1]:
#             request.session.debug = 0
#         else:
#             return super(IrHttp, self)._handle_debug()

class AxAccessModel(models.Model):
    _name = 'ax.access.model'
    _description = 'Access Control Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True,copy=False, tracking=True)
    disable_develop_mode = fields.Boolean(string='Turn Off Developer Mode',copy=False,tracking=True)
    make_readonly_whole_system = fields.Boolean(string='System Readonly Mode',copy=False,tracking=True)
    ax_user_ids = fields.Many2many('res.users','ax_model_user_rel','ax_acce_id','user_id',domain="[('share', '=', False)]" ,string="Users",copy=False,tracking=True)

    is_readonly_models = fields.Boolean("Set Models as Readonly",tracking=True)
    readonly_model_ids = fields.Many2many('ir.model','ax_access_model_rel','ax_model_id','model_id' ,string='ReadOnlyModels',help="The models which are readonly for above selected users",tracking=True)

    hide_chatter = fields.Boolean("Hide Chatter",tracking=True)
    hide_send_message = fields.Boolean("Hide Send Message",tracking=True)
    hide_log_note = fields.Boolean("Hide Log Note",tracking=True)
    hide_schedule_activity = fields.Boolean("Hide Schedule Activity",tracking=True)
    hide_import = fields.Boolean("Hide Import",tracking=True)
    hide_export = fields.Boolean("Hide Export",tracking=True)

    allowed_ips = fields.One2many(
        "allowed.ips",
        "access_config_id",
        string="Allowed IP Ranges",
        help="List of IP ranges permitted for user access under this configuration."
    )

    view_ids = fields.Many2many(
        'ir.ui.view',
        'ax_access_view_rel',
        'ax_model_id',
        'access_view_id',
        string="View Access"
    )
    button_model_ids = fields.Many2many('button.model',string="Hide Buttons",tracking=True)

    field_ids = fields.Many2many('ir.model.fields', string="Fields to Hide",tracking=True)
    hide_tab_ids = fields.Many2many('ax.hidden.tab', string="Hide Buttons",tracking=True)
    # hidden_tab_ids = fields.One2many('ax.hidden.tab', 'access_model_id', string='Hidden Tabs')
    model_id = fields.Many2one('ir.model', string="Model")
    model_domain_ids = fields.One2many(
        'access.model.domain.rule', 'access_config_id', string="Model Domain Rules")

    def _check_menu_user_is_admin(self):
        """
        Compute method to verify if the user has admin privileges.
        The menu items will be hidden for non-admin users.
        """
        for rec in self:
            rec.is_admin = False
            if rec.id == self.env.ref('base.user_admin').id:
                rec.is_admin = True

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu', string="Menus to Hide",
        store=True, help='Choose the menus that should be hidden from this user.')
    is_admin = fields.Boolean(compute=_check_menu_user_is_admin, string="Has Admin Access",
                              help='True if the user has admin privileges.')

    # for access control permission
    @api.model
    def create(self, vals):
        if not self.env.user.has_group("base.group_system"):
            raise exceptions.AccessError("You do not have permission to create access control configurations.")
        return super(AxAccessModel, self).create(vals)

    # for ip address access groups
    @api.constrains('ax_user_ids')
    def _check_required_groups_for_users(self):
        for record in self:
            for user in record.ax_user_ids:
                access_groups = ["Access User", "Access Manager"]
                rights_groups = ["Access Rights", "Settings"]

                user_group_names = [group.name for group in user.groups_id]

                access_group_selected = any(
                    group in user_group_names for group in access_groups
                )
                rights_group_selected = any(
                    group in user_group_names for group in rights_groups
                )

                if (
                        "Access Manager" in user_group_names
                        and "Settings" not in user_group_names
                ):
                    raise ValidationError(
                        f"User '{user.name}': The 'Access Manager' group must be assigned along with the 'Settings' group."
                    )

                if (
                        "Settings" in user_group_names
                        and "Access Manager" not in user_group_names
                ):
                    raise ValidationError(
                        f"User '{user.name}': The 'Settings' group must be assigned along with the 'Access Manager' group."
                    )

                if (
                        "Access User" in user_group_names
                        and "Access Rights" not in user_group_names
                ):
                    raise ValidationError(
                        f"User '{user.name}': The 'Access User' group must be assigned along with the 'Access Rights' group."
                    )

                if (
                        "Access Rights" in user_group_names
                        and "Access User" not in user_group_names
                ):
                    raise ValidationError(
                        f"User '{user.name}': The 'Access Rights' group must be assigned along with the 'Access User' group."
                    )

                if not access_group_selected:
                    raise ValidationError(
                        f"User '{user.name}': Please assign at least one of the following groups: 'Access User' or 'Access Manager'."
                    )

                if not rights_group_selected:
                    raise ValidationError(
                        f"User '{user.name}': Please assign at least one of the following groups: 'Access Rights' or 'Settings'."
                    )


    # for hide menu
    def write(self, vals):
        # Store old state before updating
        old_data = {
            rec.id: {
                'ax_user_ids': set(rec.ax_user_ids.ids),
                'hide_menu_ids': set(rec.hide_menu_ids.ids)
            }
            for rec in self
        }

        res = super(AxAccessModel, self).write(vals)

        for record in self:
            new_user_ids = set(record.ax_user_ids.ids)
            old_user_ids = old_data.get(record.id, {}).get('ax_user_ids', set())

            new_menu_ids = set(record.hide_menu_ids.ids)
            old_menu_ids = old_data.get(record.id, {}).get('hide_menu_ids', set())

            removed_users = old_user_ids - new_user_ids  # Users removed from ax_user_ids
            current_users = new_user_ids  # Users still inside ax_user_ids

            removed_menus = old_menu_ids - new_menu_ids  # Menus removed from hide_menu_ids

            # ✅ Restore menu access for removed users
            if removed_users:
                affected_menus = self.env['ir.ui.menu'].browse(list(new_menu_ids))  # Only affect hidden menus
                for menu in affected_menus:
                    existing_restricted_users = set(menu.restrict_user_ids.ids)
                    updated_users = existing_restricted_users - removed_users  # Remove only removed users
                    menu.write({'restrict_user_ids': [(6, 0, list(updated_users))]})

            # ✅ Restore menu access for removed menus
            if removed_menus:
                removed_menu_records = self.env['ir.ui.menu'].browse(list(removed_menus))
                for menu in removed_menu_records:
                    existing_restricted_users = set(menu.restrict_user_ids.ids)
                    updated_users = existing_restricted_users - current_users
                    menu.write({'restrict_user_ids': [(6, 0, list(updated_users))]})

            # ✅ Apply restriction for newly added menus
            if new_menu_ids:
                new_menu_records = self.env['ir.ui.menu'].browse(list(new_menu_ids))
                for menu in new_menu_records:
                    existing_restricted_users = set(menu.restrict_user_ids.ids)
                    updated_users = existing_restricted_users | current_users
                    menu.write({'restrict_user_ids': [(6, 0, list(updated_users))]})

        return res

    @api.onchange("make_readonly_whole_system")
    def _onchange_make_readonly_whole_system(self):
        if self.make_readonly_whole_system:
            return {
                "warning": {
                    "title": "Warning!",
                    "message": "If you enable this, All Selected Users will be Readonly for the whole System!",
                }
            }



    @staticmethod
    def is_dev_mode_allowed(user_id):
        # If any record restricts the user, return False
        access_recs = request.env['ax.access.model'].sudo().search([
            ('disable_develop_mode', '=', True),
            ('ax_user_ids', 'in', user_id),
        ])
        return not bool(access_recs)


# Controller to expose it to JS
class AxAccessController(http.Controller):
    @http.route('/ax_access/dev_mode_allowed', type='json', auth='user')
    def check_dev_mode_allowed(self):
        user_id = request.env.uid
        allowed = AxAccessModel.is_dev_mode_allowed(user_id)
        return {'dev_mode_allowed': allowed}
