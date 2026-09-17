from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime, date
from datetime import datetime, timedelta, timezone
import random
import logging
import time
from odoo import api, fields, models, tools, _
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as GD
from odoo.osv import expression
_logger = logging.getLogger(__name__)

CLOSED_STATES = {
    '1_done': 'Done',
    '1_canceled': 'Canceled',
}

TRANSPORT_ORDER_STATE_SELECTION = [
        ('collectice_shipment', 'Collective Shipment'),
        ('individual_shipment', 'Individual Shipment'),        
]

SHIPPING_TYPE_STATE_SELECTION = [
        ('truck', 'By Truck'),
        ('mail', 'By Mail'),
        ('train', 'By Train'),
        ('ship', 'By Ship'),
        ('airplane', 'By Air'),
        ]

SHPMTCOMPLTYPE = [
        ('loaded_outbound_shipment', 'Loaded Outbound Shipment'),
        ('loaded_inbound_shipment', 'Loaded Inbound Shipment'),
        ('empyt_outbound_shipment', 'Empty Outbound Shipment'),
        ('empyt_inbound_shipment', 'Empty Outbound Shipment'),
        ]

ProcessControl = [
        ('inv_shipmt_one_mode', 'Individual Shipment using one mode of transport'),
        ('inv_shipmt_several_mode', 'Individual Shipment using several mode of transport'),
        ('collective_shpmt_one_mode', 'Collective Shipment using one mode of transport'),
        ('collective_shpmt_several_mode', 'Collective Shipment using several mode of transport'),
]

DETERMINELEGSTATES = [
        ('blank', 'No legs to be determined'),
        ('0', 'Only determine assigment of deliveries of stages'),
        ('1', 'Legs determined according to departure point & itinerary'),
        ('2', 'Prelim.leg per loading point,subsqnt leg per ship-to-pty'),
        ('3', 'Determine preliminary and subsequent leg by delivery note'),
        ('4', 'AS 1,but ship .type for prel and subs legs changeble'),
]

TRANSPORTATIONPARTNER = [
        ('SP', 'Forwarding agent'),
        ('TF', 'Freight service agt'),
        ('TL', 'Head of lading'),
        ('TR', 'Cleaning firm'),
        ('TV', 'Insurance'),
]

WEIGHTSELECTION = [
        ('3mt', 'Upto 3 MT'),
        ('5mt', 'Upto 5 MT'),
        ('7mt', 'Upto 7 MT'),
        ('9mt', 'Upto 9 MT'),
        ('15mt', 'Upto 15 MT'),
        ('20mt', 'Upto 20 MT'),
        ('25mt', 'Upto 25 MT'),
        ('28mt', 'Upto 28 MT'),
        ('above28mt', 'Above 28 MT'),
        ('dnknw', 'Do Not Know'),
        ('above40mt', 'Above 40 MT'),
        ('12mt', 'Upto 12 MT'),
]

OVERALLSTATUSSELECTION = [
        ('planned', 'Planned'),
        ('planning_completed', 'Planning completed'),
        ('checkin', 'Chcek in'),
        ('loading_start', 'Loading start'),
        ('loading_end', 'Loading end'),
        ('shipment_completion', 'Shipment completion'),
        ('shipment_start', 'Shipment start'),
        ('shipment_end', 'Shipment end'),
]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    y_is_transporter = fields.Boolean(string="Is Transporter")

# class PurchaseShipmentTrack(models.Model):
#     _inherit = 'purchase.shipment'

#     def button_calculate_fleet_indent(self):
#         for rec in self:
#             fleet_vals = {
#             'y_date_of_transport':datetime.now().date()
#             }
#             fleet_indent_obj = self.env['fleet.vehicle.intent'].create(fleet_vals)
#             for picking in rec.y_purchase_id.picking_ids:
#                 fleet_indent_obj.y_fleet_vehicle_intent_line_ids = [(0,0,{
#                 'y_fleet_vehicle_intent_id':fleet_indent_obj.id,
#                 'y_picking_id':picking.id,
#                 'y_source_location_id':picking.location_id.id,
#                 'y_destination_location_id':picking.location_dest_id.id,
               
#                 })]
#             break
        
class ResCities(models.Model):
    _name = "res.state.city"
    _description = "Cities"
    _rec_name = "y_name"

    _sql_constraints = [('name_uniq', "unique(y_name, y_locality,y_state_id, y_country_id)", "A city with the same name and locality and state already exists in this country.")]

    y_name = fields.Char(string="Name")
    street = fields.Char(string="Street")
    y_state_id = fields.Many2one('res.country.state',string="States")
    y_country_id = fields.Many2one('res.country',string="Country")
    gps_coordinates = fields.Char(string='GPS Coordinates', compute="_compute_gps_coordinates")
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    y_locality = fields.Char(string="Locality")


    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        city_ids = self.search_fetch(expression.AND([domain, ['|',('y_state_id',operator,name),('y_locality', operator, name)]]), ['display_name'], limit=limit)
        result.extend((city_name.id, city_name.display_name) for city_name in city_ids.sudo())
        domain = expression.AND([domain, [('id', 'not in', city_ids.ids)]])
        if limit is not None:
            limit -= len(city_ids)
            if limit <= 0:
                return result
        result.extend(super().name_search(name, domain, operator, limit))
        return result

    @api.depends('y_name', 'y_locality')
    def _compute_display_name(self):
        for rec in self:
            name = rec.y_name
            if rec.y_locality:
                name += ' [' + rec.y_locality + ']'
            rec.display_name = name

    @api.onchange('street','y_name','y_state_id')
    def _onchange_street_get_coordinates(self):
        if self.y_name and self.y_state_id:
            street = self.street or ""
            city = self.y_name or ""
            state = self.y_state_id.name if self.y_state_id else ""
            address = f"{street} {city} {state}"
            geolocator = Nominatim(user_agent="myGeocodeApp_v1")
            try:
                location = geolocator.geocode(address, timeout=10) 
                if location:
                    _logger.info(f"location found for {address}! - {location.latitude, location.longitude}")
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                    self.write({
                        'latitude': location.latitude,
                        'longitude': location.longitude
                    })
                else:
                    _logger.warning(f"location not found for address {address} ")
            except Exception as e:
                _logger.warning(f"error at {e}")

    @api.onchange('street','y_name','y_state_id')
    def _compute_gps_coordinates(self):
        if self.latitude and self.longitude:
            self.gps_coordinates = f"{self.latitude}, {self.longitude}"
        else: self.gps_coordinates = "GPS Not Available"

class FleetVehicleIntent(models.Model):
    _name = 'fleet.vehicle.intent'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'y_name'
    _description = 'Vehicle Intent'

    y_name = fields.Char(string="Code" ,default=lambda self: _('New'), readonly=True)
    y_status = fields.Selection([
        ('draft', 'Draft'),
        ('released', 'Released'),
        ('cancel', 'Cancelled')
    ], string='Status',default='draft',copy=False,tracking=True)
    y_date_of_transport = fields.Date(string="Date of Transport",tracking=True)
    y_remark = fields.Char(string="Remark",tracking=True)
    y_company_id = fields.Many2one('res.company', default=lambda self: self.env.company,string="Company",tracking=True)
    y_from_city_id = fields.Many2one('res.state.city',string="From",tracking=True)
    y_to_city_id = fields.Many2one('res.state.city',string="To",tracking=True)
    y_fleet_vehicle_intent_line_ids = fields.One2many('fleet.vehicle.intent.line','y_fleet_vehicle_intent_id',string="Vehicle Intent Lines")
    y_transportation_order_id = fields.Many2one('transportation.order',copy=False,string="Transportation Order")

    # Vehical Category
    vehicle_category_id = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Category",tracking=True)
    vehicle_weight_capacity = fields.Float(string="Vehcilce Payload Capacity",related='vehicle_category_id.weight_capacity')
    weight_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_weight_uom_name')    
    used_weight_percentage = fields.Float(string="Weight %", compute='_compute_capacity_percentage')
    estimated_shipping_weight = fields.Float("Weight", compute='_compute_estimated_shipping_capacity', digits='Product Unit of Measure')
    y_vehicle_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('cust_ven','Customer/Vendor')
    ], string='Vehicle Type',tracking=True,default='external')

    y_sale_order_ids = fields.Many2many('sale.order',string ='Sale Order',compute="fetch_sale_Order_customer",store=True)
    y_customer_ids = fields.Many2many('res.partner',string='Customer',compute="fetch_sale_Order_customer",store=True)


    @api.depends('y_fleet_vehicle_intent_line_ids','y_fleet_vehicle_intent_line_ids.y_picking_id')
    def fetch_sale_Order_customer(self):
        for rec in self:
            if rec.y_fleet_vehicle_intent_line_ids:

                rec.y_sale_order_ids = rec.y_fleet_vehicle_intent_line_ids.filtered(lambda x:x.y_picking_id).mapped('y_picking_id').mapped('sale_id')
                rec.y_customer_ids = rec.y_fleet_vehicle_intent_line_ids.filtered(lambda x:x.y_picking_id).mapped('y_picking_id').mapped('partner_id')
            else:
                rec.y_sale_order_ids = False
                rec.y_customer_ids = False









    @api.constrains('y_from_city_id','y_to_city_id')
    def _check_from_to_city(self):
        for indent in self:
            if indent.y_from_city_id and indent.y_to_city_id:
                if indent.y_from_city_id == indent.y_to_city_id and indent.y_from_city_id.y_locality == indent.y_to_city_id.y_locality:
                    raise UserError("From and To city of selected indents must be same.")


    # vehicle_volume_capacity = fields.Float(string="Max Volume (m³)",related='vehicle_category_id.volume_capacity')
    # volume_uom_name = fields.Char(string='Volume unit of measure label', compute='_compute_volume_uom_name')
    # used_volume_percentage = fields.Float(string="Volume %", compute='_compute_capacity_percentage')
    # estimated_shipping_volume = fields.Float("shipping_volume", compute='_compute_estimated_shipping_capacity', digits='Product Unit of Measure')

    def _compute_weight_uom_name(self):
        self.weight_uom_name = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    # def _compute_volume_uom_name(self):
    #     self.volume_uom_name = self.env['product.template']._get_volume_uom_name_from_ir_config_parameter()

    @api.depends('y_fleet_vehicle_intent_line_ids.y_picking_id')
    def _compute_estimated_shipping_capacity(self):
        for indent in self:
            indent.estimated_shipping_weight = sum(indent.y_fleet_vehicle_intent_line_ids.mapped('y_weight'))
            # estimated_shipping_volume = 0
            # for move in self.y_fleet_vehicle_intent_line_ids.y_picking_id.move_ids:
            #     estimated_shipping_weight += move.product_id.weight * move.product_qty
                # estimated_shipping_volume += move.product_id.volume * move.product_qty
        
    @api.depends('estimated_shipping_weight', 'vehicle_category_id.weight_capacity')
    def _compute_capacity_percentage(self):
        self.used_weight_percentage = False
        # self.used_volume_percentage = False
        for indent in self:
            if indent.vehicle_weight_capacity:
                indent.used_weight_percentage = 100 * (indent.estimated_shipping_weight / indent.vehicle_weight_capacity)
            # if indent.vehicle_volume_capacity:
            #     indent.used_volume_percentage = 100 * (indent.estimated_shipping_volume / indent.vehicle_volume_capacity)

    def create_transportation_order(self):
        transportation_order_id = self.env['transportation.order']
        from_city_ids = self.mapped('y_from_city_id')
        to_city_ids = self.mapped('y_to_city_id')
        for indent in self:
            if indent.y_transportation_order_id:
                raise UserError(_("Indent already created for this transportation order"))
            if indent.y_status != 'released':
                raise ValidationError("In order to create a transportation order, the indent must be in the released state.")
            if not indent.y_fleet_vehicle_intent_line_ids:
                raise ValidationError("In order to create a transportation order, the indent must have pickings.")


            from_city = False if len(from_city_ids) > 1 and from_city_ids else from_city_ids[0]
            to_city = False if len(to_city_ids) > 1 and to_city_ids else to_city_ids[0]
            vals = {
            'y_from_city_id': from_city.id,
            'y_to_city_id':to_city.id,
            'y_vehicle_category_id':indent.vehicle_category_id.id,
            'y_vehicle_type':indent.y_vehicle_type,
            'y_company_id':indent.y_company_id.id,
            }
            transportation_order_id = transportation_order_id.create(vals)
            indent.write({'y_transportation_order_id':transportation_order_id.id})
            for indent_lines in indent.y_fleet_vehicle_intent_line_ids:
                transportation_order_id.y_transportation_order_intent_line_ids = [(0,0,{
                'y_fleet_indent_id':indent.id,
                'y_transportation_order_id':transportation_order_id.id,
                'y_picking_id':indent_lines.y_picking_id.id,
                'from_city':indent_lines.y_from_city ,
                'to_city':indent_lines.y_to_city,
                'y_indent_line_id':indent_lines.id,
                'y_weight':indent_lines.y_weight,
               
                })]
        return self.action_view_transportation_order()

    def action_posted(self):
        for rec in self:
            if not rec.y_fleet_vehicle_intent_line_ids:
                raise ValidationError("Picking's required to release.")
            rec.write({'y_status':'released'})

    def button_reset_draft(self):
        for rec in self:
            rec.write({'y_status':'draft'})

    def button_cancel(self):
        for rec in self:
            if rec.y_transportation_order_id:
                raise ValidationError("Once a transportation order has been created, it should not be canceled.")
            rec.write({'y_status':'cancel'})
    
    @api.model
    def create(self, vals):
        if vals:
            company_id = self.env['res.company'].sudo().search([('id','=',vals.get('y_company_id'))])
            vehicle_intent_sequence_id = company_id.y_vehicle_intent_sequence_id
            if company_id.sudo().parent_id:
                vehicle_intent_sequence_id = company_id.sudo().parent_id.y_vehicle_intent_sequence_id
            if not vehicle_intent_sequence_id:
                raise UserError("Vehicle Indent Sequence not configured in Settings")
            vals['y_name'] = vehicle_intent_sequence_id.next_by_id() or _('New')
        res = super(FleetVehicleIntent, self).create(vals)
        return res


    def action_execute(self):
        transportation_order_id = self.env['transportation.order'].browse(self._context.get('record_id'))
        for indent in self.filtered(lambda x:not x.y_transportation_order_id and x.id not in transportation_order_id.y_transportation_order_intent_line_ids.y_fleet_indent_id.ids):
            for fleet in indent.y_fleet_vehicle_intent_line_ids:
                transportation_order_id.y_transportation_order_intent_line_ids = [(0,0,{
                'y_transportation_order_id':transportation_order_id.id,
                'y_fleet_indent_id':fleet.y_fleet_vehicle_intent_id.id,
                'y_picking_id':fleet.y_picking_id.id,
                'from_city':fleet.y_from_city,
                'to_city':fleet.y_to_city,
                })]

    def get_picking(self):
        if self.y_status != 'draft':
            raise ValidationError("You can add pickings only in draft state.")
        tree_view = self.env.ref('fleet_module_18.view_stock_picking_fleet_tree')
        domain = [('picking_type_code', 'in', ('incoming','outgoing','internal')),('state','in',('assigned','confirmed','done')),('company_id','=',self.y_company_id.id),('id','not in',self.y_fleet_vehicle_intent_line_ids.y_picking_id.ids),('y_transportation_order_id','=',False)]
        return {
            'name': 'Pickings',
            'view_mode': 'list',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'views': [(tree_view.id, 'list')],
            'context':{'record_id':self.id,'create': False}
        }

    def action_view_transportation_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("fleet_module_18.action_fleet_transportation_order")
        action['views'] = [
            (self.env.ref('fleet_module_18.view_fleet_transportation_order_kanban').id,'kanban'),
            (self.env.ref('fleet_module_18.view_fleet_transportation_order_tree').id, 'list'),
            (self.env.ref('fleet_module_18.view_fleet_transportation_order_form').id,'form')
        ]
        action['context'] = self.env.context
        action['domain'] = [('id', '=', self.y_transportation_order_id.id)]
        return action


class FleetVehicleIndentLine(models.Model):
    _name = 'fleet.vehicle.intent.line'
    _description = 'Fleet Vehicle Indent Line'

    y_fleet_vehicle_intent_id = fields.Many2one('fleet.vehicle.intent',string="Fleet Vehicle Indent")
    y_picking_id = fields.Many2one('stock.picking',string="Picking",domain="[('state','in',('assigned','done')),('picking_type_code', 'in', ('incoming','outgoing','internal')),('y_transportation_order_id','=',False)]")
    y_from_city = fields.Char(string="From",related="y_fleet_vehicle_intent_id.y_from_city_id.y_name")
    y_to_city = fields.Char(string="To",related="y_fleet_vehicle_intent_id.y_to_city_id.y_name")
    y_scheduled_date = fields.Datetime(string="Scheduled Date",related="y_picking_id.scheduled_date")
    y_weight = fields.Float(string="Weight",compute="_compute_picking_weight")
    y_source_document = fields.Char(related="y_picking_id.origin")
    y_partner_id = fields.Many2one('res.partner',related="y_picking_id.partner_id")
    y_picking_state = fields.Selection(related="y_picking_id.state")

    @api.depends('y_picking_id.move_ids')
    def _compute_picking_weight(self):
        for line in self:
            weight = 0
            for move in line.y_picking_id.move_ids:
                weight += move.product_id.weight * move.product_uom_qty
            line.y_weight = weight

    @api.onchange('y_picking_id')
    def _onchange_picking(self):
        for line in self:
            if line.y_picking_id:
                if line.y_picking_id.company_id != line.y_fleet_vehicle_intent_id.y_company_id:
                    raise UserError("You are allowed to add picking's exclusively for the vehicle indent company '{}'.".format(line.y_fleet_vehicle_intent_id.y_company_id.name))

class ResCompany(models.Model):
    _inherit = 'res.company'

    y_vehicle_intent_sequence_id = fields.Many2one('ir.sequence',string="Vehicle Intent Sequence")
    y_transportation_order_sequence_id = fields.Many2one('ir.sequence',string="Transporation Order Sequence")
    y_freight_cost_master_sequence_id = fields.Many2one('ir.sequence',string="Freight Cost Master")
    y_transportation_order_approver_ids = fields.Many2many('res.users','transportation_order_comapny_approval_rel',string="Transportation Approver")
    y_transportation_product_id = fields.Many2one('product.product',string="Product")
    y_transportation_journal_id = fields.Many2one('account.journal',string="Journal")
    
    
class ResConfigSettingfleet(models.TransientModel):
    _inherit = 'res.config.settings'   

    y_vehicle_intent_sequence_id = fields.Many2one('ir.sequence',string="Vehicle Intent Sequence",readonly=False,related="company_id.y_vehicle_intent_sequence_id")
    y_transportation_order_sequence_id = fields.Many2one('ir.sequence',string="Transporation Order Sequence",readonly=False,related="company_id.y_transportation_order_sequence_id")
    y_freight_cost_master_sequence_id = fields.Many2one('ir.sequence',string="Freight Cost Master",readonly=False,related="company_id.y_freight_cost_master_sequence_id")
    y_transportation_order_approver_ids = fields.Many2many('res.users','transportation_order_approval_rel',string="Transportation Approver",readonly=False,related="company_id.y_transportation_order_approver_ids")
    y_transportation_product_id = fields.Many2one('product.product',string="Product",readonly=False,related="company_id.y_transportation_product_id")
    y_transportation_journal_id = fields.Many2one('account.journal',string="Journal",readonly=False,related="company_id.y_transportation_journal_id")
    
class StockPickingfleet(models.Model):
    _inherit = 'stock.picking'

    y_vehicle_intent_id = fields.Many2one('fleet.vehicle.intent', string='Vehicle Intent', readonly=True,copy=False)
    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order",copy=False)
    y_driver_number = fields.Char(string="Driver Number",copy=False)
    y_vehicle_intent_number = fields.Char(string='Vehicle indents',copy=False)
    y_overall_status= fields.Selection(
        selection=OVERALLSTATUSSELECTION,
        string="Overall status",
        copy=False,
        default='planned',
        tracking=True)
    y_lr_date = fields.Date(string="LR Date",copy=False)
    y_lr_number = fields.Char(string="LR Number",copy=False)
    y_vehicle_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('cust_ven','Customer/Vendor')
    ], string='Vehicle Type',tracking=True,copy=False)
    y_vehicle_number = fields.Char(string="Vehicle Number",copy=False)

    y_fleet_indent_line_ids = fields.One2many('fleet.vehicle.intent.line','y_picking_id',string="Fleet Indent Lines")

    def action_create_vehicle_intent(self):
        pickings = self.env['stock.picking'].browse(self._context.get('active_ids'))
        if not all(pickings.mapped('y_vehicle_type')):
            raise UserError(_("Please map vehicle type"))


        if 'cust_ven' in pickings.filtered(lambda x:x.y_vehicle_type).mapped('y_vehicle_type'):
            raise UserError(_("Vehicle indent cannot be created for this type of vehicle."))
        
        company_id_ids = set([order.company_id for order in pickings])
        if len(company_id_ids) > 1:
            raise UserError(_('You can only create vehicle indent of identical company.'))

        total_weight = sum(pickings.mapped('weight'))
        vals = {
                'y_date_of_transport': fields.Date.today(),
                'y_status': 'draft',
                'y_company_id':pickings.mapped('company_id').id,
                }
        
        fleet_indent_id = self.env['fleet.vehicle.intent'].create(vals)
        pickings_ids = pickings.filtered(lambda x:x.picking_type_code in ('incoming','outgoing','internal') and x.state in ('assigned','confirmed','done'))
        for picking in pickings_ids:
            picking.y_vehicle_intent_id = fleet_indent_id.id
            fleet_indent_id.y_fleet_vehicle_intent_line_ids = [(0,0,{
            'y_fleet_vehicle_intent_id':fleet_indent_id.id,
            'y_picking_id':picking.id,
            'y_from_city':picking.location_id.warehouse_id.partner_id.city,
            'y_to_city':picking.location_dest_id.warehouse_id.partner_id.city,           
            })]

        return self.action_view_indent()

    def create_transportation_order_lines(self):
        transportation_order_id = self.env['transportation.order'].browse(self._context.get('record_id'))
        for fleet in self:
            weight = sum([move.product_id.weight * move.product_uom_qty for move in fleet.move_ids])
            transportation_order_id.y_transportation_order_intent_line_ids = [(0,0,{
            'y_transportation_order_id':transportation_order_id.id,
            'y_picking_id':fleet.id,
            'from_city':fleet.location_id.warehouse_id.partner_id.city,
            'to_city':fleet.location_dest_id.warehouse_id.partner_id.city,
            'y_other_weight':weight,   
            })]

    def create_fleet_indent_lines(self):
        fleet_indent_id = self.env['fleet.vehicle.intent'].browse(self._context.get('record_id'))
        for picking in self:
            fleet_indent_id.y_fleet_vehicle_intent_line_ids = [(0,0,{
            'y_fleet_vehicle_intent_id':fleet_indent_id.id,
            'y_picking_id':picking.id,
            'y_weight':picking.weight,
            'y_from_city':picking.partner_id.city,
            'y_to_city':picking.location_dest_id.warehouse_id.partner_id.city,
            })]

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.y_transportation_order_id:
                landed_cost = self.env['stock.landed.cost'].search([('y_transportation_order_id','=',picking.y_transportation_order_id.id)])
                landed_cost.picking_ids = [(4, picking.id)]
            if not picking.y_vehicle_type and picking.picking_type_code in ('incoming','outgoing'):
                raise ValidationError("Vehicle Type required to validate.")

        return res

    def action_view_indent(self):
        action = self.env["ir.actions.actions"]._for_xml_id("fleet_module_18.action_fleet_vehicle_intent")
        action['views'] = [
            (self.env.ref('fleet_module_18.view_fleet_vehicle_intent_tree').id, 'list'),
            (self.env.ref('fleet_module_18.view_fleet_vehicle_intent_form').id,'form')
        ]
        action['context'] = self.env.context
        action['domain'] = [('id', 'in', self.y_fleet_indent_line_ids.mapped('y_fleet_vehicle_intent_id').ids)]
        return action

class SaleOrder(models.Model):
    _inherit = "sale.order"

    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")

class AccountMove(models.Model):
    _inherit = "account.move"

    y_lr_date = fields.Date( string="LR Date")
    y_lr_number = fields.Char(string="LR Number")
    y_tender_status = fields.Selection([
        ('withcontract', 'With Contract'),
        ('withoutcontract', 'With Out Contract'),       
    ], string='Service Level',tracking=True)
    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")

    def action_post(self):
        res = super().action_post()
        for bill in self:
            if bill.y_transportation_order_id:
                bill.y_transportation_order_id.write({'y_purchase_invoice_status':'fully_billed'})
        return res




    
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")
    y_lr_date = fields.Date(related="y_transportation_order_id.y_lr_date", string="LR Date")
    y_lr_number = fields.Char(string="LR Number")
    y_tender_status = fields.Selection([
        ('withcontract', 'With Contract'),
        ('withoutcontract', 'With Out Contract'),
    ],related="y_transportation_order_id.y_tender_status", string='Service Level',tracking=True)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        values['y_lr_date'] = self.y_lr_date  
        values['y_lr_number'] = self.y_lr_number
        values['y_tender_status'] = self.y_tender_status     
        values['y_transportation_order_id'] = self.y_transportation_order_id.id if self.y_transportation_order_id else False
        return values

    def button_confirm(self):
        res = super().button_confirm()
        for rec in self:
            if rec.y_transportation_order_id:
                rec.y_transportation_order_id.write({'y_purchase_invoice_status':'waiting_for_bill'})

                for indent_lines in rec.y_transportation_order_id.y_transportation_order_intent_line_ids:
                    indent_lines.y_picking_id.y_transportation_order_id = rec.y_transportation_order_id.id
        return res

    def button_approve(self,force=False):
        res = super().button_approve(force)
        for rec in self:
            if rec.y_transportation_order_id:
                rec.y_transportation_order_id.write({'y_purchase_invoice_status':'waiting_for_bill'})

                for indent_lines in rec.y_transportation_order_id.y_transportation_order_intent_line_ids:
                    indent_lines.y_picking_id.y_transportation_order_id = rec.y_transportation_order_id.id

        return res

    def prepare_purchase_order(self,order):
        value = {
        'partner_id':order.mapped('y_fwd_agent').id,
        'origin': ",".join(order.mapped('y_name')),
        'y_transportation_order_id':order[0].id,
        'company_id':order.mapped('y_company_id').id,
        }
        return value

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def prepare_purchase_order_line(self,order,purchase):
        transportation_product_id = purchase.company_id.y_transportation_product_id
        if purchase.company_id.sudo().parent_id:
            transportation_product_id = purchase.company_id.sudo().parent_id.y_transportation_product_id
        if not transportation_product_id:
            raise UserError("Service Product not configured in Transportation Order Settings")
        
        value = {
            'product_id':transportation_product_id.id,
            'name':transportation_product_id.name,
            'product_qty':1,
            'price_unit':sum(order.y_transportation_costing_ids.mapped('y_cost')),
            'price_subtotal':sum(order.y_transportation_costing_ids.mapped('y_cost')),
            'order_id':purchase.id
            }
        return value
        
class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")

    def unlink(self):
        for rec in self:
            if rec.y_transportation_order_id:
                raise ValidationError(_("Landed Cost created from transportation order cannot be deleted"))
        return super().unlink()

class FreightViaCost(models.Model):
    _name = 'freight.via.cost'
    _description = "Freight Via Cost"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")

class FreightCostMasterDescription(models.Model):
    _name = 'freight.cost.master.description'
    _description = "Freight Cost Description"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")

class FreightCostMaster(models.Model):
    _name = 'freight.cost.master'
    _description = "Freight Cost Master"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'y_name'

    active = fields.Boolean(string="Active",default=True,tracking=True)
    y_name = fields.Char(string="Name",default=lambda self: _('New'), readonly=True)
    y_transporter_id = fields.Many2one('res.partner',string="Transporter",tracking=True)
    y_from_city_id = fields.Many2one('res.state.city',string="From",tracking=True)
    y_to_city_id = fields.Many2one('res.state.city',string="To",tracking=True)
    y_vehicle_category_id = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Category",tracking=True)
    y_rate_based = fields.Selection([('fixed_cost','Fixed Cost'),('by_weight','By Weight')],default="fixed_cost",string="Rate Based",tracking=True)
    y_cost_per = fields.Float(string="Cost Per",tracking=True)
    y_via = fields.Many2one('freight.via.cost',string="Via",tracking=True)
    y_fixed_cost = fields.Float(string="Fixed Cost",tracking=True)
    y_contract_cost_master_id = fields.Many2one('freight.cost.master.description',string="Freight Cost Description",tracking=True)
    y_company_id = fields.Many2one('res.company', default=lambda self: self.env.company,string="Company")

    y_start_date = fields.Date(string="Start Date",tracking=True)
    y_end_date = fields.Date(string="End Date",tracking=True)

    @api.constrains('y_transporter_id','y_from_city_id','y_to_city_id','y_vehicle_category_id')
    def _check_duplicate(self):
        for rec in self:              
            domain = [('y_transporter_id','=',rec.y_transporter_id.id),
                      ('y_from_city_id','=',rec.y_from_city_id.id),
                      ('y_to_city_id','=',rec.y_to_city_id.id),
                      ('y_vehicle_category_id','=',rec.y_vehicle_category_id.id)]
            existing_ids = self.env['freight.cost.master'].search(domain)
            if len(existing_ids) > 1:
                raise UserError (_("Oops, looks like we've got a duplicate record!"))

    @api.model
    def create(self, vals):
        if vals:
            company_id = self.env['res.company'].sudo().search([('id','=',vals.get('y_company_id'))])
            freight_cost_master_sequence_id = company_id.y_freight_cost_master_sequence_id
            if company_id.sudo().parent_id:
                freight_cost_master_sequence_id = company_id.sudo().parent_id.y_freight_cost_master_sequence_id
            if not freight_cost_master_sequence_id:
                raise UserError("Freight Cost Master Sequence not configured in Settings")
            vals['y_name'] = freight_cost_master_sequence_id.next_by_id() or _('New')

        return super(FreightCostMaster, self).create(vals)

    @api.constrains('y_from_city_id','y_to_city_id')
    def _check_from_to_city(self):
        for indent in self:
            if indent.y_from_city_id and indent.y_to_city_id:
                if indent.y_from_city_id == indent.y_to_city_id:
                    raise UserError("From and To city of selected indents must be same.")

    @api.constrains('y_start_date','y_end_date')
    def _check_dates(self):
        if self.y_end_date and self.y_start_date:
            if self.y_end_date < self.y_start_date:
                raise ValidationError(_("""End Date Date should not be less than Start Date"""))


class TransportationFreightCostMaster(models.Model):
    _name = 'transportation.freight.cost.master'
    _description = 'Transportation Freight Cost Master'

    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")
    y_contract_cost_master_id = fields.Many2one('freight.cost.master.description',string="Name")
    y_cost = fields.Float(string="Cost")
    y_is_cost_master_record = fields.Boolean(string="Is Cost Master Record")
    y_serial_no = fields.Integer(string="#",compute="_compute_import_sl")
    y_freight_cost_id = fields.Many2one('freight.cost.master',string="Freight Cost")
    y_non_contract_order_id = fields.Many2one('non.contract.order',string="Non Contract Order")
    y_currency_id = fields.Many2one('res.currency',string='Currency',tracking=True,related="y_transportation_order_id.y_company_id.currency_id")

    @api.depends('y_transportation_order_id','y_contract_cost_master_id')
    def _compute_import_sl(self):
        if self.y_transportation_order_id:
            for order in self.mapped('y_transportation_order_id'):
                number=1
                for line in order.y_transportation_costing_ids:
                    if line.y_contract_cost_master_id:
                        line.y_serial_no = number
                        number += 1
                    else:
                        line.y_serial_no = number
        else:
            self.y_serial_no = ''

    def unlink(self):
        for line in self:
            if line.y_transportation_order_id.y_state != 'draft' and line.y_is_cost_master_record:
                raise ValidationError("Once the transportation order is planned, you are unable to delete the line.")
        return super().unlink()



class TransportationOrder(models.Model):
    _name = "transportation.order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'y_name'
    _description = 'Transportation Order'

    y_name = fields.Char(string="Code" ,default=lambda self: _('New'), readonly=True)

    #Procressing tab fields
    y_shipment_type = fields.Selection(
        selection=TRANSPORT_ORDER_STATE_SELECTION,
        string="Shipment Type",
        copy=False,
        tracking=True,default='individual_shipment'
    )
    y_overall_status= fields.Selection(
        selection=OVERALLSTATUSSELECTION,
        string="Overall status",
        copy=False,
        default='planned',
        tracking=True)
    suitable_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_suitable_partner_ids',)
    y_fwd_agent = fields.Many2one('res.partner',string="Partner",domain="[('y_is_transporter', '!=',False)]")
    y_non_contract_transporter = fields.Char(string="Non Contract Transporter")
    y_shipping_type = fields.Selection(
        selection=SHIPPING_TYPE_STATE_SELECTION,
        string="Shipping Type",
        copy=False,
        tracking=True)
    y_planned_start_date = fields.Date(string="Planned Start Date")
    y_planned_end_date = fields.Date(string="Planned End Date")
    y_vehicle_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('cust_ven','Customer/Vendor')
    ], string='Vehicle Type',tracking=True,default='external')
    y_vehicle_number = fields.Char(string="Vehicle Number",copy=False)
    y_state = fields.Selection([
        ('draft', 'Draft'),
        ('planned','Planned'),
        ('running', 'In Transit'),
        ('posted', 'Completed'),
    ], string='State',default='draft',copy=False,tracking=True)
    y_approval_state = fields.Selection([
        ('request_for_approval', 'Request for Approval'),
        ('sent_for_approval','Sent for Approval'),
        ('approved', 'Approved'),
    ], string='Approval Status',default='request_for_approval',tracking=True,copy=False)

    y_total_weight = fields.Float(string="Weight",compute="_compute_indent_pickings_weight")
    y_fleet_id = fields.Many2one('fleet.vehicle',string="Vehicle",copy=False)
    y_vehicle_intent_ids = fields.Many2many('fleet.vehicle.intent',string="Vehicle Intents")
    y_lr_date = fields.Date(string="LR Date")
    y_lr_number = fields.Char(string="LR Number")

    y_transporter = fields.Char(string="Transporter")    
    y_tender_status = fields.Selection([
        ('withcontract', 'With Contract'),
        ('withoutcontract', 'With Out Contract'),
    ], string='Service Level',tracking=True)
    y_purchase_order_id = fields.Many2one('purchase.order',string="Purchase Order")
    y_driver_number = fields.Char(string="Driver Number")
    y_purchase_state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='PO Status', readonly=True, index=True, copy=False, tracking=True,related="y_purchase_order_id.state")
    
    
    y_actual_start_date = fields.Date(string="Actual Start Date")
    y_actual_end_date = fields.Date(string="Actual End Date")
    
    #Identification tab fields
    y_shipment_number = fields.Char(string="Shipment Number")
    y_description = fields.Char(string="Description")
    
    #Indent Lines
    y_transportation_order_intent_line_ids = fields.One2many('transportation.order.intent.line','y_transportation_order_id',string="Transportation Order indent Lines")

    y_transportation_po_ids = fields.One2many('purchase.order','y_transportation_order_id',string="Transportation Purchase Order Lines")

    y_from_city_id = fields.Many2one('res.state.city',string="Departure Point")
    y_to_city_id = fields.Many2one('res.state.city',string="Destination")

    from_gps_coordinates = fields.Char(string='GPS Coordinates',related="y_from_city_id.gps_coordinates")
    to_gps_coordinates = fields.Char(string='GPS Coordinates',related="y_to_city_id.gps_coordinates")

    latitude = fields.Float(string='Latitude',related="y_from_city_id.latitude")
    longitude = fields.Float(string='Longitude',related="y_from_city_id.longitude")

    y_company_id = fields.Many2one('res.company',string="Company")
    # map_html = fields.Html('Body', sanitize=False,compute='_compute_map_location')
    image_1920 = fields.Image("Image", compute='_compute_image_1920', inverse='_set_image_1920')
    avatar_128 = fields.Image("Image 128", compute='_compute_image_128')
    y_vehicle_category_id = fields.Many2one('fleet.vehicle.model.category', string="Vehicle Category",tracking=True)
    y_transportation_costing_ids = fields.One2many('transportation.freight.cost.master','y_transportation_order_id',string="Transportation Costing Lines")

    y_vehicle_weight_capacity = fields.Float(string="Vehcilce Payload Capacity",related='y_vehicle_category_id.weight_capacity')
    y_weight_uom_name = fields.Char(string='Weight unit of measure label', compute='_compute_weight_uom_name')    
    y_used_weight_percentage = fields.Float(string="Weight %", compute='_compute_capacity_percentage')
    y_non_contract_order_ids = fields.One2many('non.contract.order','y_transportation_order_id',string="Non Contract Order Lines")
    y_via = fields.Many2one('freight.via.cost',string="Via",tracking=True)

   
    y_purchase_invoice_status = fields.Selection([
        ('na','N/A'),
        ('pending_for_po', 'Pending for PO'),
        ('waiting_for_bill', 'Waiting for Bills'),
        ('fully_billed', 'Fully Billed'),
    ], string='Billing Status',default='na',copy=False)


    y_sale_order_ids = fields.Many2many('sale.order',string ='Sale Order',compute="fetch_sale_Order_customer",store=True)
    y_customer_ids = fields.Many2many('res.partner',string='Customer',compute="fetch_sale_Order_customer",store=True)


    @api.depends('y_transportation_order_intent_line_ids','y_transportation_order_intent_line_ids.y_picking_id')
    def fetch_sale_Order_customer(self):
        for rec in self:
            if rec.y_transportation_order_intent_line_ids:

                rec.y_sale_order_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:x.y_picking_id).mapped('y_picking_id').mapped('sale_id')
                rec.y_customer_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:x.y_picking_id).mapped('y_picking_id').mapped('partner_id')
            else:
                rec.y_sale_order_ids = False
                rec.y_customer_ids = False



    @api.onchange('y_fwd_agent')
    def _check_user_hase_non_contract_approval(self):
        for order in self:
            if order.y_tender_status == 'withoutcontract' and not order.env.user.has_group('fleet_module_18.group_for_approval_non_contract_order'):
                raise ValidationError("You don't have access to change the partner for a non-contract order.")

    def _compute_weight_uom_name(self):
        self.y_weight_uom_name = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()

    @api.depends('y_total_weight', 'y_vehicle_category_id.weight_capacity')
    def _compute_capacity_percentage(self):
        self.y_used_weight_percentage = False
        for order in self:
            if order.y_vehicle_weight_capacity:
                order.y_used_weight_percentage = 100 * (order.y_total_weight / order.y_vehicle_weight_capacity)

    def update_cost_element(self):
        for order in self:
            if order.y_from_city_id and order.y_to_city_id and order.y_vehicle_category_id and order.y_fwd_agent:
                domain = [('y_company_id','=',order.y_company_id.id),
                      ('y_transporter_id','=',order.y_fwd_agent.id),
                      ('y_from_city_id','=',order.y_from_city_id.id),
                      ('y_to_city_id','=',order.y_to_city_id.id),
                      ('y_vehicle_category_id','=',order.y_vehicle_category_id.id)]
                cost_element_id = self.env['freight.cost.master'].search(domain,limit=1)
                if cost_element_id.y_rate_based == 'fixed_cost':
                    amount = cost_element_id.y_fixed_cost
                else:
                    amount = cost_element_id.y_cost_per * order.y_total_weight
                if cost_element_id and cost_element_id not in order.y_transportation_costing_ids.mapped('y_freight_cost_id'):
                    order.write({'y_transportation_costing_ids':[(0,0,{'y_contract_cost_master_id':cost_element_id.y_contract_cost_master_id.id,
                                                                   'y_cost':amount,
                                                                   'y_freight_cost_id':cost_element_id.id,
                                                                   'y_is_cost_master_record':True})],
                                'y_via': cost_element_id.y_via.id,
                                })


    @api.constrains('create_date','y_planned_start_date','y_planned_end_date','y_actual_end_date','y_actual_start_date')
    def _check_planned_dates(self):
        if self.y_planned_start_date and self.create_date:
            if self.y_planned_start_date < self.create_date.date():
                raise ValidationError(_("""Planned Start Date should not be less than Create Date"""))

        if self.y_planned_end_date and self.y_planned_start_date:
            if self.y_planned_end_date < self.y_planned_start_date:
                raise ValidationError(_("""Planned End Date should not be less than Planned Start Date"""))

        # if self.y_actual_start_date and self.y_planned_end_date:
        #     if self.y_actual_start_date < self.y_planned_end_date:
        #         raise ValidationError(_("""Actual Start Date should not be less than Planned End Date"""))

        if self.y_actual_end_date and self.y_actual_start_date:
            if self.y_actual_end_date < self.y_actual_start_date:
                raise ValidationError(_("""Actual End Date should not be less than Actual Start Date"""))


    
    @api.constrains('y_from_city_id','y_to_city_id')
    def check_from_to_city(self):
        for line in self:
            if line.y_from_city_id == line.y_to_city_id:
                raise UserError(_("From and TO should be different"))
                
    @api.depends('y_transportation_order_intent_line_ids.y_indent_weight')
    def _compute_indent_pickings_weight(self):
        for order in self:
            order.y_total_weight = sum(order.y_transportation_order_intent_line_ids.mapped('y_indent_weight'))

    def _compute_image_1920(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image_1920 = record.y_fwd_agent.image_1920

    def _set_image_1920(self):
        pass

    def _compute_image_128(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.avatar_128 = record.y_fwd_agent.avatar_128

    @api.onchange('y_lr_date','y_lr_number')
    def onchange_lr_date_lr_number(self):
        for rec in self:
            for indent_line in rec.y_transportation_order_intent_line_ids:
                indent_line.write({'y_lr_number':rec.y_lr_number})

            for indent_line in rec.y_transportation_order_intent_line_ids:
                indent_line.y_picking_id.write({'y_lr_date':rec.y_lr_date})
                indent_line.y_picking_id.write({'y_lr_number':rec.y_lr_number})

    def get_picking(self):
        if self.y_state != 'draft':
            raise ValidationError("You can add pickings only in draft state.")
        tree_view = self.env.ref('fleet_module_18.view_stock_picking_trasnaportation_order_tree')
        domain = [('picking_type_code', 'in', ('incoming','outgoing'))]
        domain = [('picking_type_code', 'in', ('incoming','outgoing','internal')),('state','in',('assigned','confirmed')),('company_id','=',self.y_company_id.id),('id','not in',self.y_transportation_order_intent_line_ids.y_picking_id.ids)]
        return {
            'name': 'Pickings',
            'view_mode': 'list',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'views': [(tree_view.id, 'list')],
            'context':{'record_id':self.id,'create': False}
        }

    def get_vehicle_indent(self):
        if self.y_state != 'draft':
            raise ValidationError("You can add Vehical Indent only in draft state.")
        tree_view = self.env.ref('fleet_module_18.view_fleet_vehicle_intent_transportation_order_tree')
        domain = [('y_status', '=', 'released'),('y_transportation_order_id','=',False),('y_company_id','=',self.y_company_id.id)]
        return {
            'name': 'Vehicle Intent',
            'view_mode': 'list',
            'res_model': 'fleet.vehicle.intent',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
            'views': [(tree_view.id, 'list')],
            'context':{'record_id':self.id,'create': False}
        }

    #y_transportation_order_id
    def create_purchase_order(self):
        check_state = self.filtered(lambda x:x.y_state == 'draft')
        if check_state:
            raise UserError("Creating a purchase order or transportation order in draft state is not feasible.")
        partner_ids = self.filtered(lambda x: not x.y_fwd_agent)
        if partner_ids:
            raise UserError(_("Partner required to create purchase order."))

        ay_fwd_agent_ids = set([order.y_fwd_agent for order in self])
        if len(ay_fwd_agent_ids) > 1:
            raise UserError(_('You can only create purchase order of identical partner.'))

        company_id_ids = set([order.y_company_id for order in self])
        if len(company_id_ids) > 1:
            raise UserError(_('You can only create purchase order of identical company.'))

        non_external_orders = self.filtered(lambda x:x.y_vehicle_type != 'external')
        if non_external_orders:
            raise UserError(_("The service PO is only applicable for external vehicle types."))

        purchase_transportation_orders = self.y_purchase_order_id.filtered(lambda x:x.state not in ('cancel','reject'))
        if purchase_transportation_orders:
            raise UserError(_("Purchase Order already created for this transportation order."))

        purchase_order_obj = self.env['purchase.order']
        purchase_order_vals = purchase_order_obj.prepare_purchase_order(self)
        purchase_obj = purchase_order_obj.create(purchase_order_vals)
        self.write({'y_purchase_order_id':purchase_obj.id})                    
        for rec in self:
            purchase_order_line_obj = self.env['purchase.order.line']
            purchase_order_line_vals = purchase_order_line_obj.prepare_purchase_order_line(rec,purchase_obj)
            purchase_line_obj = purchase_order_line_obj.create(purchase_order_line_vals)

            #flow Transportation order to intent picking(PO)
            for indent_lines in rec.y_transportation_order_intent_line_ids:
                if indent_lines.y_picking_id.purchase_id:
                    indent_lines.y_picking_id.purchase_id.write({'y_transportation_order_id':rec.id})
                elif indent_lines.y_picking_id.sale_id:
                    indent_lines.y_picking_id.sale_id.write({'y_transportation_order_id':rec.id})


    def view_landed_cost(self):
        for rec in self:
            tree_view = self.env.ref('stock_landed_costs.view_stock_landed_cost_tree')
            view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form')
            return {
                'name': _('Landed Cost'),
                'view_type': 'form',
                'view_mode': 'list, form',
                'res_model': 'stock.landed.cost',
                'domain': [('y_transportation_order_id','=',rec.id)],
                'view_id': view_id.id,
                'views': [(tree_view.id, 'list'),(view_id.id, 'form')],
                'type': 'ir.actions.act_window',
                }

    def view_purchase_order(self):
        for rec in self:
            tree_view = self.env.ref('purchase.purchase_order_kpis_tree')
            view_id = self.env.ref('purchase.purchase_order_form')
            return {
                'name': _('Purchase Order'),
                'view_type': 'form',
                'view_mode': 'list, form',
                'res_model': 'purchase.order',
                'domain': [('id','=',rec.y_purchase_order_id.id)],
                'view_id': view_id.id,
                'views': [(tree_view.id, 'list'),(view_id.id, 'form')],
                'type': 'ir.actions.act_window',
                }

    def view_non_contract_order(self):
        for rec in self:
            tree_view = self.env.ref('fleet_module_18.view_non_contract_order_tree')
            form_view_id = self.env.ref('fleet_module_18.view_fleet_non_contract_order_form')
            return {
                'name': _('Non Contract Order'),
                'view_type': 'tree',
                'view_mode': 'list,form',
                'res_model': 'non.contract.order',
                'domain': [('y_transportation_order_id','=',rec.id)],
                'views': [(tree_view.id, 'list'),(form_view_id.id,'form')],
                'type': 'ir.actions.act_window',
                'context':{'default_y_transportation_order_id':rec.id,
                           'default_y_from_city_id':rec.y_from_city_id.id,
                           'default_y_to_city_id':rec.y_to_city_id.id,
                           }
                }

    def request_approval(self):
        for rec in self:
            non_lr_number_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:not x.y_lr_number)
            if non_lr_number_ids:
                raise UserError("In order to process LR Number should be required")

            if rec.y_approval_state == 'request_for_approval':
                rec.write({'y_approval_state':'sent_for_approval'})  
                
    def action_send_approval(self):
        for rec in self:
            if rec.y_vehicle_type == 'external' and rec.y_tender_status == 'withoutcontract':
                if not rec.y_non_contract_order_ids.filtered(lambda x:x.y_approval_state == 'approve'):
                    raise UserError("Non contract order approval not done.")
            if rec.y_vehicle_type == 'external' and rec.y_tender_status == 'withcontract':
                if not rec.y_transportation_costing_ids.filtered(lambda x:x.y_is_cost_master_record):
                    raise UserError("Contract not available to approve.")

            if rec.y_fleet_id or rec.y_vehicle_number:
                if rec.y_approval_state == 'sent_for_approval':
                    approver_ids = rec.y_company_id.y_transportation_order_approver_ids

                    if rec.y_company_id.sudo().parent_id:
                        approver_ids += rec.y_company_id.sudo().parent_id.y_transportation_order_approver_ids
                    if not approver_ids:
                        raise UserError("Approval not configured in Settings")
                    user = self.env.uid
                    if user in approver_ids.ids:
                        rec.write({'y_approval_state':'approved','y_state':'planned'})
                        
                        if rec.y_vehicle_type == 'external':
                            rec.write({'y_purchase_invoice_status':'pending_for_po'})
                        else:
                            rec.write({'y_purchase_invoice_status':'na'})

                        if not rec.y_planned_start_date:
                            rec.write({'y_planned_start_date':fields.Date.today()})

                        for indent_line in rec.y_transportation_order_intent_line_ids:
                            indent_line.y_picking_id.write({'y_lr_date':rec.y_lr_date,
                                                            'y_lr_number':rec.y_lr_number,
                                                            'y_transportation_order_id':rec.id,
                                                            'carrier_tracking_ref':rec.y_name,
                                                            'y_driver_number':rec.y_driver_number,
                                                            'y_overall_status':'planning_completed',
                                                            'y_lr_number':indent_line.y_lr_number,
                                                            'y_vehicle_intent_number':indent_line.y_fleet_indent_id.y_name,
                                                            'y_vehicle_type': rec.y_vehicle_type,
                                                            })
                    else:
                        raise UserError(_("You can't approve"))
            else:
                raise UserError("Vehicle Details Not Available.")

    def action_shipment_start(self):
        for order in self:
            if 'assigned' in order.y_transportation_order_intent_line_ids.mapped('y_picking_id').filtered(lambda x:x.sale_id).mapped('state'):
                raise ValidationError(_("Picking is in ready state"))
            order.write({'y_state':'running'})
            if not order.y_planned_end_date:
                order.write({'y_planned_end_date':fields.Date.today()})

            if not order.y_actual_start_date:
                order.write({'y_actual_start_date':fields.Date.today()})

            for indent_line in order.y_transportation_order_intent_line_ids:
                indent_line.y_picking_id.write({'y_lr_date':order.y_lr_date,
                                                'y_lr_number':order.y_lr_number,
                                                'y_transportation_order_id':order.id,
                                                'y_vehicle_number':order.y_vehicle_number,

                                                'carrier_tracking_ref':order.y_name,
                                                'y_overall_status':'shipment_start',
                                                'y_lr_number':indent_line.y_lr_number,
                                                'y_vehicle_intent_number':indent_line.y_fleet_indent_id.y_name,
                                                'y_vehicle_type': order.y_vehicle_type,
                                                })

    def check_pod_document(self):
        for rec in self:
            non_pod_document_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:not x.y_pod_document)
            if non_pod_document_ids:
                raise UserError("POD Document Not Available in Indent Lines")

    def action_process(self):
        for rec in self:
            if rec.y_state == 'running':
                if not rec.y_actual_end_date:
                    rec.write({'y_actual_end_date':fields.Date.today()})

                self.check_pod_document()
                
                pending_picking_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:x.y_picking_state != 'done')
                if pending_picking_ids:
                    raise UserError("In order to process Pickings should be in done state")

                non_lr_number_ids = rec.y_transportation_order_intent_line_ids.filtered(lambda x:not x.y_lr_number)
                if non_lr_number_ids:
                    raise UserError("In order to process LR Number should be required")

                rec.write({'y_state':'posted'})
                transportation_product_id = rec.y_company_id.y_transportation_product_id
                if rec.y_company_id.sudo().parent_id:
                    transportation_product_id = rec.y_company_id.sudo().parent_id.y_transportation_product_id
                if not transportation_product_id:
                    raise UserError("Service Product not configured in Transportation Order Settings")
                
                for indent_line in rec.y_transportation_order_intent_line_ids:
                    indent_line.y_picking_id.write({'y_lr_date':rec.y_lr_date,
                                                    'y_lr_number':rec.y_lr_number,
                                                    'y_transportation_order_id':rec.id,
                                                    'carrier_tracking_ref':rec.y_name,
                                                    'y_vehicle_number':rec.y_vehicle_number,

                                                    'y_overall_status':'shipment_end',
                                                    'y_lr_number':indent_line.y_lr_number,
                                                    'y_vehicle_intent_number':indent_line.y_fleet_indent_id.y_name,
                                                    'y_vehicle_type': rec.y_vehicle_type,
                                                    })

    @api.model
    def create(self, vals):
        if vals:
            company_id = self.env['res.company'].sudo().search([('id','=',vals.get('y_company_id'))])
            transportation_order_sequence_id = company_id.y_transportation_order_sequence_id
            if company_id.sudo().parent_id:
                transportation_order_sequence_id = company_id.sudo().parent_id.y_transportation_order_sequence_id
            if not transportation_order_sequence_id:
                raise UserError("Transporation Order Sequence not configured in Settings")
            vals['y_name'] = transportation_order_sequence_id.next_by_id() or _('New')
        return super(TransportationOrder, self).create(vals)
        
    def action_planning_time(self):
        for rec in self:
            rec.y_execution_planning_time= datetime.now()
            rec.y_overall_status = 'planning_completed'
            rec.y_state = 'planned'

    def action_checkin(self):
        for rec in self:
            rec.y_execution_checkin_time= datetime.now()
            rec.y_overall_status = 'checkin'

    def action_loading_start(self):
        for rec in self:
            rec.y_execution_loading_start_time= datetime.now()
            rec.y_overall_status = 'loading_start'

    def action_loading_end(self):
        for rec in self:
            rec.y_execution_loading_end_time= datetime.now()
            rec.y_overall_status = 'loading_end'

    def action_execution_shipment_completion_time(self):
        for rec in self:
            rec.y_execution_shipment_completion_time= datetime.now()
            rec.y_overall_status = 'shipment_completion'

    def action_shipment_start_time(self):
        for rec in self:
            rec.y_shipment_start_time= datetime.now()
            rec.y_overall_status = 'shipment_start'
            rec.write({'y_state':'running'})
            for indent_lines in rec.y_transportation_order_intent_line_ids:
                indent_lines.y_picking_id.write({'carrier_tracking_ref':indent_lines.y_transportation_order_id.y_name,'y_vehicle_intent_number':indent_lines.y_fleet_indent_id.y_name,'y_transportation_order_id':rec.id})

    def action_shipment_end_time(self):
        for rec in self:
            rec.y_shipment_end_time= datetime.now()
            rec.y_overall_status = 'shipment_end'

class NonContractOrders(models.Model):
    _name = "non.contract.order"
    _description = "Non Contract Order"
    _rec_name = 'y_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    y_name = fields.Char(string="CODE",default=lambda self: self.env['ir.sequence'].next_by_code('non.contract.order') or _('NEW'))
    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")
    y_from_city_id = fields.Many2one('res.state.city',string="Departure Point")
    y_to_city_id = fields.Many2one('res.state.city',string="Destination")
    y_contract_cost_master_id = fields.Many2one('freight.cost.master.description',string="Freight Cost Description",tracking=True)
    y_rate_based = fields.Selection([('fixed_cost','Fixed Cost'),('by_weight','By Weight')],default="fixed_cost",string="Rate Based",tracking=True)
    y_rate_by_unit = fields.Float(string="Rate by Unit",tracking=True)
    y_base_cost = fields.Float(string="Base Cost",tracking=True)
    y_travel_document = fields.Binary(string="Attachement" ,copy=False)
    y_attachment_filename = fields.Char(string="POD Document Name")
    y_uom_id = fields.Many2one('uom.uom',string="UOM")
    y_distance = fields.Float(string="Distance",compute="calculate_total_distance",inverse="inverse_total_distance")
    y_duration = fields.Float(string="Total Duration")
    
    y_stage_forward_agent_id = fields.Many2one('res.partner',string="Transporter",tracking=True,domain="[('y_is_transporter', '!=',False)]")
    y_approval_state = fields.Selection([
        ('pending', 'Pending'),
        ('approve', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status',default='pending',tracking=True,copy=False)
    y_is_existing_transporter = fields.Boolean(default=True,string="Is Existing Transporter")
    y_transporter = fields.Char(string="Transporter")
    y_concat_transporter = fields.Char(compute='_compute_concat_transporter',string="Transporter")
    


    y_toll_charge = fields.Float(string="Toll Charge")
    y_labour_charge = fields.Float(string="Labour Charge")
    y_broker_charge = fields.Float(string="Broker Charge")
    y_other_charge = fields.Float(string="Other Charge")
    y_taxes_ids = fields.Many2many('account.tax',string="Taxes")
    y_additional_cost = fields.Float(string="Additional Cost",compute="calculate_total_additional_cost")
    y_net_total = fields.Float(string="Net Total",compute="calculate_net_total")
    y_total_net_total = fields.Float(string="Total Net Total",compute="calculate_total_net_amount")

    @api.depends('y_is_existing_transporter','y_transporter')
    def _compute_concat_transporter(self):
        for line in self:
            if line.y_is_existing_transporter:
                line.y_concat_transporter = line.y_stage_forward_agent_id.name
            else:
                line.y_concat_transporter = line.y_transporter



    @api.constrains('y_stage_forward_agent_id','y_from_city_id','y_to_city_id')
    def _check_duplicate(self):
        for rec in self:         
            domain = [('y_from_city_id','=',rec.y_from_city_id.id),
                      ('y_to_city_id','=',rec.y_to_city_id.id),
                      ('y_transportation_order_id','=',rec.y_transportation_order_id.id),
                      ('y_is_existing_transporter','=',rec.y_is_existing_transporter),
                      ]
            if rec.y_is_existing_transporter:
                domain += [('y_stage_forward_agent_id','=',rec.y_stage_forward_agent_id.id)]
            else:
                domain += [('y_transporter','=',rec.y_transporter)]
            
            existing_ids = self.env['non.contract.order'].search(domain)
            if len(existing_ids) > 1:
                raise UserError (_("Oops, looks like we've got a duplicate record!"))



    @api.onchange('y_rate_based')
    def _onchange_rate_based(self):
        for line in self:
            if line.y_rate_based == 'fixed_cost':
                line.y_rate_by_unit = 0
            else:
                line.y_base_cost = 0

    @api.constrains('y_from_city_id','y_to_city_id')
    def check_from_to_city(self):
        for line in self:
            if line.y_from_city_id == line.y_to_city_id:
                raise UserError(_("From and TO should be different"))

    def inverse_total_distance(self):
        for rec in self:
            rec.y_distance = rec.y_distance

    @api.depends('y_from_city_id','y_to_city_id')
    def calculate_total_distance(self):
        for rec in self:
            if rec.y_from_city_id and rec.y_to_city_id:
                lat_long_city1 = (rec.y_from_city_id.latitude ,rec.y_from_city_id.longitude)
                lat_long_city2 = (rec.y_to_city_id.latitude ,rec.y_to_city_id.longitude)
                rec.y_distance = GD(lat_long_city1 , lat_long_city2).km
            else:
                rec.y_distance = 0

    @api.depends('y_rate_by_unit','y_distance')
    def get_base_cost(self):
        for rec in self:
            if rec.y_rate_by_unit and rec.y_distance:
                rec.y_base_cost = rec.y_rate_by_unit * rec.y_distance
            else:
                rec.y_base_cost = 0.0

    def approve_non_contract_order(self):
        for rec in self:
            if rec.y_transportation_order_id.y_state != 'draft':
                raise ValidationError("Once the transportation order is planned, you can not approve the order.")

            approved_contract_order_ids = rec.y_transportation_order_id.y_non_contract_order_ids.filtered(lambda x:x.y_approval_state == 'approve')
            if approved_contract_order_ids:
                raise UserError("Non contract order already approved.")
            if self.env.user.has_group('fleet_module_18.group_for_approval_non_contract_order'):
                rec.write({'y_approval_state':'approve'})
                if rec.y_rate_based == 'fixed_cost':
                    amount = rec.y_base_cost
                else:
                    amount = rec.y_rate_by_unit * rec.y_transportation_order_id.y_total_weight

                rec.y_transportation_order_id.write({'y_transportation_costing_ids':[(0,0,{'y_contract_cost_master_id':rec.y_contract_cost_master_id.id,
                                                                   'y_cost':amount,
                                                                   'y_non_contract_order_id':rec.id,
                                                                   'y_is_cost_master_record':True})],
                                                    })
                if not rec.y_is_existing_transporter:
                    rec.y_transportation_order_id.write({'y_non_contract_transporter':rec.y_transporter,
                                                        'y_fwd_agent':False})
                else:
                    rec.y_transportation_order_id.write({'y_fwd_agent':rec.y_stage_forward_agent_id.id})



            else:
                raise UserError(_("You can't approve"))
            
    def reject_non_contract_order(self):
        for rec in self:
            if self.env.user.has_group('fleet_module_18.group_for_approval_non_contract_order'):
                rec.write({'y_approval_state':'rejected'})
            else:
                raise UserError(_("You can't reject"))

    def revoke_non_contract_order(self):
        for rec in self:
            if rec.y_transportation_order_id.y_state != 'draft':
                raise UserError("Once a transportation order is planned, it cannot be revoked.")
            if rec.env.user.has_group('fleet_module_18.group_for_approval_non_contract_order'):
                non_contract_order_id = rec.y_transportation_order_id.y_transportation_costing_ids.filtered(lambda x:x.y_non_contract_order_id == rec)
                non_contract_order_id.unlink()
                rec.write({'y_approval_state':'pending'})
                rec.y_transportation_order_id.write({'y_non_contract_transporter':False,'y_fwd_agent':False})
            else:
                raise UserError(_("You can't revoke"))

    def unlink(self):
        for line in self:
            if line.y_approval_state == 'approve':
                raise UserError("Once the contract is approved, it should not be deleted.")
        return super().unlink()

class TransportatioOrderIndentLines(models.Model):
    _name = 'transportation.order.intent.line'
    _description = "Transportation Order Indent Line"

    y_transportation_order_id = fields.Many2one('transportation.order',string="Transportation Order")
    y_fleet_indent_id = fields.Many2one('fleet.vehicle.intent',string="Indent")
    y_picking_id = fields.Many2one('stock.picking',string="Picking")
    from_city = fields.Char(string="From")
    to_city = fields.Char(string="To")
    y_scheduled_date = fields.Datetime(string="Scheduled Date",related="y_picking_id.scheduled_date")
    y_lr_number = fields.Char(string="LR Number")
    y_indent_line_id = fields.Many2one('fleet.vehicle.intent.line',string="Indent Line")
    y_weight = fields.Float(string="Weight")
    y_pod_document = fields.Binary(string="POD" ,copy=False)
    y_attachment_filename = fields.Char(string="POD Document Name")
    y_attachment_date = fields.Date(string="POD Date")
    y_picking_state = fields.Selection(related="y_picking_id.state")
    y_source_document = fields.Char(related="y_picking_id.origin")
    y_partner_id = fields.Many2one('res.partner',related="y_picking_id.partner_id")
    y_indent_weight = fields.Float(string="Weight",compute="_compute_indent_weight")
    y_other_weight = fields.Float(string="Other Weight")

    @api.depends('y_fleet_indent_id')
    def _compute_indent_weight(self):
        for line in self:
            line.y_indent_weight = line.y_fleet_indent_id.estimated_shipping_weight + line.y_other_weight
    

    @api.onchange('y_picking_id')
    def onchange_y_picking_id(self):
        for rec in self:
            if rec.y_picking_id:
                rec.write({'from_city':rec.y_picking_id.partner_id.city,'to_city':rec.y_picking_id.location_dest_id.warehouse_id.partner_id.city})

    def unlink(self):
        for line in self:
            if line.y_transportation_order_id.y_state != 'draft':
                raise ValidationError("Once the transportation order is planned, you are unable to delete the line.")
        return super().unlink()
