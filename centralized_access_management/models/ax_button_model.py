from odoo import models, fields, api
from lxml import etree
from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)


class CustomModelAction(models.Model):
    _name = 'custom.model.action'
    _description = 'Custom Model Action'

    name = fields.Char(string="Action Name", required=True)
    model_id = fields.Many2one('ir.model', string="Model", required=True,ondelete='cascade')
    method = fields.Char(string="Method", required=True)

class TabActionModel(models.Model):
    _name = 'tab.action.model'
    _description = 'Model-wise tab Actions'
    _rec_name = 'tab_name'

    model_id = fields.Many2one('ir.model', string=" Model", required=True, ondelete='cascade')
    tab_name = fields.Char(string="tab Name", required=True)
    tab_label = fields.Char(string="tab Label", required=True)
    active = fields.Boolean(string="Active", default=True)


class ButtonActionModel(models.Model):
    _name = 'button.action.model'
    _description = 'Model-wise Button Actions'
    _rec_name = 'button_name'

    model_id = fields.Many2one('ir.model', string=" Model", required=True, ondelete='cascade')
    button_name = fields.Char(string="Button Name", required=True)
    button_label = fields.Char(string="Button Label", required=True)
    active = fields.Boolean(string="Active", default=True)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.button_label} ({rec.button_name})"
            result.append((rec.id, name))
        return result

class AXHiddenTab(models.Model):
    _name = 'ax.hidden.tab'
    _description = 'Hidden Tabs for Access Control'

    model_id = fields.Many2one('ir.model', string="Model", ondelete='set null')
    tab_object_id = fields.Many2one(
        'tab.action.model',
        string="Button Action", domain="[('model_id', '=', model_id)]",

    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if not self.model_id:
            self.tab_object_id = False
            return

        View = self.env['ir.ui.view']
        TabModel = self.env['tab.action.model']
        model_name = self.model_id.model

        views = View.search([('model', '=', model_name), ('type', '=', 'form')])
        existing_tabs = TabModel.search([('model_id', '=', self.model_id.id)])
        existing_tab_names = set(existing_tabs.mapped('tab_name'))

        for view in views:
            try:
                xml_tree = etree.fromstring(view.arch)
                for xpath_expr in ["//page[@string]"]:
                    for page in xml_tree.xpath(xpath_expr):
                        tab_label = page.attrib.get('string')
                        tab_name = page.attrib.get('name', tab_label)

                        if tab_name and tab_name not in existing_tab_names:
                            TabModel.create({
                                'model_id': self.model_id.id,
                                'tab_name': tab_name,
                                'tab_label': tab_label,
                                'active': True,
                            })
            except Exception as e:
                _logger.warning(f"Failed parsing view: {view.name or view.id} - {e}")
                continue

        self.tab_object_id = False

class ButtonModel(models.Model):
    _name = "button.model"
    _description = "Button Model for Model Selection and Action"

    model_id = fields.Many2one('ir.model', string="Model",  ondelete='cascade')
    button_object_id = fields.Many2one(
        'button.action.model',
        string="Button Action",domain="[('model_id', '=', model_id)]",

    )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if not self.model_id:
            self.button_object_id = False
            return

        View = self.env['ir.ui.view']
        ActionModel = self.env['button.action.model']
        model_name = self.model_id.model

        views = View.search([('model', '=', model_name), ('type', '=', 'form')])

        # Load all existing actions for this model to avoid duplicates
        existing_actions = ActionModel.search([('model_id', '=', self.model_id.id)])
        existing_button_names = set(existing_actions.mapped('button_name'))

        for view in views:
            try:
                xml_tree = etree.fromstring(view.arch)
                for button in xml_tree.xpath("//button[@name][@type='object']"):
                    button_name = button.attrib['name']
                    button_label = button.attrib.get('string', button_name)

                    # Only create if not already exists
                    if button_name not in existing_button_names:
                        ActionModel.create({
                            'model_id': self.model_id.id,
                            'button_name': button_name,
                            'button_label': button_label,
                            'active': True,
                        })
            except Exception as e:
                _logger.warning(f"Failed parsing view: {view.name or view.id} - {e}")
                continue

        # Refresh domain
        self.button_object_id = False


class AccessModelDomainRule(models.Model):
    _name = 'access.model.domain.rule'
    _description = 'Model Wise Domain Rules'

    access_config_id = fields.Many2one("ax.access.model", string="Access Config", required=True)
    model_id = fields.Many2one('ir.model', string="Model",  ondelete='cascade')
    ax_domain = fields.Char(string="Domain", help="Example: [('user_id', '=', uid)]")

