# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    y_co_prod_seq_id = fields.Many2one('ir.sequence', string="Co-product_sequence", help="set the sequence for co product MO")
    y_co_lot_seq_id = fields.Many2one('ir.sequence', string="Co-lot sequence", help="set the sequence for co product lot MO")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(y_co_prod_seq_id = int(params.get_param('production.y_co_prod_seq_id')) or False,
                   y_co_lot_seq_id = int(params.get_param('production.y_co_lot_seq_id')) or False,
                  ) 
        return res

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('production.y_co_prod_seq_id',self.y_co_prod_seq_id.id)
        self.env['ir.config_parameter'].sudo().set_param('production.y_co_lot_seq_id',self.y_co_lot_seq_id.id)


class MrpBomCoProduct(models.Model):
    _name = 'mrp.bom.coproduct'
    _description = 'Coproduct BOM'
    _rec_name = "y_product_id"

    y_product_id = fields.Many2one('product.product', 'Co-Product', required=True)
    y_product_qty = fields.Float('Quantity',default=1.0, digits='Product Unit of Measure', required=True)
    y_product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    y_bom_id = fields.Many2one('mrp.bom', 'BoM', ondelete='cascade')
    

    @api.onchange('y_product_id')
    def onchange_y_product_id(self):
        if self.y_product_id:
            self.y_product_uom_id = self.y_product_id.uom_id.id

    @api.onchange('y_product_uom_id')
    def onchange_uom(self):
        res = {}
        if self.y_product_uom_id and self.y_product_id and self.y_product_uom_id.category_id != self.y_product_id.uom_id.category_id:
            res['warning'] = {
                'title': _('Warning'),
                'message': _('The unit of measure you choose is in a different category than the product unit of measure.')
            }
            self.y_product_uom_id = self.y_product_id.uom_id.id
        return res

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    y_coproduct_ids = fields.One2many('mrp.bom.coproduct','y_bom_id', string='Co-Products', copy=True)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    y_co_prod_mo_id = fields.Many2one('mrp.production', string='FG-Product-MO',store=True)
    y_co_prod_mo_ids = fields.One2many('mrp.production','y_co_prod_mo_id',string='Co-Product-MO')
    y_co_prod_ids = fields.One2many('mrp.mo.coproduct','y_fg_prod_mo_id', string='Co-Products')
    y_co_product_track = fields.Boolean(store=True,copy=False)
    y_co_product_track = fields.Integer("Number of generated Co Product")
    y_co_product_count = fields.Integer(compute="compute_y_co_product_count")
    
    y_mark_done = fields.Boolean()

    def action_confirm(self):
        for co_prod in self.y_co_prod_ids:
            if not co_prod.y_co_lot_id and co_prod.y_product_id.tracking =='lot':
                sequence = co_prod.env['ir.sequence'].browse(int(co_prod.env['ir.config_parameter'].sudo().get_param('production.y_co_lot_seq_id')))
                if sequence:            
                    lot_id = co_prod.env["stock.lot"].create({
                        'name': sequence,
                        'product_id': co_prod.y_product_id.id,
                        'company_id': co_prod.y_fg_prod_mo_id.company_id.id,
                    })
                    co_prod.y_co_lot_id = lot_id
                else:
                    raise UserError("Co-Product lot sequence not configured in settings")
        return super().action_confirm()

 
    def button_mark_done(self):          
        res = super(MrpProduction, self).button_mark_done()  
        for co_prod in self.y_co_prod_ids:    
            if self.y_mark_done != True:  
                co_prod.action_process()
                co_prod.action_confirm()
                co_prod.button_mark_done()
                
        self.y_mark_done = True
        return res

    def compute_y_co_product_count(self):       
        for rec in self:        
            if rec.y_co_prod_mo_ids:
                rec.y_co_product_count=len(rec.y_co_prod_mo_ids)
            else:
                rec.y_co_product_count=0
                
 
    @api.onchange('product_id','bom_id','qty_producing')
    def _create_y_co_prod_ids(self):
            self.y_co_prod_ids = [(2, line.id) for line in self.y_co_prod_ids if line.y_bomlineboolean==True]

            new_y_co_prod_ids = [(0, 0, {
                'y_product_id': line.y_product_id.id,
                'y_product_qty': self.product_qty - self.qty_producing if self.product_qty >= self.qty_producing else 0,
                'y_product_uom_id': line.y_product_uom_id.id,
                'y_bomlineboolean': True
            }) for line in self.bom_id.y_coproduct_ids]

            self.y_co_prod_ids = new_y_co_prod_ids
            self.y_co_prod_ids.write({
                'y_product_qty': self.product_qty - self.qty_producing if self.product_qty >= self.qty_producing else 0,
                })
            
    def action_view_coproduct_views(self):
        return {
            'name': ("Co Product MO"),
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'domain': [('y_co_prod_mo_id', '=', self.id)],
            'view_mode': 'list,form'
            }

class MrpMoCoProduct(models.Model):
    _name = 'mrp.mo.coproduct'
    _description = 'Coproduct MO'
    _rec_name = "y_product_id"

    y_product_id = fields.Many2one('product.product', 'Co-Product', required=True)
    y_product_qty = fields.Float('Quantity',default=1.0, digits='Product Unit of Measure', required=True)
    y_product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    y_fg_prod_mo_id = fields.Many2one('mrp.production', 'FGMO', ondelete='cascade')
    y_co_prod_mo_id = fields.Many2one('mrp.production', 'COMO', ondelete='cascade')
    y_state = fields.Selection(related='y_co_prod_mo_id.state')
    y_bomlineboolean = fields.Boolean(default=False)
    y_co_lot_id = fields.Many2one('stock.lot',string="Lot/Serial Number")


    def action_process(self):
        sequence = self.env['ir.sequence'].browse(int(self.env['ir.config_parameter'].sudo().get_param('production.y_co_prod_seq_id')))
        bom = self.env['mrp.bom']._bom_find(self.y_product_id, picking_type=None, company_id=self.y_product_id.company_id.id, bom_type='normal')[self.y_product_id]
        component_list = [(0, 0, {
            'name':component.product_id.name,
            'location_id': component.location_id.id,
            'location_dest_id': component.location_dest_id.id,
            'product_id': component.product_id.id,
            'product_uom': component.product_uom.id,
            'warehouse_id': component.warehouse_id.id,
            'picking_type_id': component.picking_type_id.id,
            'product_uom_qty': (self.y_product_qty  * sum(self.y_fg_prod_mo_id.bom_id.bom_line_ids.filtered(lambda x:x.product_id == component.product_id).mapped('product_qty'))) / self.y_fg_prod_mo_id.bom_id.product_qty,
            'product_uom': component.product_uom.id
        }) for component in self.y_fg_prod_mo_id.move_raw_ids if component.quantity!=0]
        
        # analytic_account_id field is not avilable in mrp.production bcz of that i comended

        if not self.y_co_lot_id and self.y_product_id.tracking =='lot':
            sequence = self.env['ir.sequence'].browse(int(self.env['ir.config_parameter'].sudo().get_param('production.y_co_lot_seq_id')))
            if sequence:            
                lot_id = self.env["stock.lot"].create({
                    'name': sequence,
                    'product_id': self.y_product_id.id,
                    'company_id': self.y_fg_prod_mo_id.company_id.id,
                })
                self.y_co_lot_id = lot_id
            else:
                raise UserError("Co-Product lot sequence not configured in settings")
      
        if sequence:
            new_mo = self.env['mrp.production'].with_context(is_co_product=True).create({
                'name': sequence.next_by_id(),
                'product_id': self.y_product_id.id,
                'lot_producing_id':self.y_co_lot_id.id,
                'product_qty': self.y_product_qty,
                'bom_id': bom.id if bom else "",
                'product_uom_id': self.y_product_uom_id.id,
                'origin':self.y_fg_prod_mo_id.name,
                'picking_type_id': self.y_fg_prod_mo_id.picking_type_id.id,
                'location_src_id': self.y_fg_prod_mo_id.location_src_id.id,
                'location_dest_id':self.y_fg_prod_mo_id.location_dest_id.id,
                'move_raw_ids':component_list 
            })
        else:
            new_mo = self.env['mrp.production'].with_context(is_co_product=True).create({
            'product_id': self.y_product_id.id,
            'lot_producing_id':self.y_co_lot_id.id,
            'product_qty': self.y_product_qty,
            'bom_id': bom.id if bom else "",
            'product_uom_id': self.y_product_uom_id.id,
            'origin':self.y_fg_prod_mo_id.name,
            'picking_type_id': self.y_fg_prod_mo_id.picking_type_id.id,
            'location_src_id': self.y_fg_prod_mo_id.location_src_id.id,
            'location_dest_id':self.y_fg_prod_mo_id.location_dest_id.id,
            'move_raw_ids':component_list 
        })
       
        new_mo._onchange_product_id()
        self.y_co_prod_mo_id = new_mo.id
        self.y_fg_prod_mo_id.y_co_prod_mo_ids = [(4, new_mo.id, 0)]
        self.y_fg_prod_mo_id.y_co_product_track = True
        self.y_fg_prod_mo_id.y_co_product_track = len(self.y_fg_prod_mo_id.y_co_prod_mo_ids)

    
    def action_confirm(self):
        self.y_co_prod_mo_id.action_confirm()

    def button_mark_done(self):
        self.y_co_prod_mo_id.qty_producing = self.y_product_qty
        self.y_co_prod_mo_id._onchange_producing()
        self.y_co_prod_mo_id.button_mark_done()
        
    @api.onchange('y_product_id')
    def onchange_product_id(self):
        if self.y_product_id:
            self.y_product_uom_id = self.y_product_id.uom_id.id

    @api.onchange('y_product_uom_id')
    def onchange_uom(self):
        res = {}
        if self.y_product_uom_id and self.y_product_id and self.y_product_uom_id.category_id != self.y_product_id.uom_id.category_id:
            res['warning'] = {
                'title': _('Warning'),
                'message': _('The unit of measure you choose is in a different category than the product unit of measure.')
            }
            self.y_product_uom_id = self.y_product_id.uom_id.id
        return res
    
    



