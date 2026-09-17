from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class MaterialPurchaseRequestWizard(models.TransientModel):
    _name = "material.purchase.request.wizard"
    _description = " "

    y_material_request_id = fields.Many2one('material.request',string="Material Request")
    y_material_request_line_ids = fields.Many2many('material.request.line',string='Material Request Lines')
    y_purchase_request_type_id = fields.Many2one('request.type',string="Purchase Request Type")

    @api.onchange('y_material_request_id')
    def _onchange_material_request_line_ids(self):
        for rec in self:
            mr_lines = []
            if self._context.get('default_y_material_request_line_ids'):
                mr_lines = [(6,0,self._context.get('default_y_material_request_line_ids'))]
            rec.y_material_request_line_ids = mr_lines

    def button_create_purchase_request(self):
        plines = self.y_material_request_line_ids.filtered(lambda x:x.y_purchase_request_pending_qty > 0)
        prequests = []
        request_obj = self.y_purchase_request_type_id
        purchase = {
            'y_material_request_id' : self.y_material_request_id.id,
            'request_type_id' : request_obj.id,
            'name': request_obj.sequence_id.next_by_id(),
            'line_ids' : [],
            'approver_ids': [(6,0,request_obj.approver_ids.ids)],
            'origin':self.y_material_request_id.y_name,
            'company_id':self.y_material_request_id.y_company_id.id,
        }

        purchase_request_line_ids = []
        for pline in plines:     
            if pline.y_planned_qty < (pline.y_purchase_requested_qty + pline.y_purchase_request_pending_qty):
                raise UserError("Request Qty should not be greter than Planned Qty")
            purchase_request_id = pline.y_purchase_request_ids.filtered(lambda x:x.state == 'draft')     
            line_ids = purchase_request_id.line_ids.filtered(lambda x:x.product_id == pline.y_product_id)
            if line_ids:
                for line in line_ids:
                    quantity = line.product_qty + pline.y_purchase_request_pending_qty
                    line.write({'product_qty':quantity})
                
            else:
                purchase_request_line_ids.append((0, 0,{
                    'product_id': pline.y_product_id.id,
                    'product_uom_id' : pline.y_product_id.uom_id.id,
                    'product_qty' : pline.y_purchase_request_pending_qty,
                    'y_mr_line_id' : pline.id,
                }))
                
            pline.y_purchase_requested_qty += pline.y_purchase_request_pending_qty

        purchase_id = self.env['purchase.request']
        if purchase_request_line_ids:
            purchase['line_ids'] = purchase_request_line_ids
            purchase_id = self.env['purchase.request'].create(purchase)
            
        for line in purchase_id.line_ids:
            line.y_mr_line_id.y_purchase_request_ids = [(4, line.request_id.id, 0)]
    


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    y_material_request_id = fields.Many2one('material.request',string="Material Request")
  

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'
    
    y_material_request_id = fields.Many2one('material.request',string="Material Request")

class ResCompany(models.Model):
    _inherit = 'res.company'

    y_mr_sequence_id = fields.Many2one('ir.sequence',string="Material Request Sequence")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    y_mr_sequence = fields.Many2one('ir.sequence',string="Material Request Sequence",readonly=False,related='company_id.y_mr_sequence_id')
    

class MaterialRequest(models.Model):
    _name = 'material.request'
    _inherit = ['mail.thread', 'mail.activity.mixin','analytic.mixin']
    _description = 'Material Request'
    _rec_name = 'y_name'

    y_name = fields.Char('Sequence',default=lambda self: _('New'),tracking=True)
    y_material_picking_ids = fields.One2many('stock.picking','y_material_request_id',string="Pickings")
    y_purchase_material_ids = fields.One2many('purchase.request','y_material_request_id',string="Purchase Requests")
    y_picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type",tracking=True)
    y_source_location_id = fields.Many2one('stock.location',tracking=True,string="Source Location")
    y_dest_location_id = fields.Many2one('stock.location',tracking=True,string="Destination Location")
    y_purchase_request_type_id = fields.Many2one('request.type',tracking=True,string="Purchase Request Type")
    y_material_request_line_ids = fields.One2many('material.request.line','y_material_request_id',tracking=True,string="Material Request Lines")
    y_request_material_boolean = fields.Boolean(default=False,string="Request Material")
    y_picking_count = fields.Integer(compute="_compute_get_y_picking_count",string="picking Count")
    y_purchase_count = fields.Integer(compute="_compute_get_y_purchase_count",string="Purchase Request Count")
    y_responsible_id = fields.Many2one('res.users',string="Responsible")
    y_company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.company)
    y_state = fields.Selection([('draft','Draft'),('to_approve','To Approve'),('approved','Approved'),('closed','Closed'),('cancel','Canceled')], default='draft',tracking=True,string="State")
    y_approved_date = fields.Datetime(string="Approved Date")

    def copy(self, default=None):
        default = dict(default or {})
        default.update({"y_state": "draft", "y_name":"New"})
        return super(MaterialRequest, self).copy(default)

    def request_approve_button(self):
        if all([True if line.y_planned_qty == 0 else False for line in self.y_material_request_line_ids]):
            raise ValidationError("Planned Qty should be greter than zero")
        self.write({'y_state':'to_approve'})

    def approved(self):
        self.write({'y_state':'approved','y_approved_date':datetime.now()})

    def button_cancel(self):
        transfer_ids = self.y_material_request_line_ids.y_transfer_order_ids.filtered(lambda x:x.state == 'done')
        if transfer_ids:
            raise ValidationError("Once Transfers are confirmed, you cannot cancel the material request.")

        purchase_ids = self.y_material_request_line_ids.y_purchase_request_ids.line_ids.purchase_lines.order_id.filtered(lambda x:x.state in ('purchase','done'))
        if purchase_ids:
            raise ValidationError("Once purchase orders are confirmed, you cannot cancel the material request.")
        
        self.y_material_request_line_ids.y_transfer_order_ids.action_cancel()
        self.y_material_request_line_ids.y_purchase_request_ids.button_cancel()
        self.y_material_request_line_ids.y_purchase_request_ids.line_ids.purchase_lines.order_id.button_cancel()
        self.write({'y_state':'cancel'})
    
    @api.depends('y_material_picking_ids')
    def _compute_get_y_picking_count(self):
        for request in self:
            request.y_picking_count = len(request.y_material_picking_ids)
            
    @api.depends('y_purchase_material_ids')
    def _compute_get_y_purchase_count(self):
        for req in self:
            req.y_purchase_count = len(req.y_purchase_material_ids)

    @api.onchange('y_picking_type_id')
    def _get_default_location_y_picking_type_id(self):
        for rec in self:
            if rec.y_picking_type_id:
                rec.y_source_location_id = rec.y_picking_type_id.default_location_src_id.id
                rec.y_dest_location_id = rec.y_picking_type_id.default_location_dest_id.id
                for record in rec.y_material_request_line_ids:
                    record.y_picking_type_id = rec.y_picking_type_id.id

    @api.onchange('y_source_location_id')
    def _get_default_location_y_source_location_id(self):
        for rec in self:
            if rec.y_source_location_id:
                for record in rec.y_material_request_line_ids:
                    record.y_source_location_id = rec.y_source_location_id.id

    @api.onchange('y_dest_location_id')
    def _get_default_location_y_dest_location_id(self):
        for rec in self:
            if rec.y_dest_location_id:
                for record in rec.y_material_request_line_ids:
                    record.y_dest_location_id = rec.y_dest_location_id.id
        
    def action_mr_picking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['views'] = [(self.env.ref('stock.vpicktree').id, 'list'),(self.env.ref('stock.view_picking_form').id,'form')]
        action['context'] = self.env.context
        action['domain'] = [('y_material_request_id', '=', self.id)]
        return action
    
    def action_mr_purchase(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase_base_18.purchase_request_form_action")
        action['views'] = [(self.env.ref('purchase_base_18.view_purchase_request_tree').id, 'list'),(self.env.ref('purchase_base_18.view_purchase_request_form').id,'form')]
        action['context'] = self.env.context
        action['domain'] = [('y_material_request_id', '=', self.id)]
        return action

    def close(self):
        self.write({'y_state':'closed'})
    
    def reset(self):
        self.write({'y_state':'draft'})

    def process_all(self):
        for each_line in self.y_material_request_line_ids:
            each_line.write({'y_request_qty': each_line.y_planned_qty})

    # @api.onchange('y_purchase_request_type_id')
    # def _get_default_y_purchase_request_type_id(self):
    #     for rec in self:
    #         if rec.y_purchase_request_type_id:
    #             for record in rec.y_material_request_line_ids.filtered(lambda x:x.y_request_type == 'purchase'):
    #                 record.y_purchase_request_type_id = rec.y_purchase_request_type_id.id
    @api.model
    def create(self, vals):
        vals['y_request_material_boolean'] = True
        if vals.get('y_name', _('New')) == _('New'):
            company = self.env['res.company'].browse(vals['y_company_id'])
            sequence = company.y_mr_sequence_id
            if sequence:
                vals['y_name'] = sequence.next_by_id()
            else:                
                raise UserError("Material Request Sequence Not Configured {} Company".format(company.name))
        return super(MaterialRequest, self).create(vals)

    def prepare_picking(self,operation):
        return {
                'y_material_request_id' : self.id,
                'user_id' : self.y_responsible_id.id,
                'picking_type_id' : operation[0],
                'location_id' : operation[1],
                'location_dest_id' : operation[2],
                'move_ids_without_package' : [],
                'company_id' : self.y_company_id.id,
                }

    def prepare_stock_move_line(self,stock_move,operation):
        return {
                'product_id' : stock_move.y_product_id.id,
                'name' : stock_move.y_product_id.partner_ref,
                'product_uom_qty' : stock_move.y_request_qty,
                'product_uom' : stock_move.y_product_id.uom_id.id,
                'y_mr_line_id' : stock_move.id,
                'location_id': operation[1],
                'group_id':stock_move.y_group_id.id,
                'location_dest_id' : operation[2],
                'company_id':self.y_company_id.id,
                }

    def request_material(self):
        if all([True if line.y_request_qty == 0 else False for line in self.y_material_request_line_ids]):
            raise ValidationError("Quantity to ship should be greter than zero")

        moves = self.y_material_request_line_ids
        operations = []        
        for move in moves:
            operations.append((move.y_picking_type_id.id,move.y_source_location_id.id,move.y_dest_location_id.id))
        operations = set(operations)
        for mov in moves:       
            if mov.y_request_type == 'stock':
                for operation in operations:                   
                    if operation[0]:
                        picking = self.prepare_picking(operation)               
                        stock_moves = moves.filtered(lambda mov: mov.y_picking_type_id.id ==  operation[0] and mov.y_source_location_id.id == operation[1] and mov.y_dest_location_id.id == operation[2] and mov.y_request_qty)
                        for stock_move in stock_moves:
                            move_values = self.prepare_stock_move_line(stock_move,operation)
                            picking['move_ids_without_package'].append((0, 0,move_values))
                            if stock_move.y_request_type != 'purchase':
                                stock_move.y_requested_qty += stock_move.y_request_qty
                                stock_move.y_request_qty = 0
                    
                        if len(stock_moves):
                            picking = self.env['stock.picking'].create(picking)
                            for move in picking.move_ids_without_package:
                                move.y_mr_line_id.y_transfer_order_ids = [(4, move.picking_id.id, 0)]
                        

            # else:                
            #     plines = self.y_material_request_line_ids.filtered(lambda req: req.y_request_type == 'purchase')
            #     prequests = []
            #     for pline in plines:
            #         y_purchase_request_type_id = pline.y_material_request_id.y_purchase_request_type_id
            #         if not y_purchase_request_type_id:
            #             raise ValidationError(_("Purchase Request Sequence Not Configured"))
            #         else:
            #             request_obj = y_purchase_request_type_id
            #             purchase = {
            #                 'y_material_request_id' : self.id,
            #                 'request_type_id' : request_obj.id,
            #                 'name': request_obj.sequence_id.next_by_id(),
            #                 'line_ids' : [],
            #                 'approver_ids': [(6,0,request_obj.approver_ids.ids)],
            #             }
                    
            #             purchase_lines = plines.filtered(lambda lin:lin.y_request_qty > 0)
            #             for purchase_line in purchase_lines:
                            
            #                 purchase['line_ids'].append((0, 0,{
            #                     'product_id': purchase_line.y_product_id.id,
            #                     'product_uom_id' : purchase_line.y_product_id.uom_id.id,
            #                     'product_qty' : purchase_line.y_request_qty,
            #                     'y_mr_line_id' : purchase_line.id,
            #                 }))
            #                 purchase_line.y_requested_qty += purchase_line.y_request_qty
            #                 purchase_line.y_request_qty = 0
                            
            #             if len(purchase_lines) :  
            #                 purchase = self.env['purchase.request'].create(purchase)
                            
            #                 for line in purchase.line_ids:
            #                     line.y_mr_line_id.y_purchase_request_ids = [(4, line.request_id.id, 0)]
            

    def generate_purchase_requeset_form_wizard(self):
        line_ids = self.y_material_request_line_ids.filtered(lambda x:x.y_planned_qty > x.y_purchase_requested_qty)
        if not line_ids:
            raise ValidationError(_("You Can't process a greater quantity than the purchase requested quantity."))
        if self.y_state != 'approved':
            raise UserError(_("Purchase Request Should allow only in approved state"))

        for line in self.y_material_request_line_ids:
            line.y_purchase_request_pending_qty = line.y_planned_qty - line.y_purchase_requested_qty
        
        return {'name': ("Purchase Request"),

                'type': 'ir.actions.act_window',

                'res_model': 'material.purchase.request.wizard',

                'view_mode': 'form',

                'views': [(self.env.ref('material_request.material_purchase_request_wizard_form_view').id, 'form')],

                'target': 'new',

                'context': dict(self._context, 
                                create=False,
                                edit=False,
                                default_y_material_request_id = self.id,
                                default_y_material_request_line_ids = line_ids.ids)
                }

class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _inherit = ['analytic.mixin']
    _description = 'Material Request Line'
          
    y_material_request_id = fields.Many2one('material.request',string="Material Request")  
    y_company_id = fields.Many2one('res.company',related="y_material_request_id.y_company_id",string="Company")
    y_picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    y_source_location_id = fields.Many2one('stock.location',string="Source Location")
    y_dest_location_id = fields.Many2one('stock.location',string="Destination Location")
    y_purchase_request_type_id = fields.Many2one('request.type',string="Purchase Request Type")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_available_qty = fields.Float(related='y_product_id.qty_available',string="Available Qty")
    y_forcast_qty = fields.Float(related='y_product_id.virtual_available',string="Forcast Qty")
    y_planned_qty = fields.Float(string="Qty")
    y_requested_qty = fields.Float(readonly=True, string="Quantity Shipped")
    y_request_qty = fields.Float(string="Quantity To Ship")
    # y_request_type = fields.Selection([('stock','Internal Transfer'),('purchase','Purchase Request')],default='stock',string="Request Type") 
    y_request_type = fields.Selection([('stock','Internal Transfer')],default='stock',string="Request Type")
    y_transfer_order_ids = fields.Many2many('stock.picking', readonly=True,string="Transfer Order")
    y_purchase_request_ids = fields.Many2many('purchase.request', readonly=True,string="Purchase Request")
    y_group_id = fields.Many2one('procurement.group',string="Procurement Group")
    y_purchase_requested_qty = fields.Float(string="Purchase Request Qty")
    y_purchase_request_pending_qty = fields.Float(string="Pending Qty")
    
    @api.onchange('y_request_type')
    def _onchage_request_type(self):
        for line in self:
            if line.y_request_type == 'stock':
                line.y_material_request_id._get_default_location_y_picking_type_id()
                line.y_material_request_id._get_default_location_y_source_location_id()
                line.y_material_request_id._get_default_location_y_dest_location_id()

    def unlink(self):
        for each in self:
            if each.y_requested_qty:
                raise UserError(_("Request Can't be Deleted after Processing"))
        return super(MaterialRequestLine, self).unlink()

    @api.constrains('y_request_qty')
    def _check_something(self):
        for rec in self:
            if rec.y_request_qty > rec.y_planned_qty - rec.y_requested_qty:
                raise ValidationError(_("Keep Calm and don't process more quantity than planned"))
    
    @api.model
    def create(self, vals):
        mr = self.env['material.request'].browse(vals.get('y_material_request_id'))
        if not vals['y_picking_type_id'] and  vals['y_request_type'] == 'stock':
            vals['y_picking_type_id'] = mr.y_picking_type_id.id
        if not vals['y_source_location_id'] and  vals['y_request_type'] == 'stock':
            vals['y_source_location_id'] = mr.y_source_location_id.id
        if not vals['y_dest_location_id'] and  vals['y_request_type'] == 'stock':
            vals['y_dest_location_id'] = mr.y_dest_location_id.id
        if vals.get('y_request_type') == 'purchase':
            if not vals.get('y_purchase_request_type_id'):
                vals['y_purchase_request_type_id'] = mr.y_purchase_request_type_id.id
        return super(MaterialRequestLine, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    y_mr_line_id = fields.Many2one('material.request.line',string="Material Request")
    
class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'
    
    y_mr_line_id = fields.Many2one('material.request.line',string="Material Request")