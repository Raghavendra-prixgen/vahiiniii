from odoo import models, fields,api
from lxml import etree
import json
import logging
_logger = logging.getLogger(__name__)

from odoo.osv.expression import AND
import ast
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression

class Model(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_views(self, views, options=None):

        res = super().get_views(views, options)

        # Check if form view exists
        if res['views'].get('form') and res['views']['form'].get('arch') and self.env.uid in self.env['ir.model.access'].get_readonly_users_hide_chatter():

            try:
                # Parse XML
                doc = etree.XML(res['views']['form']['arch'])

                # Find and remove the <chatter> tag directly
                for node in doc.xpath("//chatter"):
                    node.getparent().remove(node)

                # Convert back to string and update the response
                res['views']['form']['arch'] = etree.tostring(doc, encoding='unicode')

            except Exception as e:
                print(f"Error parsing form view XML: {e}")

        hidden_view_ids = self.env['ax.access.model'].sudo().search([]).mapped('view_ids')
        user_ids = self.env['ir.model.access'].general_get_readonly_users()

        # FIXED: More selective button hiding based on configured buttons
        if self.env.uid in user_ids:
            current_user = self.env.user
            current_model = self._name
            
            # Get access model configuration for current user
            access_models = self.env['ax.access.model'].sudo().search([
                ('ax_user_ids', 'in', current_user.id)
            ])
            
            # Get specific buttons to hide for this model
            buttons_to_hide = set()
            for access_model in access_models:
                for button_model in access_model.button_model_ids:
                    if button_model.model_id.model == current_model and button_model.button_object_id:
                        buttons_to_hide.add(button_model.button_object_id.button_name)
            
            # Only hide specific configured buttons, not all buttons
            if buttons_to_hide:
                for view_type, view_info in res['views'].items():
                    if isinstance(view_info, dict) and 'arch' in view_info:
                        try:
                            doc = etree.XML(view_info['arch'])

                            # Only remove specific configured buttons
                            for button_name in buttons_to_hide:
                                for node in doc.xpath(f"//button[@name='{button_name}'][@type='object']"):
                                    node.getparent().remove(node)

                            res['views'][view_type]['arch'] = etree.tostring(doc, encoding='unicode')

                        except Exception as e:
                            print(f"Error while removing specific buttons from {view_type} view: {e}")

        if self.env.uid in user_ids:
            for view_type, view_info in res['views'].items():
                if isinstance(view_info, dict) and 'arch' in view_info and view_info.get('id') in hidden_view_ids.ids:
                    if view_type == 'form':
                        res['views'][view_type]['arch'] = '<form></form>'
                    elif view_type == 'list':
                        res['views'][view_type]['arch'] = '<list></list>'
                    elif view_type == 'kanban':
                        res['views'][view_type]['arch'] = '''
                                        <kanban>
                                            <templates>
                                                <t t-name="kanban-box">
                                                    <div class="oe_kanban_global_click">No Content</div>
                                                </t>
                                            </templates>
                                        </kanban>
                                    '''
                    elif view_type == 'calendar':
                        res['views'][view_type]['arch'] = '<calendar></calendar>'
                    elif view_type == 'pivot':
                        res['views'][view_type]['arch'] = '<pivot></pivot>'
                    elif view_type == 'graph':
                        res['views'][view_type]['arch'] = '<graph></graph>'
                    elif view_type == 'activity':
                        res['views'][view_type]['arch'] = '<activity></activity>'
                    elif view_type == 'gantt':
                        res['views'][view_type]['arch'] = '<gantt></gantt>'
                    elif view_type == 'search':
                        res['views'][view_type]['arch'] = '<search></search>'
                    elif view_type == 'cohort':
                        res['views'][view_type]['arch'] = '<cohort></cohort>'
                    elif view_type == 'dashboard':
                        res['views'][view_type]['arch'] = '<dashboard></dashboard>'
                    else:
                        res['views'][view_type]['arch'] = '<sheet></sheet>'


        # 💡 FIELD HIDING BASED ON `field_ids` IN ax.access.model
        user = self.env.user
        current_model = self._name

        # Step 1: Get all access rules for current user
        all_rules = self.env['ax.access.model'].sudo().search([
            ('ax_user_ids', 'in', user.id)
        ])

        # Step 2: Filter rules for the current model
        access_rules = all_rules.filtered(
            lambda r: r.field_ids and any(f.model_id.model == current_model for f in r.field_ids))

        # Step 3: Extract fields to hide
        fields_to_hide = set()
        for rule in access_rules:
            for field in rule.field_ids:
                if field.model_id.model == current_model:
                    fields_to_hide.add(field.name)

        if fields_to_hide:
            for view_type, view_info in res['views'].items():
                if isinstance(view_info, dict) and 'arch' in view_info:
                    try:
                        doc = etree.XML(view_info['arch'])
                        for field_name in fields_to_hide:
                            for node in doc.xpath(f"//field[@name='{field_name}']"):
                                node.set('invisible', '1')
                                # Properly modify the modifiers JSON
                                modifiers = node.get('modifiers') or '{}'
                                modifiers_dict = json.loads(modifiers)
                                modifiers_dict['invisible'] = True
                                node.set('modifiers', json.dumps(modifiers_dict))
                        res['views'][view_type]['arch'] = etree.tostring(doc, encoding='unicode')
                    except Exception as e:
                        print(f"Error hiding fields in {view_type} view: {e}")

        access_model = self.env['ax.access.model'].sudo().search([('ax_user_ids', 'in', user.id)], limit=1)
        model_name = self._name

        if access_model:
            # Get all hidden tabs (label or name) for this model
            hidden_tab_names = access_model.hide_tab_ids.filtered(
                lambda tab: tab.model_id and tab.model_id.model == model_name
            ).mapped('tab_object_id.tab_name')

            if hidden_tab_names and 'form' in res['views'] and 'arch' in res['views']['form']:
                try:
                    doc = etree.XML(res['views']['form']['arch'])

                    for tab_name in hidden_tab_names:
                        for page in doc.xpath(f"//page[@name='{tab_name}']"):
                            page.getparent().remove(page)

                    res['views']['form']['arch'] = etree.tostring(doc, encoding='unicode')

                except Exception as e:
                    print(f"Error hiding tabs in form view: {e}")

        return res

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        model_name = self._name
        current_user = self.env.user

        access_model = self.env['ax.access.model'].sudo().search([
            ('ax_user_ids', 'in', current_user.id)
        ])

        additional_domain = []
        for rule in access_model.mapped('model_domain_ids'):
            if rule.model_id.model == model_name and rule.ax_domain:
                try:
                    eval_domain = safe_eval(rule.ax_domain, {
                        'uid': current_user.id,
                        'user': current_user
                    })
                    if isinstance(eval_domain, list):
                        additional_domain = expression.AND([additional_domain, eval_domain])
                        _logger.info(f"[AX_ACCESS] Domain for {model_name}: {eval_domain}")
                except Exception as e:
                    _logger.warning(f"[AX_ACCESS] Domain eval failed for {model_name}: {e}")

        domain = expression.AND([domain or [], additional_domain])

        return super().web_search_read(
            domain,
            specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit
        )

class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    def general_get_readonly_users(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users_hide_chatter(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
            WHERE a.hide_chatter = TRUE;
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users_import(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
            WHERE a.hide_import = TRUE;
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users_export(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
            WHERE a.hide_export = TRUE;
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
            WHERE a.make_readonly_whole_system = TRUE;
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users_model_wise(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.id
            FROM res_users u
            JOIN ax_model_user_rel rel ON u.id = rel.user_id
            JOIN ax_access_model a ON rel.ax_acce_id = a.id  -- Correct join condition
            WHERE a.is_readonly_models = TRUE;
        """)

        users = self.env.cr.fetchall()
        return [user[0] for user in users]  # Extract user IDs

    @api.model
    def get_readonly_users_model_all_selected_models(self):
        self.env.cr.execute("""
            SELECT DISTINCT u.model
            FROM ir_model u
            JOIN ax_access_model_rel rel ON u.id = rel.model_id
            JOIN ax_access_model a ON rel.ax_model_id = a.id
        """)

        models = self.env.cr.fetchall()
        return [model[0] for model in models]  # Extract user IDs

    @api.model
    def check(self, model, mode='read', raise_exception=True):
        # Fetch records where make_readonly_whole_system is True
        # Collect all users from ax_user_ids
        readonly_users = self.get_readonly_users()
        readonly_modelwise_users = self.get_readonly_users_model_wise()
        readonly_models = self.get_readonly_users_model_all_selected_models()
        ax_mode = ['write','create','unlink']
        ax_mode_all = ['read','write','create','unlink']

        if (mode in ax_mode) and (self.env.uid in readonly_users):
            return False
        if (mode in ax_mode) and (self.env.uid in readonly_modelwise_users) and (model in readonly_models) :
            return False

        if mode == 'read' and (self.env.uid in self.get_readonly_users_hide_chatter()) and (model in ["mail.thread", "mail.activity.mixin","mail.tracking.value","mail.notification",'res.users.log', 'mail.channel', 'mail.alias'
                 'mail.channel.member','mail.activity']):
            return False

        if mode in ax_mode_all and (self.env.uid in self.get_readonly_users_import()) and (model in ["base_import.import"]):
            return False

        if mode == ax_mode_all and (self.env.uid in self.get_readonly_users_export()) and (model in ["base_import.import"]):
            return False

        return super().check(model,mode,raise_exception)