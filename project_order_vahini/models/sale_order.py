from odoo import models, fields, api, _


class SaleDocType(models.Model):
    _inherit = 'sale.doc.type'
    
    y_is_project_order = fields.Boolean(string="Project Order")
    

class SaleOrderLine(models.Model):
	_inherit='sale.order.line'


	y_base_price = fields.Float(string="Base Price",store=True)
	y_weight = fields.Float(string="Weight",store=True)
	
	
	@api.onchange('y_base_price','y_weight','product_uom','product_uom_qty')
	def CalculateUnitPrice(self):
		for rec in self:
			if rec.order_id.y_doc_type_id.y_is_project_order == True:
				rec.price_unit = rec.y_base_price * rec.y_weight
			else:
				rec.y_base_price=False
				rec.y_weight=False

	


class SaleOrder(models.Model):
	_inherit='sale.order'

	y_doc_type_project_order = fields.Boolean(string="Doc Type Project Order",store=True,compute="CheckDocTypeIsProjectOrder")
	
	
	@api.depends('y_doc_type_id')
	def CheckDocTypeIsProjectOrder(self):
		for res in self:
			if res.y_doc_type_id.y_is_project_order == True:
				res.y_doc_type_project_order = True
			else:
				res.y_doc_type_project_order = False
      
	
	
 
 


			
