# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EquipmentCateg1(models.Model):
    _name = "sub.equipment.categ.1"
    _description = "Maintenance Sub Equipment Category 1"
    _sql_constraints = [('name_unique', 'unique(name)', 'Name already exists!')]

    name = fields.Char(required=True)
    parent_equipment_categ = fields.Many2one('maintenance.equipment.category',string='Equipment Category')


class EquipmentCateg2(models.Model):
    _name = "sub.equipment.categ.2"
    _description = "Maintenance Sub Equipment Category 2"
    _sql_constraints = [('name_unique', 'unique(name)', 'Name already exists!')]

    name = fields.Char(required=True)
    parent_sub_equipment_categ_1 = fields.Many2one('sub.equipment.categ.1',string='Sub-Category 1')

class EquipmentCateg3(models.Model):
    _name = "sub.equipment.categ.3"
    _description = "Maintenance Sub Equipment Category 3"
    _sql_constraints = [('name_unique', 'unique(name)', 'Name already exists!')]

    name = fields.Char(required=True)
    parent_sub_equipment_categ_2 = fields.Many2one('sub.equipment.categ.2',string='Sub-Category 2')