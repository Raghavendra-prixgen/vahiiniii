from odoo import api, fields, models, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_id = fields.Many2one(tracking=True)
    qty_producing = fields.Float(tracking=True)
    date_start = fields.Datetime(tracking=True)
    bom_id = fields.Many2one(tracking=True)

class StockScrap(models.Model):
    _inherit = 'stock.scrap'   
    
    origin = fields.Char(tracking=True)
    product_id = fields.Many2one(tracking=True)
    scrap_qty = fields.Float(tracking=True)
    location_id = fields.Many2one(tracking=True)
    scrap_location_id = fields.Many2one(tracking=True)
    
class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'
    
    product_id = fields.Many2one(tracking=True)
    bom_id = fields.Many2one(tracking=True)
    product_qty = fields.Float(tracking=True)
    location_id = fields.Many2one(tracking=True)
    location_dest_id = fields.Many2one(tracking=True)

    
class MrpBom(models.Model):
    _inherit = 'mrp.bom'   

    code = fields.Char(tracking=True)
    type = fields.Selection(tracking=True)
    product_tmpl_id = fields.Many2one(tracking=True)
    product_id = fields.Many2one(tracking=True)
    product_qty = fields.Float(tracking=True)
    ready_to_produce = fields.Selection(tracking=True)
    picking_type_id = fields.Many2one(tracking=True)
    company_id = fields.Many2one(tracking=True)
    consumption = fields.Selection(tracking=True)  

    
    
