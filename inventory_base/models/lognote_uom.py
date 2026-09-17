# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import SUPERUSER_ID, _, api, fields, models


def get_selection_label(self, object, field_name, field_value):
    return (dict(self.env[object].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])


class UomCategory(models.Model):
    _name = "uom.category"
    _inherit = ['uom.category','mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(tracking=True)

    def write(self,vals):
        new_dist = []
        if vals.get('uom_ids'):
            new_list = []
            for list1 in vals.get('uom_ids'):
                if list1[-1] != False:
                    new_list.append(list1)
                    uom_ids = self.uom_ids.filtered(lambda x:x.id in [value[1] for value in new_list])
                    new_dist = []
                    for dicts in uom_ids:
                        for newval in new_list:
                            if not isinstance(newval[-1],int):
                                if newval[1] == dicts.id:
                                    if newval[-1].get('y_weight_uom') and dicts.y_weight_uom:
                                        new_y_weight_uom = get_selection_label(self,'uom.uom','y_weight_uom',newval[-1].get('y_weight_uom'))
                                        old_y_weight_uom = get_selection_label(self,'uom.uom','y_weight_uom',dicts.y_weight_uom)
                                        new_dist.append('{} for {}:{} ---> {}'.format("Weight Unit of Measure",dicts.name,old_y_weight_uom,new_y_weight_uom))

                                    if newval[-1].get('name'):
                                        new_name = newval[-1].get('name')
                                        new_dist.append('{}{} ---> {}'.format("Unit of Measure : ",dicts.name,new_name))

                                    if newval[-1].get('uom_type') and dicts.uom_type:
                                        new_uom_type = get_selection_label(self,'uom.uom','uom_type',newval[-1].get('uom_type'))
                                        old_uom_type = get_selection_label(self,'uom.uom','uom_type',dicts.uom_type)
                                        new_dist.append('{} for :{} ---> {}'.format("Type",old_uom_type,new_uom_type))

                                    if newval[-1].get('ratio'):
                                        new_ratio = newval[-1].get('ratio')
                                        new_dist.append('{} for {}:{} ---> {}'.format("Ratio: ",dicts.name,dicts.ratio,new_ratio))

                                    if newval[-1].get('rounding'):
                                        new_rounding = newval[-1].get('rounding')
                                        new_dist.append('{} for {}:{} ---> {}'.format("Rounding",dicts.name,dicts.rounding,new_rounding))
                                
            if new_dist:
                msg = ', '.join(dic for dic in new_dist)
                if self.env.user:
                    self.message_post(body=msg)                
        
        return super().write(vals)


