from odoo import models, fields, api, _

class VahiniPackingListCategory(models.Model):
    _name = 'packing.category'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'y_name'
    
    y_name = fields.Char('Name')
    
class VahiniStockPackingType(models.Model):
    _inherit = 'stock.package.type'
    
    y_packing_category_id = fields.Many2one('packing.category',string="Packing Category")
    
class VahiniProductPacking(models.Model):
    _inherit = 'product.packaging'
    
    y_packing_category_id = fields.Many2one('packing.category',string="Packing Category",store=True,compute="compute_get_product_packing_category")
    
    @api.depends('package_type_id')
    def compute_get_product_packing_category(self):
        for line in self:
            if line.package_type_id:
                line.y_packing_category_id = line.package_type_id.y_packing_category_id.id
            else:
                line.y_packing_category_id = False
    
# class SaleOrder(models.Model):
#     _inherit = 'sale.order.line'

#     y_packing_category_id = fields.Many2one('packing.category',string="Packing Category",store=True,compute="compute_get_packing_category")
    
    
#     @api.depends('product_packaging_id')
#     def compute_get_packing_category(self):
#         for line in self:
#             if line.product_packaging_id:
#                 line.y_packing_category_id =  line.product_packaging_id.y_packing_category_id.id
#             else:
#                 line.y_packing_category_id = False
                
                
class StockMove(models.Model):
    _inherit = 'stock.move'

    y_packing_category_id = fields.Many2one('packing.category',string="Packing Category",store=True,compute="compute_get_stock_packing_category")
    
    
    @api.depends('product_packaging_id')
    def compute_get_stock_packing_category(self):
        for line in self:
            if line.product_packaging_id:
                line.y_packing_category_id =  line.product_packaging_id.y_packing_category_id.id
            else:
                line.y_packing_category_id = False
                
                
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    y_e_way_doc_no = fields.Char(string="E-Way Bill Document No")
    
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    y_packing_category_id = fields.Many2one('packing.category',string="Packing Category",store=True,compute="compute_get_packing_category_account")
    
    
    @api.depends('y_stock_move_id')
    def compute_get_packing_category_account(self):
        for line in self:
            if line.y_stock_move_id.product_packaging_id:
                line.y_packing_category_id =  line.y_stock_move_id.product_packaging_id.y_packing_category_id.id
            else:
                line.y_packing_category_id = False


    

# class CustomFields(models.Model):
# 	_name = "custom.fields"
 
# 	y_name= fields.Char(string='Name',store=True ,index=True,ondelete='cascade')

# class Custom(models.Model):
#     _name = 'crm.custom'
    
#     y_name= fields.Char(string='Category here',store=True )

# class BloodGroup(models.Model):
# 	_name = "custom.fields.bgroup"
 
# 	y_name= fields.Char(string='Group',store=True ,index=True,ondelete='cascade')

# class IndustryGroup(models.Model):
# 	_name = "custom.fields.industrygroup"
 
# 	y_name= fields.Char(string='Group',store=True ,index=True,ondelete='cascade')

# class IndustryType(models.Model):
# 	_name = "custom.fields.industrytype"
 
# 	y_name= fields.Char(string='Type',store=True ,index=True,ondelete='cascade')

# class CrmFields(models.Model):
#     _name = 'custom.fields.crm'
    
#     y_name= fields.Char(string='Category here',store=True ,ondelete='cascade')
    

# class BloodGroup(models.Model):
#     _name = "custom.fields.bgroup"
    
#     y_name= fields.Char(string='Group',store=True ,index=True,ondelete='cascade')



# class PortOrder(models.Model):
# 	_name = 'port.order'

# 	y_name= fields.Char('Name')
# 	y_city= fields.Char('City')
# 	y_country= fields.Many2one('res.country','Country')

# class ExportShipment(models.Model):
# 	_name = 'export.shipment'
	
# 	y_name= fields.Char('Name')

# class ContainerType(models.Model):
# 	_name = 'type.container'
 
# 	y_name= fields.Char('Name')
 

