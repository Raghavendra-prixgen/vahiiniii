from odoo import api, fields, models,exceptions, _
from odoo.exceptions import ValidationError, UserError

class Reason(models.Model):
    _name = "weighment.reason"
    _description = "Weighment Picking"
    _rec_name = "y_name"

    y_name = fields.Char(string="Reason")

class WeighmentTrollyMoves(models.Model):
    _name = "weighment.trolly"
    _description = "WeighmentTrollyMoves"
    _rec_name ="y_trolly_id"

    y_weigh_trolly_id = fields.Many2one('weighment.picking',string="Weighment")
    y_trolly_id = fields.Many2one('maintenance.equipment',string="Trolley No.")
    y_empty_trolly_weight = fields.Integer(string="Empty Trolley Weight",related="y_trolly_id.y_weight",store=True)
    y_total_trolly_weight = fields.Float(string="Product Weight",store=True,compute="_calculate_trolly_weight")
    y_loaded_trolly_weight = fields.Float(string="Loaded Trolley Weight")
    y_weighment_type = fields.Many2one('weighment.picking.type',string="Weighment Type", related = "y_weigh_trolly_id.y_weighment_type",invisible=True)

    @api.depends('y_loaded_trolly_weight','y_empty_trolly_weight')
    def _calculate_trolly_weight(self):
        for line in self:
            if line.y_trolly_id:
                line.y_total_trolly_weight = line.y_loaded_trolly_weight - line.y_empty_trolly_weight
            else:
                line.y_total_trolly_weight = 0

    @api.onchange('y_empty_trolly_weight','y_loaded_trolly_weight')
    def _onchange_truck_weight(self):
        for line in self:
            if line.y_empty_trolly_weight > 0 or line.y_loaded_trolly_weight > 0:
                if not line.y_trolly_id:
                    raise ValidationError(_('Please Enter Trolley Number'))

class WeighmentPicking(models.Model):
    _name = "weighment.picking"
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = "Weighment Picking"
    _rec_name ="y_name"

    y_name = fields.Char(string="Weighment No.",readonly=True)
    y_weighment_type = fields.Many2one('weighment.picking.type',string="Type",store=True,readonly=True)
    y_order_type = fields.Selection(related='y_weighment_type.y_order_type',store=True)
    y_shipment_no = fields.Many2one('stock.picking',string="Shipment No.", domain="['&','&',('state','=','done'),('move_type','=','direct'),('sale_id', '=', y_sale_id)]")

    y_date = fields.Datetime(string="Date",default=fields.Datetime.now,readonly=True)
    y_user_id = fields.Many2one('res.users', string='User', readonly=True, default=lambda self: self.env.user)
    y_state = fields.Selection([('open', 'Open'),('release', 'Released'),('close', 'Closed'),('cancel', 'Cancel')], string='Status', default='open',tracking=True)
    
    #for capturing all the product details
    y_weighment_product_lines = fields.One2many('weighment.product','y_weigh_product_id')
    #for capturing all the truck details
    # y_weighment_truck_lines = fields.One2many('weighment.truck','y_weigh_truck_id')
    #for capturing all the trolly details
    y_weighment_trolly_lines = fields.One2many('weighment.trolly','y_weigh_trolly_id')
    #for capturing all the trolly details
    # y_weighment_vehicle_lines = fields.One2many('weighment.vehicle','y_weigh_vehicle_id')
    y_purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    y_purchase_ids = fields.Many2many('purchase.order', string='Purchase Orders',compute="_compute_weighment_purchase_orders")

    y_reason = fields.Many2one('weighment.reason',string='Reason')

    y_sale_id = fields.Many2one('sale.order', string='Sale Order')        
    y_sale_ids = fields.Many2many('sale.order', string='Sale Orders',compute="_compute_weighment_sale_orders")

    y_mo_id = fields.Many2one('mrp.production', string='Manufacturing Order')    
    y_mo_ids = fields.Many2many('mrp.production', string='Manufacturing Orders',compute="_compute_weighment_mo_orders")

    y_gate_in_id = fields.Many2one('gate.management',string="Gate In Number")
    y_gate_out_id = fields.Many2one('gate.management',string="Gate Out Number")

    y_workcenter_id = fields.Many2one('mrp.workcenter',string="Machine Number",domain="[('production_id','=',y_mo_id)]",readonly=True)

    y_total_products = fields.Float(string="Total Products",default=0.0,compute="_compute_total_qty")


    # y_total_truck_weight = fields.Float(string="Loaded Truck Weight",default=0.0,compute="_compute_total_qty")
    # y_empty_truck_weight = fields.Float(string="Empty Truck Weight",default=0.0,compute="_compute_total_qty")
    # y_gross_weight = fields.Float(string="Total Product Standard Weight",default=0.0,compute="_compute_total_qty")
    # y_tolerance = fields.Float(string="Tolerance",default=0.0,compute="_compute_total_qty")
    # y_net_weight = fields.Float(string = 'Net Actual Weight',compute="_total_net_weight")
    # y_difference = fields.Float(string='Difference',compute="_calculate_difference")


    y_total_truck_weight = fields.Float(string="Loaded Truck Weight",default=0.0)
    y_empty_truck_weight = fields.Float(string="Empty Truck Weight",default=0.0)
    y_gross_weight = fields.Float(string="Total Product Standard Weight",default=0.0,compute="_compute_total_qty")
    y_tolerance = fields.Float(string="Tolerance",default=0.0,compute="_compute_total_qty")
    y_net_weight = fields.Float(string = 'Net Actual Weight',compute="_total_net_weight")
    y_difference = fields.Float(string='Difference',compute="_calculate_difference")
    

    

    y_reference = fields.Char(string="Reference")
    y_deliver_line_id = fields.Many2one('stock.move',string="Stock move")

    y_vehicle_type = fields.Selection([('internal', 'Internal'),('external', 'External')], string='Vehicle Type', default='internal',tracking=True)


    y_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle Number")
    y_vehicle_number = fields.Char(string="Vehicle Number")

    y_total_weight = fields.Float(compute="calculate_total_weight",string="Total Weight",default=0.0)
    

    # y_sale_order_ids = fields.Many2many('sale.order',string="sale order")
    
    # y_related_pickings = fields.Many2many('stock.picking',compute='_compute_related_pickings', store=True)
    # y_pickings = fields.Float(compute='_compute_related_pickings', store=True)
    
   
                
                
    # @api.depends('y_sale_order_ids',)
    # def _compute_related_pickings(self):
    #     print("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")
    #     # for rec in self:
    #     #     rec.y_related_pickings = rec.y_sale_order_ids.mapped('picking_ids') if rec.y_sale_order_ids else self.env['stock.picking'].browse([]) 
    #     #     print(rec.y_related_pickings,"88888888888888888888888888888888888888888888")
    #     sale = []
    #     for rec in self:
    #         if rec.y_sale_order_ids :
    #            sale.append(rec.y_sale_order_ids.ids)
    #            print(sale,2222222222222222222222222222222222222222344444444)
    #            for sale in sale:
    #                rec.y_sale_order_ids = sale
    #         rec.y_pickings = 0
        
    
   
        
    
    
    
    
    @api.depends('y_total_products','y_total_truck_weight','y_empty_truck_weight','y_gross_weight','y_tolerance','y_net_weight','y_difference')
    def calculate_total_weight(self):
        for rec in self:
            rec.y_total_weight = rec.y_total_products  + rec.y_total_truck_weight + rec.y_empty_truck_weight + rec.y_gross_weight + rec.y_tolerance + rec.y_net_weight + rec.y_difference





    @api.depends('y_weighment_product_lines.y_purchase_line_id','y_weighment_product_lines.y_purchase_id')
    def _compute_weighment_purchase_orders(self):
        for weightment in self:
            weightment.y_purchase_ids = [(6,0,weightment.y_weighment_product_lines.y_purchase_line_id.mapped('order_id').ids)]

    @api.depends('y_weighment_product_lines.y_sale_line_id','y_weighment_product_lines.y_sale_id')
    def _compute_weighment_sale_orders(self):
        for weightment in self:
            weightment.y_sale_ids = [(6,0,weightment.y_weighment_product_lines.y_sale_line_id.mapped('order_id').ids)]

    @api.depends('y_weighment_product_lines.y_mo_id')
    def _compute_weighment_mo_orders(self):
        for weightment in self:
            weightment.y_mo_ids = [(6,0,weightment.y_weighment_product_lines.mapped('y_mo_id').ids)]

    @api.depends('y_weighment_product_lines.y_product_quantity')
    def _compute_total_qty(self):
        for line in self:
            line.y_gross_weight= 0
            total_product_qty = gross_weight  = tolerance = 0.00
            # print(line.y_weighment_product_lines)
            for qty in line.y_weighment_product_lines:
                total_product_qty += qty.y_product_quantity
                gross_weight += qty.y_gross_weight

            for tol in line.y_weighment_product_lines[:1]:
                tolerance += tol.y_tolerance

            line.y_total_products = total_product_qty
            line.y_tolerance = tolerance
            line.y_gross_weight = gross_weight or 0

    @api.depends('y_total_truck_weight','y_empty_truck_weight')
    def _total_net_weight(self):
        for order in self:
            order.y_net_weight = order.y_total_truck_weight - order.y_empty_truck_weight

    @api.depends('y_gross_weight','y_net_weight')
    def _calculate_difference(self):
        for line in self:
            line.y_difference = line.y_net_weight - line.y_gross_weight

    @api.onchange('weighment_product_lines')
    def _onchange_purchase_order_origin(self):
        purchase_order_ids = self.y_purchase_ids
        sale_order_ids = self.y_sale_ids
        shiping_order_ids = self.y_weighment_product_lines.mapped('y_shipment_no')
        mo_order_ids = self.y_mo_ids
        if purchase_order_ids:
            self.y_reference = ', '.join(purchase_order_ids.mapped('name'))
        if sale_order_ids:
            self.y_reference = ', '.join(sale_order_ids.mapped('name'))
        if mo_order_ids:
            self.y_reference = ', '.join(mo_order_ids.mapped('name'))
        if shiping_order_ids:
            self.y_reference = ', '.join(shiping_order_ids.mapped('name'))

    def _prepare_invoice_line_from_po_lines(self, line):
        invoice_line = self.env['weighment.product']
        data = {
            'y_purchase_id': line.order_id.id,
            'y_purchase_line_id': line.id,
            'y_description': line.name,
            'y_name': line.order_id.name,
            'y_product_id': line.product_id.id,
            'y_po_qty':line.product_qty
        }
        return data
    

    def action_create_weighment_product_line(self, data):
        new_line = self.env['weighment.product'].new(data)
        new_line._set_additional_po_order_fields(self)
        # print(new_line,"---------------------------------------new_line")
        existing_line = self.y_weighment_product_lines.filtered(lambda line: line.y_sale_id.id == data.get('y_sale_id') 
                                                                and line.y_shipment_no.id == data.get('y_shipment_no')and(line.y_line_id.id == data.get('y_line_id')))
        if existing_line:
            self.y_weighment_product_lines -= existing_line
           
        self.y_weighment_product_lines += new_line

    # def action_create_weighment_product_line(self,data):
    #     new_lines = self.env['weighment.product']
    #     new_line = new_lines.new(data)
    #     new_line._set_additional_po_order_fields(self)
    #     new_lines += new_line
    #     if self.y_weighment_product_lines:
    #         self.y_weighment_product_lines.unlink()
    #     self.y_weighment_product_lines += new_lines
    
    

# Load all unsold PO lines
    @api.onchange('y_purchase_id')
    def purchase_order_change(self):
        if not self.y_purchase_id:
            self.y_purchase_id = self.y_purchase_id
            return {}
        new_lines = self.env['weighment.product']
        for line in self.y_purchase_id.order_line - self.y_weighment_product_lines.mapped('y_purchase_line_id'):
            data = self._prepare_invoice_line_from_po_lines(line)
            self.action_create_weighment_product_line(data)

        self.env.context = dict(self.env.context, from_purchase_order_change=True)
        self.y_purchase_id = False
        self.y_sale_id = False
        self.y_mo_id = False
        self.y_shipment_no = False
        self._onchange_purchase_order_origin()

    def _prepare_invoice_line_from_so_lines(self, line):
        invoice_line = self.env['weighment.product']
        data = {
            'y_sale_id': line.order_id.id,
            'y_description': line.name,
            'y_name': line.order_id.name+': '+line.name,
            'y_product_id': line.product_id.id,
            'y_so_qty':line.product_uom_qty
        }
        return data

    # Load all unsold SO lines
    @api.onchange('y_sale_id')
    def sale_order_change(self):
        if not self.y_sale_id:
            self.y_sale_id = self.y_sale_id
            return {}

        # new_lines = self.env['weighment.product']
        # for line in self.y_sale_id.order_line - self.y_weighment_product_lines.mapped('y_sale_line_id'):
        #     data = self._prepare_invoice_line_from_so_lines(line)
        #     self.action_create_weighment_product_line(data)
        # self.y_sale_order_ids = self.y_sale_id
        self.env.context = dict(self.env.context, from_sale_order_change=True)
        # self.y_sale_id = False
        self.y_purchase_id = False
        self.y_mo_id = False
        self.y_shipment_no = False
        self._onchange_purchase_order_origin()
    
    
    
    def _prepare_invoice_line_from_deliver_lines(self, line):
        invoice_line = self.env['weighment.product']
        
        data = {
            'y_shipment_no': line.picking_id.id,
            'y_description': line.name,
            'y_name': line.picking_id.name+': '+line.name,
            'y_product_id': line.product_id.id,
            'y_so_qty':line.product_uom_qty,
            'y_product_quantity':line.quantity,
            # 'y_product_quantity':line.y_quantity_done,
            'y_sale_id': line.picking_id.sale_id.id,
            'y_line_id' : line.id
            
        }
        return data
    

    
    @api.onchange('y_shipment_no')
    def deliver_order_change(self):
        if not self.y_shipment_no:
            self.y_shipment_no = self.y_shipment_no
            return {}

        new_lines = self.env['weighment.product']
        for line in self.y_shipment_no.move_ids_without_package - self.y_weighment_product_lines.mapped('y_deliver_line_id'):
            data = self._prepare_invoice_line_from_deliver_lines(line)
            self.action_create_weighment_product_line(data)
            
        self.env.context = dict(self.env.context, from_sale_order_change=True)
        self.y_shipment_no = False
        self.y_purchase_id = False
        self.y_mo_id = False
        self._onchange_purchase_order_origin()
        
        
    

    def _prepare_invoice_line_from_mo_lines(self, line):
        invoice_line = self.env['weighment.product']
        data = {
            'y_mo_id': line.id,
            'y_name': line.name,
            'y_description': line.name,
            'y_product_id': line.product_id.id,
            'y_mo_qty': line.product_qty
        }
        return data

 # Load all unsold MO lines
    @api.onchange('y_mo_id')
    def mo_order_change(self):
        if not self.y_mo_id:
            self.y_mo_id = self.y_mo_id
            return {}

        new_lines = self.env['weighment.product']
        for line in self.y_mo_id - self.y_weighment_product_lines.mapped('y_mo_id'):
            data = self._prepare_invoice_line_from_mo_lines(line)
            self.action_create_weighment_product_line(data)            

        self.y_weighment_product_lines += new_lines
        self.env.context = dict(self.env.context, from_mo_order_change=True)
        self.y_mo_id = False
        self.y_purchase_id = False
        self.y_sale_id = False
        self._onchange_purchase_order_origin()

    def create(self, values):
        # Check the order type and use the appropriate sequence
        if values.get('y_order_type') == 'purchase':
            values['y_name'] = self.env['ir.sequence'].next_by_code('weighment.picking.purchase')
        if values.get('y_order_type') == 'sales':
            values['y_name'] = self.env['ir.sequence'].next_by_code('weighment.picking.sales')
        if values.get('y_order_type') == 'manufacturing':
            values['y_name'] = self.env['ir.sequence'].next_by_code('weighment.picking.manufacturing')
        return super(WeighmentPicking, self).create(values)

    
    def button_close(self):
        self.y_state = 'close'
        for rec in self:
            self.y_weighment_product_lines.mapped('y_mo_id').write({'y_fg_actual_weight':rec.y_net_weight})

    def button_reset(self):
        self.y_state = 'open'

    def button_cancel(self):
        self.y_state = 'cancel'
        self.y_weighment_product_lines.y_purchase_line_id.mapped('order_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':False})
        self.y_weighment_product_lines.y_sale_line_id.mapped('order_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':False})
        self.y_weighment_product_lines.mapped('y_mo_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':False})



    def button_validate(self):
        for rec in self:
            if rec.y_state == 'open':
                rec.write({'y_state':'close'})

                
    
    def calculate_tolerance_limit(self):
        for line in self:
            actual_weight = 0
            difference_weight = 0
            actual_weight = (line.y_gross_weight) * line.y_tolerance / 100
            actual_weight_less = -(line.y_gross_weight) * line.y_tolerance / 100
            difference_weight = ((line.y_net_weight) * line.y_tolerance / 100)
            if actual_weight < line.y_difference:
                raise ValidationError(("Total Weight is above Tolerance limit. Tolerance limit is '%s'. Difference weight is '%s'.") % (actual_weight,line.y_difference))
            elif actual_weight_less > line.y_difference:
                raise ValidationError(("Total Weight is below Tolerance limit. Tolerance limit is '%s'. Difference weight is '%s'.") % (actual_weight_less,line.y_difference))
            else:
                self.y_weighment_product_lines.y_purchase_line_id.mapped('order_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':True})
                self.y_weighment_product_lines.y_sale_line_id.mapped('order_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':True})
                self.y_weighment_product_lines.mapped('y_mo_id').filtered(lambda x:x.y_is_order_completed == False).write({'y_is_final_display':True})
                self.y_weighment_product_lines.mapped('y_mo_id').write({'y_fg_actual_weight':line.y_net_weight})
                self.write({'y_state':'release'})


# #adding the truck details
# class WeighmentTruckMoves(models.Model):
#     _name = "weighment.truck"
#     _description = "WeighmentTruckMoves"
#     _rec_name ="y_weigh_truck_id"

#     y_weigh_truck_id = fields.Many2one('weighment.picking',string="Weighment Moves")
#     y_truck_id = fields.Many2one('fleet.vehicle',string="Vehicle No.")
#     y_empty_truck_weight = fields.Integer(string="Empty Truck Weight")
#     y_total_truck_weight = fields.Float(string="Product Weight",store=True,compute="_calculate_truck_weight")
#     y_loaded_truck_weight = fields.Float(string="Loaded Truck Weight")
#     y_weighment_type = fields.Many2one('weighment.picking.type',string="Weighment Type",related="y_weigh_truck_id.y_weighment_type",invisible=True)

#     @api.depends('y_loaded_truck_weight','y_empty_truck_weight')
#     def _calculate_truck_weight(self):
#         for line in self:
#             if line.y_truck_id:
#                 line.y_total_truck_weight = line.y_loaded_truck_weight - line.y_empty_truck_weight

#     @api.onchange('y_empty_truck_weight','y_loaded_truck_weight')
#     def _onchange_truck_weight(self):
#         for line in self:
#             if line.y_empty_truck_weight > 0 or line.y_loaded_truck_weight > 0:
#                 if not line.y_truck_id:
#                     raise ValidationError(_('Please Enter Vehicle Number'))

# class WeighmentVehicleMoves(models.Model):
#     _name = "weighment.vehicle"
#     _description = "WeighmentVehicleMoves"
#     _rec_name = "y_weigh_vehicle_id"

#     y_weigh_vehicle_id = fields.Many2one('weighment.picking',string="Weighment")
#     y_vehicle_no = fields.Char(string="Vehicle No.")
#     y_empty_vehicle_weight = fields.Integer(string="Empty Vehicle Weight")
#     y_total_vehicle_weight = fields.Float(string="Product Weight",store=True,compute="_calculate_vehicle_weight")
#     y_loaded_vehicle_weight = fields.Float(string="Loaded Vehicle Weight")
#     y_weighment_type = fields.Many2one('weighment.picking.type',string="Weighment Type", related="y_weigh_vehicle_id.y_weighment_type",invisible=True)

#     @api.depends('y_loaded_vehicle_weight','y_empty_vehicle_weight')
#     def _calculate_vehicle_weight(self):
#         for line in self:
#             if line.y_vehicle_no:
#                 line.y_total_vehicle_weight = line.y_loaded_vehicle_weight - line.y_empty_vehicle_weight

#     @api.onchange('y_empty_vehicle_weight','y_loaded_vehicle_weight')
#     def _onchange_truck_weight(self):
#         for line in self:
#             if line.y_empty_vehicle_weight > 0 or line.y_loaded_vehicle_weight > 0:
#                 if not line.y_vehicle_no:
#                     raise ValidationError(_('Please Enter Vehicle Number'))


#new class for capturing products
class WeighmentProductMoves(models.Model):
    _name = "weighment.product"
    _description = "WeighmentProductMoves"
    _rec_name = "y_name"
    
    y_weigh_product_id = fields.Many2one('weighment.picking',string="Weighment")

    y_product_id = fields.Many2one('product.product',string="Product")
    y_name = fields.Char(string="Move name")
    y_description = fields.Char(string="Description")
    y_product_uom = fields.Many2one('uom.uom', string='UOM',related="y_product_id.uom_id",readonly=True)
    y_product_quantity = fields.Float(string='Quantity', store=True)
    y_po_qty = fields.Float(string="PO Qty",store=True)
    y_so_qty = fields.Float(string="SO Qty",store=True)
    y_mo_qty = fields.Float(string="MO Qty",store=True)
    y_product_batch = fields.Char(string='Batch')
    y_std_weight = fields.Float(string='Standard Weight Per',related="y_product_id.weight",readonly=True)
    
    y_gross_weight = fields.Float(string='Net Standard Weight',compute="_calculate_gross")
    y_tolerance = fields.Float(string='Tolerance',related="y_product_id.y_tolerance",readonly=True)
    y_weighment_type = fields.Many2one('weighment.picking.type',string="Weighment Type", related="y_weigh_product_id.y_weighment_type",invisible=True)

    y_purchase_line_id = fields.Many2one('purchase.order.line',string="Purchase order line")
    y_purchase_id = fields.Many2one('purchase.order',string="Purchase order")

    y_sale_line_id = fields.Many2one('sale.order.line',string="Sale order line")
    y_sale_id = fields.Many2one('sale.order',string="Sale order")

    y_mo_id = fields.Many2one('mrp.production',string="Manufacturing order")
    y_deliver_line_id = fields.Many2one('stock.move',string="Stock move")
    y_shipment_no = fields.Many2one('stock.picking',string="Shipment No.")
    y_line_id = fields.Many2one('stock.move',string="Move Id")
    

    #calculating the net standard weight
    @api.depends('y_product_quantity','y_std_weight')
    def _calculate_gross(self):
        for line in self:
            line.y_gross_weight = line.y_product_quantity * line.y_std_weight

    def _set_additional_po_order_fields(self, invoice):
        """ Some modules, such as Purchase, provide a feature to add automatically pre-filled
            invoice lines. However, these modules might not be aware of extra fields which are
            added by extensions of the accounting module.
            This method is intended to be overridden by these extensions, so that any new field can
            easily be auto-filled as well.
            :param invoice : account.invoice corresponding record
            :rtype line : account.invoice.line record
        """
        pass   
#store true quantity_done

