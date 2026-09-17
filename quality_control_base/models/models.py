from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from collections import defaultdict

class QualityTitleWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    y_quality_point_id = fields.Many2one(string="Quantity Point", related="current_quality_check_id.point_id")
    y_quality_point_title = fields.Char(string="Quality Check", related='y_quality_point_id.title')
    y_quality_point_norm = fields.Float(string="Norm", related='y_quality_point_id.norm')
    y_quality_point_tolerance_max = fields.Float(string="Tolerance Max", related='y_quality_point_id.tolerance_max')
    y_quality_point_tolerance_min = fields.Float(string="Tolerance Min", related='y_quality_point_id.tolerance_min')


# Inspection Plan
class InspectionPlan(models.Model):
    _name = "inspection.plan"
    _inherit = ['mail.thread']
    _description = "Inspection Plan"
    _rec_name = "y_name"

    _sql_constraints = [('product_inspection_plan_uniq', 'unique(y_product_tmpl_id, y_picking_type_id, y_company_id)',
                         'Inspection Plan for this Operation type and Product already exist.')]

    y_name = fields.Char(tracking=True,string="Name")
    y_team_id = fields.Many2one('quality.alert.team', 'Team', tracking=True)
    y_product_tmpl_id = fields.Many2one('product.template',domain="[('type', 'in', ['consu', 'product']), '|', ('company_id', '=', False), ('company_id', '=', y_company_id)]", tracking=True ,string="Product")
    y_product_id = fields.Many2one('product.product', domain="[('product_tmpl_id', '=', y_product_tmpl_id)]", tracking=True,string="Product Varient")
    y_picking_type_id = fields.Many2one('stock.picking.type',string="Operation Type", tracking=True)
    y_quality_point_ids = fields.One2many('quality.point', 'y_inspection_plan_id',string="Quality Point Lines")
    y_company_id = fields.Many2one('res.company', string='Company', index=True,default=lambda self: self.env.company, tracking=True)
    y_product_category_ids = fields.Many2many('product.category', string="Product Categories")
    y_operation_id = fields.Many2one('mrp.routing.workcenter', string="Work Order Operation", tracking=True)
    y_is_workorder_step = fields.Boolean(defualt=False,copy=False,string="Workorder Step")
    y_start_date = fields.Date(tracking=True,string="Start Date")
    y_end_date = fields.Date(tracking=True,string="End Date")

    @api.onchange('y_product_tmpl_id','y_picking_type_id')
    def _onchange_product_tmpl_id(self):
        for plan in self:
            plan.y_product_id = plan.y_product_tmpl_id.product_variant_id.id if plan.y_product_tmpl_id else plan.y_product_id.id
            plan.y_product_category_ids = [(6,0,plan.y_product_tmpl_id.categ_id.mapped('id'))] if plan.y_product_tmpl_id else False
            for point in plan.y_quality_point_ids:
                point.picking_type_ids = [(6,0,plan.y_picking_type_id.ids)] if plan.y_picking_type_id else False
            
    @api.onchange('y_product_id')
    def _onchange_product_id(self):
        for plan in self:
            plan.y_product_tmpl_id = plan.y_product_id.product_tmpl_id.id if plan.y_product_id else plan.y_product_tmpl_id.id
            
    def add_items(self):
        domain = [('company_id', '=',self.y_company_id.id),('product_ids', '=', self.y_product_tmpl_id.product_variant_id.id),('picking_type_ids', 'in', self.y_picking_type_id.id),('team_id', '=', self.y_team_id.id), ('inspection_plan_id', '=', False)]
        return {
            'name': 'Quality Points',
            'view_mode': 'list',
            'res_model': 'quality.point',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'plan_id': self.id},
            'domain': domain,
        }

    @api.onchange('y_picking_type_id')
    def picking_type_ids_onchange(self):
        for rec in self:
            rec.y_is_workorder_step = True if rec.y_picking_type_id.code == 'mrp_operation' else False

    @api.model
    def create(self, vals):
        sequence = self.env['stock.picking.type'].browse(vals.get('y_picking_type_id')).y_sequence_for_inspection_plan
        if sequence:
            vals['y_name'] = sequence.next_by_id()
        else:
            raise UserError(_("Please Enter The sequence for this operation Type"))
        return super(InspectionPlan, self).create(vals)

    @api.constrains('y_start_date', 'y_end_date')
    def _check_quantities(self):
        for rec in self:
            if rec.y_end_date and rec.y_start_date and rec.y_end_date < rec.y_start_date:
                raise ValidationError(_("""End Date Can not be less than Start Date"""))


# Quality Point
class QualityPoint(models.Model):
    _inherit = "quality.point"

    y_inspection_plan_id = fields.Many2one('inspection.plan', ondelete='cascade',string="Inspection Plan",domain="['|', ('y_company_id', '=', False), ('y_company_id', '=', company_id)]")
    y_product_tmpl_id = fields.Many2one('product.template',string="Product", required=False, check_company=True,
        domain="[('type', 'in', ['consu', 'product']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        compute='_compute_details', store=True, readonly=False)
    y_code = fields.Char(compute="_compute_details", store=True,string="Code")
    y_is_readonly = fields.Boolean(default=False,copy=False,compute="_compute_readonly",string="Is Readonly")
    y_test_method_id = fields.Many2one('quality.test.method',string="Test Method")
    y_characteristic_id = fields.Many2one('quality.characteristic',string="Characteristic")

    # @api.onchange('product_ids')
    # def _onchange_product_id(self):
    #     for point in self:
    #         point.product_category_ids = [(6,0,point.product_ids.categ_id.mapped('id'))] if point.product_ids else False

    @api.onchange('y_product_tmpl_id')
    def _onchange_y_product_tmpl_id(self):
        for point in self:
            if point.y_product_tmpl_id:
                point.product_ids = [(6,0,point.y_product_tmpl_id.product_variant_id.ids)]
                # point.product_category_ids = [(6,0,point.product_ids.categ_id.mapped('id'))]
                
    def add_items(self):
        domain = [('company_id','=',self.company_id.id),('product_tmpl_id', '=', self.y_inspection_plan_id.y_product_tmpl_id.id),('picking_type_ids', 'in', self.y_inspection_plan_id.y_picking_type_id.id), ('team_id', '=', self.y_inspection_plan_id.y_team_id.id)]
        return {
            'name': 'Quality Points',
            'view_mode': 'list',
            'res_model': 'quality.point',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': domain,
        }

    def select_button(self):
        for rec in self:
            inspect = rec.env['inspection.plan'].browse(rec._context.get('plan_id'))
            if inspect:
                rec.write({'y_inspection_plan_id': inspect.id})

    @api.depends('product_ids','y_product_tmpl_id','product_category_ids','y_inspection_plan_id')
    def _compute_readonly(self):
        for rec in self:
            rec.y_is_readonly = True if rec.y_inspection_plan_id and rec.product_ids and rec.y_product_tmpl_id and rec.product_category_ids else False

    @api.depends('y_product_tmpl_id','y_inspection_plan_id', 'y_inspection_plan_id.y_product_tmpl_id', 'y_inspection_plan_id.y_team_id')
    def _compute_details(self):
        for rec in self:
            if rec.y_inspection_plan_id:
                if not rec.y_inspection_plan_id.y_product_id:
                    prod_id = self.env[('product.product')].search([('product_tmpl_id', '=', rec.y_inspection_plan_id.y_product_tmpl_id.id)])
                else:
                    prod_id = rec.y_inspection_plan_id.y_product_id
                rec.product_ids = [(6,0,prod_id.ids)]
                rec.y_product_tmpl_id = rec.y_inspection_plan_id.y_product_tmpl_id.id
                rec.picking_type_ids = rec.y_inspection_plan_id.y_picking_type_id
                rec.product_category_ids = rec.y_inspection_plan_id.y_product_category_ids.ids
                rec.team_id = rec.y_inspection_plan_id.y_team_id.id
                rec.company_id = rec.y_inspection_plan_id.y_company_id.id
                rec.y_code = ",".join(rec.picking_type_ids.mapped('code'))
            else:
                rec.y_product_tmpl_id = rec.y_code = False

    @api.onchange('y_characteristic_id')
    def _set_title(self):
        self.title = self.y_characteristic_id.y_description

    def _prepare_quality_inspection_plan_values(self,point_ids):
        return {'y_company_id':point_ids[0].company_id.id,
                'y_team_id':point_ids[0].team_id.id,
                'y_picking_type_id':point_ids[0].picking_type_ids.id,
                'y_product_tmpl_id':point_ids[0].product_ids.product_tmpl_id.id,
                'y_product_id':point_ids[0].product_ids.id,
                'y_product_category_ids':[(6,0,point_ids[0].product_category_ids.ids)],
               }

    def action_generate_inspection_plan(self):
        filtered_points = self.filtered(lambda x:not x.inspection_plan_id)
        measure_on_operation_ids = filtered_points.filtered(lambda x:x.measure_on == 'operation')
        measure_on_product_ids = filtered_points.filtered(lambda x:x.measure_on == 'product')
        operation_ids = set([point.picking_type_ids for point in measure_on_operation_ids])
        product_ids = set([(point.product_ids,point.product_category_ids) for point in measure_on_product_ids])
        for product,pro_cat in product_ids:
            product_point_ids = filtered_points.filtered(lambda x:x.measure_on == 'product' and x.product_ids == product and x.product_category_ids == pro_cat)
            if product_point_ids:
                company_ids = set([point.company_id for point in product_point_ids])
                if len(company_ids) > 1:
                    raise UserError('You can only create inspection plan with same company.')

                team_ids = set([point.team_id for point in product_point_ids])
                if len(team_ids) > 1:
                    raise UserError('You can only create inspection plan with same team.')

                picking_type_ids = set([point.picking_type_ids for point in product_point_ids])
                if len(picking_type_ids) > 1:
                    raise UserError('You can only create inspection plan with same operation type.')
                product_point_ids.write({'y_inspection_plan_id':False,'y_product_tmpl_id':False})
                values = self._prepare_quality_inspection_plan_values(product_point_ids)
                inspection_plan = self.env['inspection.plan'].create(values)
                product_point_ids.write({'y_inspection_plan_id':inspection_plan.id})

        for operation in operation_ids:
            operation_point_ids = filtered_points.filtered(lambda x:x.measure_on == 'operation' and x.picking_type_ids == operation)
            if operation_point_ids:
                company_ids = set([point.company_id for point in operation_point_ids])
                if len(company_ids) > 1:
                    raise UserError('You can only create inspection plan with same company.')

                team_ids = set([point.team_id for point in operation_point_ids])
                if len(team_ids) > 1:
                    raise UserError('You can only create inspection plan with same team.')

                picking_type_ids = set([point.picking_type_ids for point in operation_point_ids])
                if len(picking_type_ids) > 1:
                    raise UserError('You can only create inspection plan with same operation type.')
                operation_point_ids.write({'y_inspection_plan_id':False,'y_product_tmpl_id':False})
                values = self._prepare_quality_inspection_plan_values(operation_point_ids)
                inspection_plan = self.env['inspection.plan'].create(values)
                operation_point_ids.write({'y_inspection_plan_id':inspection_plan.id})
                
# Inspection Sheet
class InspectionSheet(models.Model):
    _name = "inspection.sheet"
    _inherit = ['mail.thread']
    _description = "Inspection Sheet"
    _rec_name = 'y_name'

    y_name = fields.Char(string="Name")
    y_source = fields.Char(compute='_get_source', store=True,tracking=True,string="Source")
    y_partner_id = fields.Many2one('res.partner', string="Partner", compute='_get_source', store=True,tracking=True)
    y_product_id = fields.Many2one('product.product', domain="[('id', 'in', y_available_product_ids)]",tracking=True,string="Product")
    y_picking_id = fields.Many2one('stock.picking',tracking=True,string="Picking")
    y_production_id = fields.Many2one('mrp.production',string="Production")
    y_lot_id = fields.Many2one('stock.lot',tracking=True,string="Lot")
    y_team_id = fields.Many2one('quality.alert.team',tracking=True,string="Team")
    y_company_id = fields.Many2one('res.company',tracking=True,string="Company")
    y_quality_check_ids = fields.One2many('quality.check','y_inspection_sheet_id',string="Checks")
    y_date = fields.Date(default=fields.Date.today(),string="Date")
    y_quantity_recieved = fields.Float(string="Quantity Received")
    y_quantity_accepted = fields.Float(string="Quantity Accepeted")
    y_quantity_rejected = fields.Float(string="Quantity Rejected")
    y_quantity_pending = fields.Float(string="Quantity Pending")
    y_quantity_destructive = fields.Float(string="Quantity Destructive")
    y_under_deviation = fields.Float(string="Quantity Deviation")
    y_quality_inspector_ids = fields.Many2many('hr.employee', string='Quality Inspector', domain="[('id','in',y_quality_inspector_id)]")
    y_quality_inspector_id = fields.Many2many(related="y_team_id.y_quality_inspector_ids")
    y_state = fields.Selection([('open', 'Open'),
                              ('accept', 'Approved'),
                              ('released','Released'),
                              ('reject', 'Rejected'), ('cancel', 'Cancelled')], default='open',string="Status")
    y_processed = fields.Boolean(copy=False,default=False,string="Porcessed")
    y_sampled_quantity = fields.Float(string="Sampled Quality")
    y_revised_sheet_ids = fields.One2many('inspection.sheet.revision','y_inspection_sheet_id',string="Revised Sheets")
    y_code = fields.Selection([('incoming', 'Receipt'),
                            ('outgoing', 'Delivery'),
                            ('internal', 'Internal Transfer'),
                            ('mrp_operation', 'Manufacturing')], related="y_picking_id.picking_type_code")
    y_plan_id = fields.Many2one('inspection.plan', compute="compute_inspection_plan", store=True,string="Inspection Plan")
    y_is_editable = fields.Boolean(compute="compute_is_editable",string="Editable")
    y_related_sheet_id = fields.Many2one('inspection.sheet', string="Related Sheet", compute="compute_related_sheet", store=True)
    y_available_product_ids = fields.Many2many('stock.picking', compute='_compute_available_product_ids',string="Available Products")
    y_warehouse_id = fields.Many2one('stock.warehouse',related='y_picking_id.picking_type_id.warehouse_id')
    y_move_line_id = fields.Many2one('stock.move.line',string="Move Line")    

    def write(self,vals):
        if vals.get('y_quality_check_ids'):
            for val in vals.get('y_quality_check_ids'):
                if val[:1] == 0 and not self.user_has_groups('quality_control_base.inspection_quality_check_access'):
                    raise UserError(_("""OOPS!!!\nLooks like you aren't authorized to add Quality Checks"""))
        return super(InspectionSheet,self).write(vals)

    @api.depends('y_picking_id')
    def _compute_available_product_ids(self):
        for sheet in self:
            product_ids = sheet.y_picking_id.move_ids_without_package.mapped('product_id')
            sheet.y_available_product_ids = [(6, 0, product_ids.ids)] if product_ids else False

    @api.onchange('y_picking_id', 'y_product_id')
    def lot_id_filter(self):
        if self.y_picking_id and self.y_product_id:
            lot_ids = self.y_picking_id.move_line_ids_without_package.filtered(lambda line: line.product_id == self.y_product_id).mapped('lot_id')
            return {'domain': {'y_lot_id': [('id', 'in', lot_ids.ids)]}}
        else:
            return {'domain': {'y_lot_id': []}}

    @api.onchange('y_quantity_recieved', 'y_quantity_accepted', 'y_quantity_rejected', 'y_quantity_destructive', 'y_under_deviation')
    def onchange_quantity_validation(self):
        for rec in self:
            if self.y_quantity_accepted > (self.y_quantity_recieved + self.y_quantity_rejected + self.y_quantity_destructive + self.y_under_deviation + self.y_quantity_pending):
                raise UserError(_(""" The Accepted Quantity should not be greater than the Received Qty, Rejected Qty, Destructive Qty, Under Deviation, Pending Qty"""))

    def compute_is_editable(self):
        for rec in self:
            rec.y_is_editable = True if rec.y_plan_id else False

    @api.depends('y_picking_id', 'y_production_id')
    def compute_related_sheet(self):
        for rec in self:
            rec.y_related_sheet_id = False
            if rec.y_picking_id and rec.y_picking_id.backorder_id:
                sheet = self.env['inspection.sheet'].search([('y_picking_id', '=', rec.y_picking_id.backorder_id.id), ('y_product_id', '=', rec.y_product_id.id)], limit=1)
                rec.y_related_sheet_id = sheet.id if sheet else False

    @api.depends('y_production_id', 'y_picking_id', 'y_product_id')
    def compute_inspection_plan(self):
        for rec in self:
            domain = [('y_product_tmpl_id', '=', rec.y_product_id.product_tmpl_id.id)]
            inspection_plan_obj = self.env['inspection.plan']
            if rec.y_production_id and rec.y_production_id.picking_type_id and rec.y_product_id:
                domain+= [('y_picking_type_id', '=', rec.y_production_id.picking_type_id.id)]
                plan = inspection_plan_obj.search(domain, limit=1)
                product_plan = plan.filtered(lambda x: x.y_product_id and x.y_product_id == rec.y_product_id)
                if plan and product_plan:
                    rec.y_plan_id = product_plan.id if product_plan else False
                else:
                    rec.y_plan_id = plan.id if plan else False
            elif rec.y_picking_id and rec.y_picking_id.picking_type_id and rec.y_product_id:
                domain += [('y_picking_type_id', '=', rec.y_picking_id.picking_type_id.id)]
                plan = inspection_plan_obj.search(domain, limit=1)
                product_plan = plan.filtered(lambda x: x.y_product_id and x.y_product_id == rec.y_product_id)
                if plan and product_plan:
                    rec.y_plan_id = product_plan.id if product_plan else False
                else:
                    rec.y_plan_id = plan.id if plan else False
            
    @api.depends('y_picking_id', 'y_product_id')
    def _get_source(self):
        for rec in self:
            rec.y_source = False
            rec.y_partner_id = False
            if rec.y_picking_id:
                purchase_id = rec.y_picking_id.move_ids_without_package.purchase_line_id.order_id
                rec.y_source = rec.y_picking_id.origin
                rec.y_partner_id = purchase_id[:1].partner_id.id if purchase_id else False
            elif rec.y_production_id:
                rec.y_source = rec.y_production_id.name
                rec.y_partner_id = False

    
    def state_approve(self):
        if self.env.user.id in self.y_team_id.y_approver_ids.ids:
            if any(self.y_quality_check_ids.filtered(lambda x:x.quality_state == 'none')):
                raise UserError(_("""OOPS!!!\nStill you need to do quality testing"""))
            else:
                self.y_state = 'accept'
                self.message_post(body="Approved")
        else:
            raise UserError(_("""OOPS!!!\nLooks like you aren't authorized to Approve"""))
        tot_sum = self.y_quantity_accepted + self.y_quantity_rejected + self.y_quantity_destructive + self.y_quantity_pending
        val = round(tot_sum,2)
        receive = round(self.y_quantity_recieved,2)
        if val != receive:
            raise ValidationError(_("""Sum of Quantities (Accepeted, Rejected, Destructive and Accepeted under Deviation) "MUST" be equal to Recieved Quantity"""))

        quality_checks = self.env['quality.check'].search([('picking_id', '=', self.y_picking_id.id),('production_id', '=',self.y_production_id.id)])
        checks = quality_checks.filtered(lambda x:x.y_inspection_sheet_id != False and x.quality_state == 'none')
        if not checks:
            quality_checks.filtered(lambda x:x.y_inspection_sheet_id == False).unlink()

    def button_cancel(self):
        for sheet in self:
            sheet.write({'y_state':'cancel'})
            for check in sheet.y_quality_check_ids:
                check.write({'quality_state':'cancel'})


    def state_reject(self):
        if self.env.user.id in self.y_team_id.approver_ids.ids:
            if any(self.y_quality_check_ids.filtered(lambda x:x.quality_state == 'none')):
                raise UserError(_("""OOPS!!!\nStill you need to do quality testing"""))
            else:
                self.y_state = 'cancel'
        else:
            raise UserError(_("""OOPS!!!\nLooks like you aren't authorized to Reject"""))
        tot_sum = self.y_quantity_accepted + self.y_quantity_rejected + self.y_quantity_destructive + self.y_under_deviation
        val = round(tot_sum,2)
        receive = round(self.y_quantity_recieved,2)
        if val != receive:
            raise ValidationError(_("""Sum of Quantities (Accepeted, Rejected, Destructive and Accepeted under Deviation) "MUST" be equal to Recieved Quantity"""))

    @api.model
    def create(self, vals):
        operation_type_id = self.env['stock.picking'].browse(vals.get('y_picking_id')).picking_type_id or self.env['mrp.production'].browse(vals.get('y_production_id')).picking_type_id
        sequence = operation_type_id.y_sequence_for_inspection_sheet or operation_type_id.y_sequence_for_inspection_sheet
        if sequence:
            vals['y_name'] = sequence.next_by_id()
        # else:
        #     raise UserError(_("{} Operation Type Inspection Sheet Sequence Not Configured...!".format(operation_type_id.name)))
        return super(InspectionSheet, self).create(vals)

    def process_quantities(self):
        if self.y_picking_id:
            line = {
                'product_id': self.y_product_id.id,
                'location_dest_id': self.y_picking_id.location_dest_id.id,
                'product_uom_id': self.y_product_id.product_tmpl_id.uom_id.id,
                'location_id': self.y_picking_id.location_id.id,
                'y_no_inspect': True
            }
            if self.y_lot_id.id:
                line.update({'lot_id': self.y_lot_id.id})
            if self.y_quantity_accepted or self.y_under_deviation:
                self.y_move_line_id.write({'quantity':self.y_quantity_accepted + self.y_under_deviation})
                line.update({'quantity': self.y_quantity_accepted + self.y_under_deviation})
                
            stock_location_obj = self.env['stock.location']
            warehouse_obj = self.y_picking_id.picking_type_id.warehouse_id
            if self.y_quantity_rejected:
                domain = [('y_reject_location', '=', True),('warehouse_id', '=', warehouse_obj.id),('company_id', '=',self.y_company_id.id)]
                reject_location = stock_location_obj.search(domain)
                if not reject_location:
                    raise UserError(_("Please set a Reject Location."))
                line.update({'quantity': self.y_quantity_rejected,'location_dest_id': reject_location.id})
                self.y_picking_id.move_line_ids_without_package = [(0, 0, line)]
            if self.y_quantity_destructive:
                domain = [('y_destructive_location', '=', True),('warehouse_id', '=', warehouse_obj.id),('company_id', '=',self.y_company_id.id)]
                destructive_location = stock_location_obj.search(domain)
                if not destructive_location:
                    raise UserError(_("Please set a Destructive Location1."))
                line.update({'quantity': self.y_quantity_destructive,'location_dest_id': destructive_location.id})
                self.y_picking_id.move_line_ids_without_package = [(0, 0, line)]
        self.write({'y_state':'released','y_processed':True})

    def revise(self):
        ids = []
        for line in self.y_quality_check_ids:
            ids.append(self.env['quality.check.revision'].create({
                'y_point_id': line.point_id.id,
                'y_title': line.title,
                'y_test_type': line.test_type,
                'y_test_type_id': line.test_type_id.id,
                'y_test_method_id': line.y_test_method_id.id,
                'y_measure': line.measure,
                'y_norm': line.y_norm,
                'y_norm_unit': line.norm_unit,
                'y_tolerance_min': line.tolerance_min,
                'y_tolerance_max': line.tolerance_max,
                'y_quality_state': line.quality_state,
            }).id)

        revise_sheet = self.env['inspection.sheet.revision'].create({
            'y_name': self.y_name,
            'y_source': self.y_source,
            'y_product_id': self.y_product_id.id,
            'y_picking_id': self.y_picking_id.id,
            'y_production_id': self.y_production_id.id,
            'y_lot_id': self.y_lot_id.id,
            'y_team_id': self.y_team_id.id,
            'y_company_id': self.y_company_id.id,
            'y_date': self.y_date,
            'y_quantity_recieved': self.y_quantity_recieved,
            'y_quantity_accepted': self.y_quantity_accepted,
            'y_quantity_rejected': self.y_quantity_rejected,
            'y_quantity_destructive': self.y_quantity_destructive,
            'y_under_deviation': self.y_under_deviation,
            'y_status': self.y_status,
            'y_sampled_quantity': self.y_sampled_quantity,
            'y_quality_check_ids': [(6, 0, ids)],
        })

        self.y_revised_sheet_ids = [(4, revise_sheet.id, 0)]
        name = self.y_name.split('-')
        number = int(name[1]) if len(name) > 1 else 0
        name = name[:1]
        self.y_name = name + '-' + str(number+1)
        self.y_state = 'open'


# Quality Check
class QualityCheck(models.Model):
    _inherit = "quality.check"

    y_inspection_sheet_id = fields.Many2one('inspection.sheet',string="Inspection Sheet")
    y_create_or_not = fields.Boolean(string="Create Or Not")
    y_picking_type_ids = fields.Many2many('stock.picking.type', string='Operation Types')
    y_test_product_id = fields.Many2one('product.product', related='y_inspection_sheet_id.y_product_id',string="Test Product")
    y_norm = fields.Float(related="point_id.norm",string="Norm")
    y_test_method_id = fields.Many2one('quality.test.method', related="point_id.y_test_method_id",string="Test Method")
    quality_state = fields.Selection([
        ('none', 'To do'),
        ('pass', 'Passed'),
        ('fail', 'Failed'),
        ('cancel', 'Cancel')], string='Status', tracking=True,
        default='none', copy=False, store=True, compute='_set_state')

    y_confirm_measurement = fields.Boolean(copy=False,string="Confirm Measurement")

    def inverse_quality_check(self):
        for rec in self:
            rec.point_id = rec.point_id
            rec.team_id = rec.team_id
            rec.title = rec.title
            rec.test_type = rec.test_type
            rec.test_type_id = rec.test_type_id
            rec.y_test_method_id = rec.y_test_method_id
            rec.measure = rec.measure
            rec.y_norm = rec.y_norm
            rec.norm_unit = rec.norm_unit
            rec.tolerance_min = rec.tolerance_min
            rec.tolerance_max = rec.tolerance_max
            rec.quality_state = rec.quality_state
            rec.y_inspection_sheet_id = rec.y_inspection_sheet_id

    def do_alert(self):
        self.ensure_one()
        alert = self.env['quality.alert'].create({
            'check_id': self.id,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'lot_id': self.lot_id.id,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'company_id': self.company_id.id,
            'picking_id': self.picking_id.id,
            'partner_id': self.y_inspection_sheet_id.y_partner_id.id,
            'y_source': self.y_inspection_sheet_id.y_source

        })
        return {
            'name': _('Quality Alert'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.alert',
            'views': [(self.env.ref('quality_control.quality_alert_view_form').id, 'form')],
            'res_id': alert.id,
            'context': {'default_check_id': self.id},
        }

    @api.depends('test_type', 'measure', 'y_confirm_measurement')
    def _set_state(self):
        for rec in self:
            if rec.test_type == 'measure':
                # this condition for the negative values
                if rec.measure > 0:
                    if not rec.tolerance_min >= 0.0 and not rec.tolerance_max > 0.0:
                        if rec.measure <= rec.tolerance_min and rec.measure >= rec.tolerance_max:
                            rec.quality_state = 'pass'
                        else:
                            rec.quality_state = 'fail'
                    elif rec.measure >= rec.tolerance_min and rec.measure <= rec.tolerance_max:
                        rec.quality_state = 'pass'
                    else:
                        rec.quality_state = 'fail'
            else:
                rec.quality_state = 'none'

    def confirm_measure_btn(self):
        if self.test_type == 'measure':
            self.y_confirm_measurement = True
        else:
            self.quality_state = 'pass'

    def fail_btn(self):
        self.quality_state = 'fail'

# Desctructive Location
class StockLocation(models.Model):
    _inherit = 'stock.location'

    y_destructive_location = fields.Boolean('Is a Desctructive Location?')
    y_reject_location = fields.Boolean('Is a Reject Location?')    

    @api.constrains('y_destructive_location', 'y_reject_location','warehouse_id','company_id','active')
    def _check_duplicate_reject_descructive(self):
        destructive_loc_ids = self.env['stock.location'].search([('warehouse_id', '=', self.warehouse_id.id), ('y_destructive_location', '=', True),('company_id','=',self.company_id.id)])
        if len(destructive_loc_ids) > 1:
            raise ValidationError(_("""Can not have more than one destructive location"""))
        reject_loc_ids = self.env['stock.location'].search([('warehouse_id', '=', self.warehouse_id.id), ('y_reject_location', '=', True),('company_id','=',self.company_id.id)])
        if len(reject_loc_ids) > 1:
            raise ValidationError(_("""Can not have more than one Reject location"""))

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    y_sequence_for_inspection_plan = fields.Many2one('ir.sequence',string="Inspection Plan Sequence")
    y_sequence_for_inspection_sheet = fields.Many2one('ir.sequence',string="Inspection Sheet Sequence")

class QualityTestMethod(models.Model):
    _name = "quality.test.method"
    _description = "Quality Test Method"
    _rec_name = "y_name"

    y_name = fields.Char(string="Test Method")

# Quality Characteristics
class QualityCharacteristic(models.Model):
    _name = 'quality.characteristic'
    _inherit = ['mail.thread']
    _description = 'Quality Characteristic'
    _rec_name = "y_name"

    y_name = fields.Char(compute='_generate_name',string="Name")
    y_code = fields.Char(tracking=True,string="Code")
    y_description = fields.Char(tracking=True,string="Description")
    active = fields.Boolean(default=True,tracking=True)

    @api.depends('y_code', 'y_description')
    def _generate_name(self):
        for rec in self:
            rec.y_name = "%s %s" % (rec.y_code or '', rec.y_description or '')

class QualityAlertTeam(models.Model):
    _inherit = 'quality.alert.team'

    y_approver_ids = fields.Many2many('res.users', string='Approver')
    y_quality_inspector_ids = fields.Many2many('hr.employee', string="Quality Inspector")
    y_inspection_sheet_count = fields.Integer('# Inspection Sheet Alerts', compute='_compute_inspection_sheet_count')
    
    def _compute_inspection_sheet_count(self):
        sheet_data = self.env['inspection.sheet'].read_group([('y_team_id', 'in', self.ids), ('y_state', 'in',('open','accept')), ('y_processed', '=',False)], ['y_team_id'], ['y_team_id'])
        sheet_result = dict((data['y_team_id'][0], data['y_team_id_count']) for data in sheet_data)
        for team in self:
            team.y_inspection_sheet_count = sheet_result.get(team.id, 0)

class StockMove(models.Model):
    _inherit = "stock.move"

    y_is_edit = fields.Boolean(compute="compute_edit_lot",string="Editable")
    y_is_quality_check_required = fields.Boolean(default=False,copy=False,string="Is Quality Check Required")

    @api.depends('picking_id', 'picking_id.picking_type_id', 'picking_id.picking_type_id.show_operations')
    def compute_edit_lot(self):
        for rec in self:
            rec.y_is_edit = False if rec.picking_id and rec.picking_id.picking_type_id and not rec.picking_id.picking_type_id.show_operations and rec.picking_id.check_ids and 'open' in rec.picking_id.check_ids.y_inspection_sheet_id.filtered(lambda x: x.y_product_id == rec.product_id).mapped('y_state') else True


    def _create_quality_checks(self):
        # Groupby move by picking. Use it in order to generate missing quality checks.
        pick_moves = defaultdict(lambda: self.env['stock.move'])
        for move in self:
            if move.picking_id:
                pick_moves[move.picking_id] |= move
        check_vals_list = self._create_operation_quality_checks(pick_moves)
        for picking, moves in pick_moves.items():
            # Quality checks by product
            quality_points_domain = self.env['quality.point']._get_domain(moves.product_id, picking.picking_type_id, measure_on='product')
            quality_points = self.env['quality.point'].sudo().search(quality_points_domain)

            if not quality_points:
                continue
            picking_check_vals_list = quality_points._get_checks_values(moves.product_id, picking.company_id.id, existing_checks=picking.sudo().check_ids)
            for check_value in picking_check_vals_list:
                check_value.update({
                    'picking_id': picking.id,
                })
            check_vals_list += picking_check_vals_list
        if check_vals_list:
            for move in self:
                move.y_is_quality_check_required = True

    def check_quality_checks_quantity(self):
        # Groupby move by picking. Use it in order to generate missing quality checks.
        pick_moves = defaultdict(lambda: self.env['stock.move'])
        for move in self.filtered(lambda x:x.quantity > 0):
            if move.picking_id:
                pick_moves[move.picking_id] |= move
        check_vals_list = self._create_operation_quality_checks(pick_moves)
        for picking, moves in pick_moves.items():
            # Quality checks by product
            quality_points_domain = self.env['quality.point']._get_domain(moves.product_id, picking.picking_type_id, measure_on='product')
            quality_points = self.env['quality.point'].sudo().search(quality_points_domain)

            if not quality_points:
                continue
            picking_check_vals_list = quality_points._get_checks_values(moves.product_id, picking.company_id.id, existing_checks=picking.sudo().check_ids)
            for check_value in picking_check_vals_list:
                check_value.update({
                    'picking_id': picking.id,
                })
            check_vals_list += picking_check_vals_list
        if check_vals_list:
            for move in self:
                move.env.cr.execute("UPDATE stock_move set y_is_quality_check_required = True WHERE id=%s" % (move.id))
                self.env.cr.commit()
        else:
            for move in self:
                move.env.cr.execute("UPDATE stock_move set y_is_quality_check_required = False WHERE id=%s" % (move.id))
                self.env.cr.commit()



# Quality with lots from Picking
class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    y_inspection_sheet_id = fields.Many2one('inspection.sheet',string="Inspection Sheet")
    y_no_inspect = fields.Boolean(string="No Inspect")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    y_inspection_sheet_ids = fields.One2many('inspection.sheet','y_picking_id',string="Inspection Sheets")
    y_quality_sheet_status = fields.Selection([('not_completed','Not Completed'),('partial','Partial Completed'),('accepted','Accepeted'),('fully_completed','Fully Completed'),('cancelled','Cancelled')],compute="get_quality_status",string="QC Status",store=True)
    y_is_quality_check_required = fields.Boolean(compute="compute_quality_check_required",string="Is Quality Check Required")

    @api.depends('move_ids_without_package.y_is_quality_check_required')
    def compute_quality_check_required(self):
        for picking in self:
            picking.y_is_quality_check_required = True if any(picking.move_ids_without_package.filtered(lambda x:x.y_is_quality_check_required == True)) else False

    def button_genarate_quality_checks_inspection_sheets(self):
        for move_line in self.move_line_ids_without_package:
            # quality_check = move_line.env['quality.check'].search([('move_line_id','=',move_line.id)])
            if not move_line.check_ids:                
                # Groupby move by picking. Use it in order to generate missing quality checks.
                pick_move_lines = defaultdict(lambda: self.env['stock.move.line'])
                if move_line.move_id.picking_id:
                    pick_move_lines[move_line.move_id.picking_id] |= move_line
                check_vals_list = self._create_operation_quality_checks_inspecion(pick_move_lines)
                for picking, move_line in pick_move_lines.items():
                    # Quality checks by product
                    quality_points_domain = self.env['quality.point']._get_domain(move_line.product_id, picking.picking_type_id, measure_on='product')
                    quality_points = self.env['quality.point'].sudo().search(quality_points_domain)

                    if not quality_points:
                        continue
                    # picking_check_vals_list = []
                    # for quality_point in quality_points.filtered(lambda x:move_line.product_id in x.product_ids):
                    #     quality_point_vals = self._get_check_values_inspecion(quality_point,move_line,picking)
                    #     picking_check_vals_list.append(quality_point_vals)

                    picking_check_vals_list = self._get_check_values_inspecion(quality_points,move_line, picking, existing_checks=picking.sudo().check_ids)
                    check_vals_list += picking_check_vals_list

                quality_check = self.env['quality.check'].sudo().create(check_vals_list)
            if move_line.check_ids:
                move_line.move_id.y_is_quality_check_required = False
            else:
                move_line.move_id.y_is_quality_check_required = True
        picking_check_ids = self.check_ids.filtered(lambda x:not x.y_inspection_sheet_id)
        if picking_check_ids:
            for move_line in picking_check_ids.mapped('move_line_id'):
                check_ids = picking_check_ids.filtered(lambda x:x.move_line_id == move_line)
                self.generate_inspection_sheets(check_ids,move_line)

        if not self.y_inspection_sheet_ids and not self.check_ids:
            self.move_ids_without_package.check_quality_checks_quantity()



    def _get_check_values_inspecion(self, quality_points,move_line_id,picking_id,existing_checks):
        quality_points_list = []
        point_values = []
        products = move_line_id.product_id
        if not existing_checks:
            existing_checks = []
        for check in existing_checks:
            point_key = (check.point_id.id, check.team_id.id, check.product_id.id)
            quality_points_list.append(point_key)

        for point in quality_points:
            if not point.check_execute_now():
                continue
            point_products = point.product_ids

            if point.product_category_ids:
                point_product_from_categories = self.env['product.product'].search([('categ_id', 'child_of', point.product_category_ids.ids), ('id', 'in', products.ids)])
                point_products |= point_product_from_categories

            if not point.product_ids and not point.product_category_ids:
                point_products |= products

            for product in point_products:
                if product not in products:
                    continue
                point_key = (point.id, point.team_id.id, product.id)
                if point_key in quality_points_list:
                    continue
                point_values.append({
                    'point_id': point.id,
                    'measure_on': point.measure_on,
                    'team_id': point.team_id.id,
                    'product_id': move_line_id.product_id.id,
                    'picking_id': picking_id.id,
                    'move_line_id': move_line_id.id,
                    'lot_name': move_line_id.lot_name,
                    'lot_id': move_line_id.lot_id.id,
                })
                quality_points_list.append(point_key)

        return point_values    

    def _create_operation_quality_checks_inspecion(self, pick_move_lines):
        check_vals_list = []
        for picking, move_line in pick_move_lines.items():
            quality_points_domain = self.env['quality.point']._get_domain(move_line.product_id, picking.picking_type_id, measure_on='operation')
            quality_points = self.env['quality.point'].sudo().search(quality_points_domain)
            for point in quality_points:
                lot_id = move_line.lot_id
                if not move_line.lot_id:
                    lot_id = self.env['stock.lot'].search([('name','=',move_line.lot_name)])
                if point.check_execute_now():
                    check_vals_list.append({
                        'point_id': point.id,
                        'team_id': point.team_id.id,
                        'measure_on': 'operation',
                        'picking_id': picking.id,
                        'lot_id':move_line.lot_id.id,
                    })
        return check_vals_list
    
    def generate_inspection_sheets(self,check_ids,move_line_id):
        check = check_ids[:1]
        sheet = self.env['inspection.sheet']
        create_params = {'y_product_id':check.product_id.id,
                        'y_team_id':check.team_id.id,
                        'y_company_id':check.company_id.id,
                        'y_move_line_id':check.move_line_id.id}
    
        create_params.update({'y_quantity_recieved':check.move_line_id.quantity_product_uom})
        if check.picking_id:
            create_params.update({'y_picking_id':check.picking_id.id})
        if check.lot_id:
            create_params.update({'y_lot_id':check.lot_id.id})
        if check.production_id:
            create_params.update({'y_production_id':check.production_id.id}) 
            value = check.production_id.qty_producing
            create_params.update({'y_quantity_recieved':value})
        if create_params.get('y_quantity_recieved') and not move_line_id.y_inspection_sheet_id:
            sheet = self.env['inspection.sheet'].create(create_params)   

        check_ids.write({'y_inspection_sheet_id':sheet.id})
        

    @api.depends('y_inspection_sheet_ids.y_state')
    def get_quality_status(self):
        for picking in self:
            picking.y_quality_sheet_status = False
            if picking.y_inspection_sheet_ids:
                if all([True if sheet.y_state == 'open' else False for sheet in picking.y_inspection_sheet_ids.filtered(lambda x:x.y_state != 'cancel')]):
                    picking.y_quality_sheet_status = 'not_completed'
                elif all([True if sheet.y_state == 'accept' else False for sheet in picking.y_inspection_sheet_ids]):
                    picking.y_quality_sheet_status = 'accepted'
                elif all([True if sheet.y_state == 'released' else False for sheet in picking.y_inspection_sheet_ids]):
                    picking.y_quality_sheet_status = 'fully_completed'
                elif all([True if sheet.y_state == 'cancel' else False for sheet in picking.y_inspection_sheet_ids]):
                    picking.y_quality_sheet_status = 'cancelled'
                else:
                    picking.y_quality_sheet_status = 'partial'

    def action_cancel(self):
        res = super(StockPicking,self).action_cancel()
        for picking in self:
            if picking.y_inspection_sheet_ids:
                picking.y_inspection_sheet_ids.button_cancel()
        return res

    def view_inspection_sheet(self):
        return {
            'name': 'Inspection Sheets',
            'view_mode': 'list,form',
            'res_model': 'inspection.sheet',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('y_picking_id', '=', self.id)],
        }

    def button_validate(self):
        self.move_ids_without_package.check_quality_checks_quantity()
        self.compute_quality_check_required()
        for picking in self:
            if picking.y_is_quality_check_required and not picking.y_inspection_sheet_ids:
                raise UserError(_("Please Generate Inspection Sheet."))
        
        res = super(StockPicking, self).button_validate()
        for picking in self:
            for line in picking.move_line_ids_without_package.filtered(lambda x: x.lot_id):
                line.lot_id.expiration_date = line.expiration_date
            if picking.check_ids:
                picking_sheets_ids = picking.y_inspection_sheet_ids
                if picking_sheets_ids:
                    if all([True if sheet.y_state == 'open' else False for sheet in picking_sheets_ids]):
                        raise UserError(_("Please Complete the QC Check in the Inspection Sheet."))

                elif not sum(picking.move_ids_without_package.mapped('quantity')):
                    raise UserError(_("Please Complete the QC Check in the Inspection Sheet."))
                sheets = picking.y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'accept')
                for sheet in sheets:
                    if not sheet.y_processed:
                        raise UserError(_("Please Release the Inventory From QC to Move the Product to Stock."))

            if picking.picking_type_id.create_backorder =='always':
                sheets = picking.y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'open')
                if sheets:
                    check_ids = sheets.mapped('y_quality_check_ids')
                    if check_ids:
                        if len(check_ids) == 1:
                            self.env.cr.execute("""delete from quality_check where id = {}""".format(check_ids[0].id))
                        else:
                            self.env.cr.execute("""delete from quality_check where id in {}""".format(tuple(check_ids.ids)))
                    if len(sheets) == 1:
                        self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id = {}""".format(sheets[0].id))
                    else:
                        self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id in {}""".format(tuple(sheets.ids)))

        return res


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        for rec in self: 
            for pickining in rec.backorder_confirmation_line_ids:
                for pick in pickining.picking_id.check_ids:
                    if pick.quality_state == 'none':
                        pick.quality_state = 'cancel'
            value = super().process()
            sheets = rec.pick_ids.filtered(lambda x: x.check_ids).y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'open')
            if sheets:
                check_ids = sheets.mapped('y_quality_check_ids')
                if check_ids:
                    if len(check_ids) == 1:
                        self.env.cr.execute("""delete from quality_check where id = {}""".format(check_ids[0].id))
                    else:
                        self.env.cr.execute("""delete from quality_check where id in {}""".format(tuple(check_ids.ids)))

                if len(sheets) == 1:
                    self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id = {}""".format(sheets[0].id))
                else:
                    self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id in {}""".format(tuple(sheets.ids)))
     
        return value


    def process_cancel_backorder(self):
        res = super().process_cancel_backorder()
        for rec in self:
            sheets = rec.pick_ids.filtered(lambda x: x.check_ids).y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'open')
            if sheets:
                check_ids = sheets.mapped('y_quality_check_ids')
                if check_ids:
                    if len(check_ids) == 1:
                        self.env.cr.execute("""delete from quality_check where id = {}""".format(check_ids[0].id))
                    else:
                        self.env.cr.execute("""delete from quality_check where id in {}""".format(tuple(check_ids.ids)))
                if len(sheets) == 1:
                    self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id = {}""".format(sheets[0].id))
                else:
                    self.env.cr.execute("""update inspection_sheet set y_state = 'cancel' where id in {}""".format(tuple(sheets.ids)))
        return res


class QualityAlertNew(models.Model):
    _inherit = "quality.alert"

    y_source = fields.Char(string="Source")

# Quality Check Revision
class QualityCheckRevision(models.Model):
    _name = "quality.check.revision"
    _description = "Quality Check Revision"
    _rec_name = 'y_title'

    y_inspection_sheet_id = fields.Many2one('inspection.sheet.revision',string="Inspection Sheet")
    y_point_id = fields.Many2one('quality.point', 'Control Point')
    y_title = fields.Char(related="y_point_id.title",string="Title")
    y_test_type = fields.Char("TTP")
    y_quality_state = fields.Selection([
        ('none', 'To do'),
        ('pass', 'Passed'),
        ('fail', 'Failed'),
        ('cancel', 'Cancel')], string='Status', tracking=True,
        default='none', copy=False, store=True, compute='_set_state')
    y_test_type_id = fields.Many2one('quality.point.test_type',string="Test Type")
    y_test_method_id = fields.Many2one('quality.test.method', related="y_point_id.y_test_method_id",string="Test Method")
    y_measure = fields.Float(string="Measure")
    y_norm = fields.Float(related="y_point_id.norm",string="Norm")
    y_norm_unit = fields.Char(related="y_point_id.norm_unit",string="Norm Unit")
    y_tolerance_min = fields.Float(related="y_point_id.tolerance_min",string="Tolerance Min")
    y_tolerance_max = fields.Float(related="y_point_id.tolerance_max",string="Tolerance Max")

    @api.depends('y_test_type', 'y_measure')
    def _set_state(self):
        for rec in self:
            if rec.y_test_type == 'measure':
                if rec.y_measure >= rec.y_tolerance_min and rec.y_measure <= rec.y_tolerance_max:
                    rec.y_quality_state = 'pass'
                else:
                    rec.y_quality_state = 'fail'
            else:
                rec.y_quality_state = 'none'


# Inspection Sheet Revision
class InspectionSheetRevision(models.Model):
    _name = "inspection.sheet.revision"
    _inherit = ['mail.thread']
    _description = "Inspection Sheet Revision"
    _rec_name = 'y_name'

    y_inspection_sheet_id = fields.Many2one('inspection.sheet',string="Inspection Sheet")
    y_name = fields.Char(string="Name")

    y_date = fields.Date(default=fields.Date.today(),string="Date")
    y_company_id = fields.Many2one('res.company',string="Company")
    y_team_id = fields.Many2one('quality.alert.team',string="Team")
    y_source = fields.Char(string="Source")
    y_picking_id = fields.Many2one('stock.picking',string="Picking")
    y_production_id = fields.Many2one('mrp.production',string="Production")
    y_product_id = fields.Many2one('product.product',string="Product")
    y_lot_id = fields.Many2one('stock.lot',string="Lot")
    y_status = fields.Selection([('open', 'Open'),
                               ('accept', 'Accept'),
                               ('reject', 'Reject'),
                               ('acceptud', 'Accepted Under Deviation')], default='open',string="Status")
    y_quantity_recieved = fields.Float(string="Quantity Received")
    y_sampled_quantity = fields.Float(string="Quantity Sampled")
    y_quantity_accepted = fields.Float(string="Quantity Accepeted")
    y_quantity_rejected = fields.Float(string="Quantity Rejected")
    y_quantity_destructive = fields.Float(string="Quantity Destructive")
    y_under_deviation = fields.Float(string="Under Deviation")
    y_quality_check_ids = fields.One2many('quality.check.revision', 'y_inspection_sheet_id',string="Checks")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    y_date_confirm = fields.Datetime(string="Date Confirm")
    y_inspection_sheet_ids = fields.One2many('inspection.sheet','y_production_id')
    y_valid_inspection_sheet_count = fields.Integer(compute="_compute_valid_inspection_sheet")
    
    def action_confirm(self):
        res = super().action_confirm()
        self.y_date_confirm = datetime.now()
        return res

    @api.depends('y_inspection_sheet_ids.y_state')
    def _compute_valid_inspection_sheet(self):
        for production in self:
            production.y_valid_inspection_sheet_count = len(production.y_inspection_sheet_ids.filtered(lambda x:x.y_state != 'cancel'))

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        for production in self:
            if any(production.y_inspection_sheet_ids.filtered(lambda x:x.y_state in ('accept','released'))):
                raise ValidationError("You can only update the quantity inspection sheet when it is in an open state.")
            open_inspection_sheet_ids = production.y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'open')
            if open_inspection_sheet_ids:
                open_inspection_sheet_ids.write({'y_quantity_recieved':production.qty_producing})                

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        if not self.y_inspection_sheet_ids.filtered(lambda x:x.y_state != 'cancel') and self.check_ids:
            raise UserError(_("Please Generate Inspection Sheet."))

        if self.y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'open') and self.check_ids:
            raise UserError(_("Please Complete the QC Check in the Inspection Sheet."))

        if self.y_inspection_sheet_ids.filtered(lambda x:x.y_state == 'accept') and self.check_ids:
            raise UserError(_("Please release the inventory that is pending from quality control."))
        return res

    def button_genarate_inpection_sheet(self):
        for production in self:
            if production.product_id.tracking == 'lot' and production.product_id.type == 'consu' and not production.lot_producing_id:
                raise UserError("Lot Required To Generate Inspection Sheet")
            if production.check_ids:
                if not production.check_ids.filtered(lambda x:x.y_inspection_sheet_id.y_state != 'cancel').mapped('y_inspection_sheet_id'):
                    rec = production.check_ids[0]
                    vals = {'y_product_id':rec.product_id.id,
                            'y_team_id':rec.team_id.id,
                            'y_company_id':rec.company_id.id,
                            'y_lot_id':production.lot_producing_id.id,
                            'y_quantity_recieved':rec.production_id.qty_producing,
                            'y_production_id':rec.production_id.id,
                            }
                    if rec.production_id.qty_producing <= 0:
                        raise UserError(_("Quantity Producing Should Be Greter Then Zero"))

                    sheet = self.env['inspection.sheet'].create(vals).id                
                    production.check_ids.write({'y_inspection_sheet_id': sheet})

    def view_quality_inspection_sheet_action(self):
        return {
            'name': 'Inspection Sheets',
            'view_mode': 'list,form',
            'res_model': 'inspection.sheet',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('y_production_id', '=', self.id)],
            }