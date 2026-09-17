from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.export import ExcelExport
from odoo.exceptions import AccessError,UserError
from odoo.http import request
from odoo import http, fields, models, _
import odoo
import odoo.modules.registry
from odoo.exceptions import AccessDenied
from odoo.addons.web.controllers.utils import ensure_db
import ipaddress
import logging
from datetime import datetime
from odoo.addons.web.controllers.home import Home,CREDENTIAL_PARAMS


_logger = logging.getLogger(__name__)

SIGN_UP_REQUEST_PARAMS = {
    'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
    'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
    'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'
}


class HomeCustom(Home):
    @http.route('/web/login', type='http', auth='none', readonly=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_successful'] = False

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            ip_address = request.httprequest.environ.get('REMOTE_ADDR')
            login_username = request.params.get('login')
            user_password = request.params.get('password')

            user_record = request.env['res.users'].sudo().search([('login', '=', login_username)], limit=1)
            login_allowed = True

            if user_record:
                # Fetch access configurations and allowed IP addresses
                access_configurations = request.env['ax.access.model'].sudo().search([
                    ('ax_user_ids', 'in', user_record.id)
                ])
                allowed_ips = []
                for config in access_configurations:
                    allowed_ips += [ip.ip_address for ip in config.allowed_ips]

                # Validate IP restrictions if configured
                if allowed_ips and ip_address not in allowed_ips:
                    login_allowed = False
                    values['error'] = _("Login from this IP is not permitted: %s") % ip_address
                    self._record_failed_login_attempt(user_record, ip_address, login_username, success=False)
                    self._notify_admin_blocked_login(user_record, ip_address)

            if login_allowed:
                try:
                    credentials = {
                        key: value
                        for key, value in request.params.items()
                        if key in CREDENTIAL_PARAMS and value
                    }
                    credentials.setdefault('type', 'password')
                    auth_info = request.session.authenticate(request.db, credentials)
                    request.params['login_successful'] = True
                    return request.redirect(self._login_redirect(auth_info['uid'], redirect=redirect))
                except AccessDenied as e:
                    self._record_failed_login_attempt(user_record, ip_address, login_username, success=False)
                    if e.args == AccessDenied().args:
                        values['error'] = _("Incorrect login/password")
                    else:
                        values['error'] = e.args[0]

        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Access restricted to employees only. Please contact your administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _record_failed_login_attempt(self, user_record, ip_address, login_username, success):
        if not success:
            request.env['unauthorized.access.log'].sudo().create({
                'user_id': user_record.id if user_record else None,
                'ip_address': ip_address,
                'attempt_date': datetime.now(),
            })
        _logger.info("Login attempt [%s] for user '%s' from IP %s",
                     "SUCCESS" if success else "FAILED",
                     login_username, ip_address)

    def _notify_admin_blocked_login(self, user_record, ip_address):
        admin_emails = request.env['res.users'].sudo().search(
            [('groups_id', 'in', [request.env.ref('base.group_system').id]), ('email', '!=', False)]).mapped('email')
        if not admin_emails:
            _logger.error("No admin email found to send blocked login notification")
            return

        admin_emails_str = ', '.join(admin_emails)
        _logger.info("Admin emails: %s", admin_emails_str)
        mail_template = request.env.ref('centralized_access_management.email_template_blocked_login',
                                        raise_if_not_found=False)

        if mail_template:
            ctx = {
                'default_model': 'res.users',
                'default_res_id': user_record.id,
                'default_use_template': True,
                'default_template_id': mail_template.id,
                'default_composition_mode': 'comment',
                'blocked_ip': ip_address,
                'email_to': admin_emails_str,
                "lang": user_record.lang or "en_US",
            }
            _logger.info("Context for email: %s", ctx)
            mail_template.sudo().with_context(ctx).send_mail(user_record.id, force_send=True)
        else:
            _logger.error("Email template not found")


class AxAccessController(http.Controller):

    @http.route('/ax_access/can_debug', type='json', auth='user')
    def can_debug(self):
        user_id = request.env.user.id

        access_record = request.env['ax.access.model'].sudo().search([
            ('disable_develop_mode', '=', True),
            ('ax_user_ids', 'in', [user_id])
        ], limit=1)

        return {
            'can_debug': not bool(access_record),  # If record exists, then debug is disabled
            'user_id': user_id,
        }

class CustomExportRestriction(ExcelExport):
    @http.route('/web/export/xlsx', type='http', auth='user')
    def web_export_xlsx(self, data):
        """Restrict export based on user permissions"""
        readonly_users = request.env['ir.model.access'].sudo().get_readonly_users_export()  # Ensure correct model
        if request.env.uid in readonly_users:
            raise UserError("You do not have permission to export data.")  # Friendly warning
        return super().web_export_xlsx(data)
