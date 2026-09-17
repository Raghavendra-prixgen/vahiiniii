from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class MaterialRequest(models.Model):
    _inherit = 'material.request'

    y_mrp_ids = fields.Many2many('mrp.production', string="Manufacturing Orders",tracking=True)

    def prepare_stock_move_line(self,stock_move,operation):
        move_values = super().prepare_stock_move_line(stock_move,operation)
        if stock_move.y_mo_stock_move_ids:
            move_values['move_dest_ids'] = [(6,0,stock_move.y_mo_stock_move_ids.ids)]
        return move_values

    @api.onchange('y_mrp_ids')
    def _get_lines_from_mrp(self):
        mr_ids = self.y_mrp_ids.filtered(lambda mr:mr.state in ('confirmed','to_close','progress') and mr.y_is_material_requested == False)
        move_raw_ids = mr_ids.move_raw_ids.filtered(lambda move: move.quantity != move.product_uom_qty)
        move_product_ids = move_raw_ids.mapped('product_id')
        company_id_ids = set([order.company_id for order in mr_ids])
        if len(company_id_ids) > 1:
            raise UserError(_('You can only create material request of identical company.'))
        mr_lines = []
        for product in move_product_ids:
            filter_move_raw_ids = move_raw_ids.filtered(lambda x:x.product_id == product)
            mr_lines.append((0, 0, {
                    'y_product_id' : product.id,
                    'y_planned_qty' : sum(filter_move_raw_ids.mapped('product_uom_qty')) - sum(filter_move_raw_ids.mapped('quantity')),
                    'y_picking_type_id' : False,
                    'y_source_location_id' : False,
                    'y_dest_location_id' : False,
                    'y_request_type' : 'stock',
                    'y_mo_stock_move_ids': [(6,0,filter_move_raw_ids.ids)]
                }))


        if mr_lines:
            self.y_material_request_line_ids = [(2, line.id, 0) for line in self.y_material_request_line_ids.filtered(lambda req: req.y_mo_stock_move_ids != False)] + mr_lines
            
    

class MaterialRequestLine(models.Model):
    _inherit = 'material.request.line'

    y_source_id = fields.Many2one('mrp.production', string="Source id")
    y_source = fields.Many2one('mrp.production',compute='_get_src', string="Source")
    y_mo_stock_move_ids = fields.Many2many('stock.move',string="MO Stock Moves")

    @api.depends('y_source_id')
    def _get_src(self):
        for rec in self:
            rec.y_source = rec.y_source_id.id

class MrpMaterialRequest(models.Model):
    _inherit = 'mrp.production'

    y_is_material_requested = fields.Boolean(copy=False,string="Is Material Requested")

    def mrp_materal_request_action(self):
        mr_ids = self.filtered(lambda mr:mr.state in ('confirmed','to_close','progress') and mr.y_is_material_requested == False)
        move_raw_ids = mr_ids.move_raw_ids.filtered(lambda move: move.quantity != move.product_uom_qty)
        move_product_ids = move_raw_ids.mapped('product_id')
        company_id_ids = set([order.company_id for order in mr_ids])
        if len(company_id_ids) > 1:
            raise UserError(_('You can only create material request of identical company.'))
        mr_lines = []
        for product in move_product_ids:
            filter_move_raw_ids = move_raw_ids.filtered(lambda x:x.product_id == product)
            mr_lines.append((0, 0, {
                    'y_product_id' : product.id,
                    'y_planned_qty' : sum(filter_move_raw_ids.mapped('product_uom_qty')) - sum(filter_move_raw_ids.mapped('quantity')),
                    'y_picking_type_id' : False,
                    'y_source_location_id' : False,
                    'y_dest_location_id' : False,
                    'y_request_type' : 'stock',
                    'y_mo_stock_move_ids': [(6,0,filter_move_raw_ids.ids)]
                }))
                
                
        if mr_lines:
            mr_id = self.env['material.request'].create({
                'y_mrp_ids':[(6, 0, mr_ids.ids)],
                'y_material_request_line_ids' : mr_lines,
                'y_company_id':mr_ids[0].company_id.id,

                })
            mr_ids.write({'y_is_material_requested': True})

    def action_view_material_request(self):
        action = self.env["ir.actions.actions"]._for_xml_id("material_request.material_request_action_window")
        action['views'] = [(self.env.ref('material_request.material_request_list').id, 'list'),(self.env.ref('material_request.material_request_form').id,'form')]
        action['context'] = self.env.context
        action['domain'] = [('y_mrp_ids', '=', self.id)]
        return action
    