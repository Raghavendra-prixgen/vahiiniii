from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'
    
    y_sale_order_id = fields.Many2one("sale.order", string = "Sale Order",related="production_id.y_sale_order_id",store=True)
    y_customer_id = fields.Many2one("res.partner", string = "Customer", related="y_sale_order_id.partner_id",store=True)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    y_sale_order_id = fields.Many2one('sale.order',string="Sale Order")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()
        self.picking_ids.write({'y_sale_order_id':self.id})
        for parent in self.mrp_production_ids:            
            child_lst = []
            new_child_lst = []
            child_lst+= parent._get_children().ids
            for ch in child_lst:
                new_child_lst += self.env['mrp.production'].search([('id','=',ch)])._get_children().ids
                [child_lst.append(x) for x in new_child_lst if x not in child_lst]
            child_lst.append(parent.id)            
            child_lst.sort(reverse=False)
            mo_list = self.env['mrp.production'].search([('id','in',child_lst)])
            mo_list.write({'y_sale_order_id':self.id,'y_partner_shipping_id':self.partner_id.id})
            mo_list.picking_ids.write({'y_sale_order_id':self.id})
        return res
    
class Purchaseorder(models.Model):
    _inherit = "purchase.order"

    y_sale_order_id = fields.Many2one('sale.order',string="Saleorder Ref")

    #this is function is for flow y_sale_order_id to subcon picking
    def _get_subcontracting_resupplies(self):
        result = super(Purchaseorder,self)._get_subcontracting_resupplies()
        for picking in result:
            picking.y_sale_order_id = self.y_sale_order_id
        return result

    #this is function is for flow y_sale_order_id from po to normal picking
    def _prepare_picking(self):
        res = super(Purchaseorder,self)._prepare_picking()
        for rec in self:
            res['y_sale_order_id'] = rec.y_sale_order_id
        return res

    @api.model
    def create(self,vals):
        res = super(Purchaseorder,self).create(vals)
        if res.origin:
            mrp_val = self.env['mrp.production'].search([('name','=',res.origin)])
            if mrp_val:
                res.y_sale_order_id = mrp_val.y_sale_order_id
        return res 