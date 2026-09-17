from odoo.exceptions import ValidationError
from odoo import api, fields, models, tools, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    y_quantity_alt_uom = fields.Char('Quantity Alt Uom')
    y_conversion = fields.Float('Conversion')
    y_alternate_uom = fields.Many2one('uom.uom',string="Alternate UOM")

    # @api.onchange('y_alternate_uom')
    # def y_alternate_uom_change(self):
    #     if self.uom_id and self.y_alternate_uom and self.uom_id.category_id != self.y_alternate_uom.category_id:
    #         self.y_alternate_uom = self.uom_id

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        super(ProductTemplate,self)._onchange_uom_id()
        if self.uom_id:
            self.y_alternate_uom = self.uom_id.id

class AccountMoveline(models.Model):
    _inherit = 'account.move.line'

    y_quantity_alt_uom = fields.Float(string="AUOM QTY" ,compute='compute_alt_qty')
    y_alternate_uom = fields.Many2one('uom.uom',string="AUOM",related="product_id.product_tmpl_id.y_alternate_uom",store=True)

    @api.depends('quantity','y_alternate_uom')
    def compute_alt_qty(self):
         for rec in self:
            if rec.product_id.product_tmpl_id.y_conversion != 0:
                if rec.y_alternate_uom:
                    rec.y_quantity_alt_uom = rec.quantity * rec.product_id.product_tmpl_id.y_conversion
                else:
                    rec.y_quantity_alt_uom = 0.0
            else:
                rec.y_quantity_alt_uom = 0.0
    
class StockQuant(models.Model):
    _inherit = 'stock.quant'

    y_quantity_alt_uom = fields.Float('Quantity in Alt. UOM', compute='_set_total')
    product_id = fields.Many2one('product.product', 'Product',ondelete='restrict', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',related='product_id.product_tmpl_id')
    y_conversion_prod = fields.Float('Conversion Prod',store=True,readonly=True,related="product_tmpl_id.y_conversion")
    y_alternate_uom_id = fields.Many2one('uom.uom',readonly=True,related="product_tmpl_id.y_alternate_uom",store=True)

    @api.onchange('quantity','y_conversion_prod')
    def _set_total(self):
        for line in self:
        	line.y_quantity_alt_uom = float(line.quantity) * float(line.y_conversion_prod)

    @api.model
    def _get_inventory_fields_write(self):            
        res = super(StockQuant,self)._get_inventory_fields_write()
        return res + ['y_quantity_alt_uom','y_alternate_uom_id','y_conversion_prod']

class SaleOrderLineAlter(models.Model):
    _inherit = 'sale.order.line'
    
    y_quantity_alt_uom = fields.Float(string="AUOM QTY")
    y_alternate_uom = fields.Many2one('uom.uom',string="AUOM",related="product_template_id.y_alternate_uom")
    y_conversion_prod = fields.Float('Conversion Prod',readonly=True,related="product_id.product_tmpl_id.y_conversion",store=True)

    @api.onchange('product_template_id','product_uom_qty')
    def get_y_alternate_uom_and_y_quantity_alt_uom(self):
         for rec in self:
             if rec.product_template_id.y_alternate_uom:
                rec.y_alternate_uom = rec.product_template_id.y_alternate_uom.id
                if rec.y_alternate_uom and rec.product_template_id.y_conversion != 0:
                    rec.y_quantity_alt_uom = (rec.product_uom_qty * rec.product_template_id.y_conversion)  
             
    def _prepare_invoice_line(self, **optional_values):
        vals = super(SaleOrderLineAlter, self)._prepare_invoice_line(**optional_values)
        vals.update({
            # 'y_quantity_alt_uom': self.y_quantity_alt_uom,
            'y_alternate_uom': self.y_alternate_uom.id
        })
        return vals
    
    # @api.onchange('y_quantity_alt_uom')
    # def _onchange_y_quantity_alt_uom(self):
    #     for rec in self:
    #         if rec.y_alternate_uom:
    #             rec.product_uom_qty = (rec.y_quantity_alt_uom * rec.product_template_id.y_conversion)  
            
class StockMove(models.Model):
    _inherit ='stock.move'

    y_quantity_alt_uom = fields.Float(string="AUOM QTY",compute="_compute_y_quantity_alt_uom")
    y_alternate_uom = fields.Many2one('uom.uom',string="AUOM")

    @api.depends('y_alternate_uom')
    def _compute_y_quantity_alt_uom(self):
        for rec in self:
            if rec.quantity and rec.product_id.product_tmpl_id.y_conversion != 0:
                rec.y_quantity_alt_uom = (rec.quantity * rec.product_id.product_tmpl_id.y_conversion)  
            else:
                rec.y_quantity_alt_uom = 0.0

    def create(self,values):
        res =super().create(values)
        if res.sale_line_id:
            res.y_quantity_alt_uom = res.sale_line_id.y_quantity_alt_uom
            res.y_alternate_uom = res.sale_line_id.y_alternate_uom.id
        return res
    
class StockMoveLine(models.Model):
    _inherit ='stock.move.line'

    y_quantity_alt_uom = fields.Float(string="AUOM QTY",compute='compute_alt_qty_id')
    y_alternate_uom = fields.Many2one('uom.uom',string="AUOM")

    @api.depends('quantity','y_alternate_uom')
    def compute_alt_qty_id(self):
         for rec in self:
            if rec.y_alternate_uom and rec.product_id.product_tmpl_id.y_conversion != 0:
                rec.y_quantity_alt_uom = rec.quantity * rec.product_id.product_tmpl_id.y_conversion
            else:
                rec.y_quantity_alt_uom = False
    
    def create(self,values):
        res =super(StockMoveLine,self).create(values)
        if res.move_id.sale_line_id:
            for sale_line in res.move_id.sale_line_id:
                res.y_quantity_alt_uom = sale_line.y_quantity_alt_uom
                res.y_alternate_uom = sale_line.y_alternate_uom.id
        return res
    
class MrpProdictionNew(models.Model):
    _inherit ='mrp.production'

    y_quantity_alt_uom = fields.Float(string="AUOM QTY",compute ="_compute_suom_qty")
    y_alternate_uom = fields.Many2one('uom.uom',string="AUOM",compute ="_compute_product_alternative_uom_qty" )

    @api.depends('product_id.product_tmpl_id.y_alternate_uom','product_qty')
    def _compute_suom_qty(self):
        if self.product_id.product_tmpl_id.y_alternate_uom and self.product_id.product_tmpl_id.y_conversion != 0:
            self.y_quantity_alt_uom = (self.product_qty * self.product_id.product_tmpl_id.y_conversion)  
        else:
            self.y_quantity_alt_uom = None

    @api.depends('product_id.product_tmpl_id.y_alternate_uom')
    def _compute_product_alternative_uom_qty(self):
            if self.product_id.product_tmpl_id.y_alternate_uom:
                self.y_alternate_uom = self.product_id.product_tmpl_id.y_alternate_uom.id
            else:
                self.y_alternate_uom = None
