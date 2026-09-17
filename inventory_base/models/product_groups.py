# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockWarehouse(models.Model):
    _name = "stock.warehouse"
    _inherit = ['stock.warehouse','mail.thread', 'mail.activity.mixin']

    code = fields.Char('Short Name', required=True, size=10, help="Short name used to identify your warehouse")
    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id, check_company=True,tracking=True)

class ItemGroup(models.Model):
    _name = "item.group"
    _description = "Item Group"
    _rec_name = 'y_name'
    # _sql_constraints = [('code_unique', 'unique(code)', 'code already exists!')]

    y_name = fields.Char(string="Name")
    y_code = fields.Char(string="Code")
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    y_product_category_id = fields.Many2one('product.category',string="Product Category",domain=[('y_release', '=', True)])
    active = fields.Boolean(default=True)

    @api.constrains('y_code','company_id')
    def check_item_group_code(self):
        for rec in self:
            docs=rec.env['item.group'].search([('y_code','=',rec.y_code),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""code already exists!"""))



class ProductGroup1(models.Model):
    _name = "product.group.1"
    _description = "Product Group 1"
    _rec_name = 'y_name'
    # _sql_constraints = [('code_unique', 'unique(code)', 'code already exists!')]

    y_name = fields.Char(string="Name")
    y_code = fields.Char(string="Code")
    y_product_category_id = fields.Many2one('product.category',string="Product Category",domain=[('y_release', '=', True)])
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    active = fields.Boolean(default=True)
    y_item_group = fields.Many2one('item.group', ondelete='restrict',string="Item Group")


    @api.constrains('y_code','y_company_id')
    def check_item_group_code(self):
        for rec in self:
            docs=rec.env['product.group.1'].search([('y_code','=',rec.y_code),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""code already exists!"""))


class ProductGroup2(models.Model):
    _name = "product.group.2"
    _description = "Product Group 2"
    _rec_name = 'y_name'
    # _sql_constraints = [('code_unique', 'unique(code)', 'code already exists!')]

    y_name = fields.Char(string="Name")
    y_code = fields.Char(string="Code")
    y_product_group_1 = fields.Many2one('product.group.1',string="Product Group 1")
    y_product_category_id = fields.Many2one('product.category',string="Product Category",domain=[('y_release', '=', True)])
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    active = fields.Boolean(default=True)

    @api.constrains('y_code','y_company_id')
    def check_item_group_code(self):
        for rec in self:
            docs=rec.env['product.group.2'].search([('y_code','=',rec.y_code),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""code already exists!"""))


class ProductGroup3(models.Model):
    _name = "product.group.3"
    _description = "Product Group 3"
    _rec_name = 'y_name'
    # _sql_constraints = [('code_unique', 'unique(code)', 'code already exists!')]

    y_name = fields.Char(string="Name")
    y_code = fields.Char(string="Code")
    y_product_group_2 = fields.Many2one('product.group.2',string="Product Group 2")
    y_product_category_id = fields.Many2one('product.category',string="Product Category",domain=[('y_release', '=', True)])
    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id, index=1)
    active = fields.Boolean(default=True)
    
    @api.constrains('y_code','y_company_id')
    def check_item_group_code(self):
        for rec in self:
            docs=rec.env['product.group.3'].search([('y_code','=',rec.y_code),('y_company_id','=',rec.y_company_id.id)])
            if len(docs) > 1:
                raise ValidationError(_("""code already exists!"""))



class ProductTemplate(models.Model):
    _inherit = "product.template"

    y_item_group = fields.Many2one('item.group',domain="[('y_product_category_id', '=', categ_id)]", ondelete='restrict',string="Item Group")
    y_product_group_1 = fields.Many2one('product.group.1', domain="['|',('y_product_category_id', '=', categ_id),('y_item_group', '=', y_item_group)]", ondelete='restrict',string="Product Group 1")
    y_product_group_2 = fields.Many2one('product.group.2', domain="['|',('y_product_category_id', '=', categ_id),('y_product_group_1', '=', y_product_group_1)]", ondelete='restrict',string="Product Group 2")
    y_product_group_3 = fields.Many2one('product.group.3', domain="['|',('y_product_category_id', '=', categ_id),('y_product_group_2', '=', y_product_group_2)]", ondelete='restrict',string="Product Group 3")


    def write(self,vals):
        if vals.get('y_product_group_2') == False and self.y_product_group_1:
            raise UserError(_('product Group2 is not Mapped'))
    
        if vals.get('y_product_group_3') == False and self.y_product_group_2:
            raise UserError(_('product Group3 is not Mapped'))
        return super().write(vals)

class ProductProduct(models.Model):
    _inherit = "product.product"

    y_item_group = fields.Many2one(related='product_tmpl_id.y_item_group', store=True,string="Item Group")
    y_product_group_1 = fields.Many2one(related='product_tmpl_id.y_product_group_1',store=True,string="Product Group 1")
    y_product_group_2 = fields.Many2one(related='product_tmpl_id.y_product_group_2',store=True,string="Product Group 2")
    y_product_group_3 = fields.Many2one(related='product_tmpl_id.y_product_group_3',store=True,string="Product Group 3")

class StockQuant(models.Model):
    _inherit = "stock.quant"

    y_product_category_id = fields.Many2one('product.category',related='product_id.product_tmpl_id.categ_id', store=True)
    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group', store=True,string="Item Group")
    y_product_group_1 = fields.Many2one('product.group.1',related='product_id.product_tmpl_id.y_product_group_1',store=True,string="Product Group 1")
    y_product_group_2 = fields.Many2one('product.group.2',related='product_id.product_tmpl_id.y_product_group_2',store=True,string="Product Group 2")
    y_product_group_3 = fields.Many2one('product.group.3',related='product_id.product_tmpl_id.y_product_group_3',store=True,string="Product Group 3")
    
    @api.model
    def _get_inventory_fields_write(self):            
        res = super(StockQuant,self)._get_inventory_fields_write()
        return res + ['y_product_category_id', 'y_item_group', 'y_product_group_1','y_product_group_2','y_product_group_3']
  
class StockMove(models.Model):
    _inherit = "stock.move"

    y_product_category_id = fields.Many2one('product.category',related='product_id.product_tmpl_id.categ_id', store=True)
    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group', store=True,string="Item Group")
    y_product_group_1 = fields.Many2one('product.group.1',related='product_id.product_tmpl_id.y_product_group_1',store=True,string="Product Group 1")
    y_product_group_2 = fields.Many2one('product.group.2',related='product_id.product_tmpl_id.y_product_group_2',store=True,string="Product Group 2")
    y_product_group_3 = fields.Many2one('product.group.3',related='product_id.product_tmpl_id.y_product_group_3',store=True,string="Product Group 3")


class StockMove(models.Model):
    _inherit = "stock.move.line"

    y_product_category_id = fields.Many2one('product.category',related='product_id.product_tmpl_id.categ_id', store=True,)
    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group', store=True,string="Item Group")
    y_product_group_1 = fields.Many2one('product.group.1',related='product_id.product_tmpl_id.y_product_group_1',store=True,string="Product Group 1")
    y_product_group_2 = fields.Many2one('product.group.2',related='product_id.product_tmpl_id.y_product_group_2',store=True,string="Product Group 2")
    y_product_group_3 = fields.Many2one('product.group.3',related='product_id.product_tmpl_id.y_product_group_3',store=True,string="Product Group 3")

class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group', store=True,string="Item Group")
    y_product_group_1 = fields.Many2one('product.group.1',related='product_id.product_tmpl_id.y_product_group_1',store=True,string="Product Group 1")
    y_product_group_2 = fields.Many2one('product.group.2',related='product_id.product_tmpl_id.y_product_group_2',store=True,string="Product Group 2")
    y_product_group_3 = fields.Many2one('product.group.3',related='product_id.product_tmpl_id.y_product_group_3',store=True,string="Product Group 3")


class prixgen_stock_picking(models.Model):
    _inherit = 'sale.order.line'

    y_product_group_1 = fields.Many2one('product.group.1',string="Product Group 1",related='product_id.product_tmpl_id.y_product_group_1',store=True)
    y_product_group_2 = fields.Many2one('product.group.2',string="Product Group 2",related='product_id.product_tmpl_id.y_product_group_2',store=True)
    y_product_group_3 = fields.Many2one('product.group.3',string="Product Group 3",related='product_id.product_tmpl_id.y_product_group_3',store=True)
    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group',store=True,string="Item Group")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_product_group_1 = fields.Many2one('product.group.1',string="Product Group 1",related='product_id.product_tmpl_id.y_product_group_1',store=True)
    y_product_group_2 = fields.Many2one('product.group.2',string="Product Group 2",related='product_id.product_tmpl_id.y_product_group_2',store=True)
    y_product_group_3 = fields.Many2one('product.group.3',string="Product Group 3",related='product_id.product_tmpl_id.y_product_group_3',store=True)
    y_item_group = fields.Many2one('item.group',related='product_id.product_tmpl_id.y_item_group',store=True,string="Item Group")
