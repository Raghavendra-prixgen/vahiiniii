# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError
from lxml import etree
import json

class ResGroups(models.Model):
    _inherit = 'res.groups'


    def get_application_groups(self, domain):
        group_ids = []                    
        item_group_id = self.env.ref('inventory_base.item_group_make_invisible').id
        if item_group_id:
            group_ids.append(item_group_id)

        product_group_1_id = self.env.ref('inventory_base.product_group_1_make_invisible').id
        if product_group_1_id:
            group_ids.append(product_group_1_id)
            
        product_group_2_id = self.env.ref('inventory_base.product_group_2_make_invisible').id
        if product_group_2_id:
            group_ids.append(product_group_2_id)
            
        product_group_3_id = self.env.ref('inventory_base.product_group_3_make_invisible').id
        if product_group_3_id:
            group_ids.append(product_group_3_id)
        if len(group_ids):
            return super(ResGroups, self).get_application_groups(domain + [('id', 'not in', group_ids)])
        else:
            return super(ResGroups, self).get_application_groups(domain)


class ProductGroupConfiguration(models.Model):
    _name = 'product.group.config'
    _inherit = ['mail.thread']
    _rec_name = 'y_name'

    y_name = fields.Char(string="Item Group",tracking=True)
    y_product_group_1 = fields.Char(string="Product Group 1",tracking=True)
    y_product_group_2 = fields.Char(string="Product Group 2",tracking=True)
    y_product_group_3 = fields.Char(string="Product Group 3",tracking=True)

    y_is_item_group_required = fields.Boolean(string="Item Group Required",tracking=True)
    y_is_product_group_1_required = fields.Boolean(string="Product Group 1 Required",tracking=True)
    y_is_product_group_2_required = fields.Boolean(string="Product Group 2 Required",tracking=True)
    y_is_product_group_3_required = fields.Boolean(string="Product Group 3 Required",tracking=True)

    y_is_item_group_invisible = fields.Boolean(string="Item Group Invisible",tracking=True)
    y_is_product_group_1_invisible = fields.Boolean(string="Product Group 1 Invisible",tracking=True)
    y_is_product_group_2_invisible = fields.Boolean(string="Product Group 2 Invisible",tracking=True)
    y_is_product_group_3_invisible = fields.Boolean(string="Product Group 3 Invisible",tracking=True)
    y_state = fields.Selection([('edit','Edit'),('locked','Locked')],default='edit',tracking=True,string="State")

    def action_unlock(self):
        self.write({'y_state':'edit'})

    def action_locked(self):
        self.write({'y_state':'locked'})

    @api.model
    def create(self,vals):
        access_record_rule_obj = self.env['product.group.config'].sudo().search([])
        if access_record_rule_obj:
            raise UserError(_("Configuration already done"))
        return super().create(vals)

    def write(self,vals):
        res = super().write(vals)
        for rec in self:
            if not rec.y_is_item_group_invisible:
                product_group_id = self.env.ref('inventory_base.item_group_make_invisible')
                user_id = self.env.user
                if product_group_id:
                    product_group_id.write({'users': [(3, user_id.id)]})

            else:
                product_group_id = self.env.ref('inventory_base.item_group_make_invisible')
                if product_group_id:
                    user_id = self.env.user
                    if user_id not in product_group_id.users:
                        product_group_id.write({'users': [(4, user_id.id)]})

            
            if not rec.y_is_product_group_1_invisible:
                product_group_id = self.env.ref('inventory_base.product_group_1_make_invisible')
                user_id = self.env.user
                if product_group_id:
                    product_group_id.write({'users': [(3, user_id.id)]})
            else:
                product_group_id = self.env.ref('inventory_base.product_group_1_make_invisible')
                if product_group_id:
                    user_id = self.env.user
                    if user_id not in product_group_id.users:
                        product_group_id.write({'users': [(4, user_id.id)]})

            if not rec.y_is_product_group_2_invisible:
                product_group_id = self.env.ref('inventory_base.product_group_2_make_invisible')
                user_id = self.env.user
                if product_group_id:
                    product_group_id.write({'users': [(3, user_id.id)]})
            else:
                product_group_id = self.env.ref('inventory_base.product_group_2_make_invisible')
                if product_group_id:
                    user_id = self.env.user
                    if user_id not in product_group_id.users:
                        product_group_id.write({'users': [(4, user_id.id)]})

            if not rec.y_is_product_group_3_invisible:
                product_group_id = self.env.ref('inventory_base.product_group_3_make_invisible')
                user_id = self.env.user
                if product_group_id:
                    product_group_id.write({'users': [(3, user_id.id)]})
            else:
                product_group_id = self.env.ref('inventory_base.product_group_3_make_invisible')
                if product_group_id:
                    user_id = self.env.user
                    if user_id not in product_group_id.users:
                        product_group_id.write({'users': [(4, user_id.id)]})


        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"


    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_mandetory(field):
            field.set('required', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['required'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)
        
        
        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])

            # Fields Lables
            node = doc.xpath("//field[@name='y_item_group']")
            if node:
                node[0].set('string',access_record_rule_obj.y_name)

            node = doc.xpath("//field[@name='y_product_group_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_form_invisible(field)
            if view_type == 'tree':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_invisible(field)

            # Fields Mandetory
            doc = etree.fromstring(result['arch'])
            if access_record_rule_obj.y_is_item_group_required:
                for field in doc.xpath('//field[@name="y_item_group"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_1_required:
                for field in doc.xpath('//field[@name="y_product_group_1"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_2_required:
                for field in doc.xpath('//field[@name="y_product_group_2"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_3_required:
                for field in doc.xpath('//field[@name="y_product_group_3"]'):
                    make_mandetory(field)
        return result


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_mandetory(field):
            field.set('required', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['required'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])
            node = doc.xpath("//field[@name='y_item_group']")
            if node:
                node[0].set('string',access_record_rule_obj.y_name)

            node = doc.xpath("//field[@name='y_product_group_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_form_invisible(field)
            if view_type == 'tree':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_invisible(field)

            # Fields Mandetory
            doc = etree.fromstring(result['arch'])
            if access_record_rule_obj.y_is_item_group_required:
                for field in doc.xpath('//field[@name="y_item_group"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_1_required:
                for field in doc.xpath('//field[@name="y_product_group_1"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_2_required:
                for field in doc.xpath('//field[@name="y_product_group_2"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_3_required:
                for field in doc.xpath('//field[@name="y_product_group_3"]'):
                    make_mandetory(field)

        
        return result

class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_mandetory(field):
            field.set('required', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['required'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])
            node = doc.xpath("//field[@name='y_item_group']")
            if node:
                node[0].set('string',access_record_rule_obj.y_name)

            node = doc.xpath("//field[@name='y_product_group_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_form_invisible(field)
            if view_type == 'tree':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_invisible(field)

            # Fields Mandetory
            doc = etree.fromstring(result['arch'])
            if access_record_rule_obj.y_is_item_group_required:
                for field in doc.xpath('//field[@name="y_item_group"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_1_required:
                for field in doc.xpath('//field[@name="y_product_group_1"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_2_required:
                for field in doc.xpath('//field[@name="y_product_group_2"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_3_required:
                for field in doc.xpath('//field[@name="y_product_group_3"]'):
                    make_mandetory(field)

        
        return result


    
class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_mandetory(field):
            field.set('required', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['required'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])
            node = doc.xpath("//field[@name='y_item_group']")
            if node:
                node[0].set('string',access_record_rule_obj.y_name)

            node = doc.xpath("//field[@name='y_product_group_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_form_invisible(field)

            if view_type == 'tree':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_invisible(field)

            # Fields Mandetory
            doc = etree.fromstring(result['arch'])
            if access_record_rule_obj.y_is_item_group_required:
                for field in doc.xpath('//field[@name="y_item_group"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_1_required:
                for field in doc.xpath('//field[@name="y_product_group_1"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_2_required:
                for field in doc.xpath('//field[@name="y_product_group_2"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_3_required:
                for field in doc.xpath('//field[@name="y_product_group_3"]'):
                    make_mandetory(field)
        
        return result


    
class StockMove(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def get_view(self, view_id=None, view_type=None, **options):
        result = super().get_view(view_id, view_type, **options)
        def make_form_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_invisible(field):
            field.set('invisible', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['tree_invisible'] = True
            modifiers['column_invisible'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)

        def make_mandetory(field):
            field.set('required', '1')
            modifiers = json.loads(field.get('modifiers', '{}'))
            modifiers['required'] = True
            field.set('modifiers', json.dumps(modifiers))
            result['arch'] = etree.tostring(doc)


        access_record_rule_obj = self.env['product.group.config'].sudo().search([],limit=1)
        if access_record_rule_obj:
            doc = etree.XML(result['arch'])
            node = doc.xpath("//field[@name='y_item_group']")
            if node:
                node[0].set('string',access_record_rule_obj.y_name)

            node = doc.xpath("//field[@name='y_product_group_1']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_1)

            node = doc.xpath("//field[@name='y_product_group_2']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_2)

            node = doc.xpath("//field[@name='y_product_group_3']")
            if node:
                node[0].set('string',access_record_rule_obj.y_product_group_3)

            result['arch'] = etree.tostring(doc, encoding='unicode')

            # Fields Invisible
            if view_type == 'form':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_form_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_form_invisible(field)

            if view_type == 'tree':
                doc = etree.fromstring(result['arch'])
                if not access_record_rule_obj.y_is_item_group_invisible:
                    for field in doc.xpath('//field[@name="y_item_group"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_1_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_1"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_2_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_2"]'):
                        make_invisible(field)
                if not access_record_rule_obj.y_is_product_group_3_invisible:
                    for field in doc.xpath('//field[@name="y_product_group_3"]'):
                        make_invisible(field)

            # Fields Mandetory
            doc = etree.fromstring(result['arch'])
            if access_record_rule_obj.y_is_item_group_required:
                for field in doc.xpath('//field[@name="y_item_group"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_1_required:
                for field in doc.xpath('//field[@name="y_product_group_1"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_2_required:
                for field in doc.xpath('//field[@name="y_product_group_2"]'):
                    make_mandetory(field)
            if access_record_rule_obj.y_is_product_group_3_required:
                for field in doc.xpath('//field[@name="y_product_group_3"]'):
                    make_mandetory(field)
        
        return result