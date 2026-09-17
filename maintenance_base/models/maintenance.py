# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time
from odoo.addons.resource.models.utils import float_to_time, HOURS_PER_DAY
from random import randint
import calendar


class MaintenanceRequestTasks(models.Model):
    _name = 'maintenance.request.task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Maintenance Request Task"

    active = fields.Boolean(default=True, copy=False)
    name = fields.Char(string="Name", tracking=True)
    ttype = fields.Selection([('equipment_category', 'Equipment Category'), ('equipment', 'Equipment')], string="Type",
                             default="equipment_category", tracking=True)
    maintenance_type = fields.Selection(
        [('corrective', 'Corrective'), ('preventive', 'Preventive'), ('breakdown', 'Break Down')],
        string='Maintenance Type', default="corrective", tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date("End Date", tracking=True)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', ondelete='restrict')
    category_id = fields.Many2one('maintenance.equipment.category', string='Category')
    maintenance_request_task_line_ids = fields.One2many('maintenance.request.task.line', 'maintenance_request_task_id')

    @api.constrains('start_date', 'end_date')
    def date_constrains(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_("'Start Date' must be before 'End Date'"))


class MaintenanceRequestTaskLine(models.Model):
    _name = 'maintenance.request.task.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    maintenance_request_task_id = fields.Many2one('maintenance.request.task')
    name = fields.Char(string="Task")
    lead_time = fields.Integer(string="Lead Time")
    lead_period = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='hours', string="UOM")
    lead_type = fields.Selection([('sequencial', 'Sequencial'), ('parallel', 'Parallel')], string='Lead Type',
                                 default="sequencial")
    serial_no = fields.Char(string="#", compute="_compute_serial_no")

    @api.depends('name')
    def _compute_serial_no(self):
        number = 1
        self.serial_no = number
        for line in self.maintenance_request_task_id.maintenance_request_task_line_ids:
            if line.name:
                line.serial_no = str(number)
                number += 1
            else:
                line.serial_no = str(number)

    @api.constrains('lead_time')
    def _check_lead_time(self):
        for task in self:
            if task.lead_time < 1:
                raise UserError("Lead time should be greater than zero.")


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    sequence = fields.Many2one('ir.sequence')
    working_schedule_id = fields.Many2one('resource.calendar', string="Factory Schedule")


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    quantity = fields.Float(string="Quantity", tracking=True)
    equipment_number = fields.Char(default=lambda self: _('New'))
    state = fields.Selection([
        ('available', 'Available'),
        ('inuse', 'In Use'),
        ('under_maintenance', 'Under Maintenance'),
        ('scrap', 'Scrap'),
    ], string='Status', tracking=True, default='available')
    y_type = fields.Selection([('parent', 'Parent'), ('child', 'Child')], string='Type',
                              tracking=True, default='parent')

    sub_category_1 = fields.Many2one('sub.equipment.categ.1', string="Sub-Category 1")
    sub_category_2 = fields.Many2one('sub.equipment.categ.2', string=" Sub-Category 2")
    sub_category_3 = fields.Many2one('sub.equipment.categ.3', string="Sub-Category 3")
    dimension = fields.Char()
    location_id = fields.Many2one('stock.location', string="Stored Location", store=True)
    is_seq = fields.Boolean(compute="_check_sequence", store=True)
    image_equ = fields.Image("Image", max_width=128, max_height=128, store=True)
    working_schedule_id = fields.Many2one('resource.calendar', string="Factory Schedule")

    maintenance_equipment_request_ids = fields.One2many('maintenance.request', 'equipment_id')

    @api.depends('category_id')
    def _check_sequence(self):
        for each in self:
            if each.category_id and each.category_id.sequence:
                each.is_seq = True
            else:
                each.is_seq = False

    @api.model
    def create(self, vals):
        if vals.get('category_id') and vals.get('equipment_number', _('New')) == _('New'):
            categ = self.env['maintenance.equipment.category'].browse(vals['category_id'])
            if categ.sequence:
                vals['equipment_number'] = categ.sequence.next_by_id()
            else:
                raise UserError("Maintenance Request Not Sequence Configured {} Category".format(categ.name))
        return super(MaintenanceEquipment, self).create(vals)

    frequency = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
         ('half_yearly', 'Half Yearly'), ('yearly', 'Yearly')], default="daily")
    manual_input_date = fields.Date()
    state_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    is_every = fields.Boolean(string="Every")

    def get_increment_shedule(self, schedule_date):
        if self.frequency == 'daily':
            return schedule_date + relativedelta(days=1)
        elif self.frequency == 'weekly':
            return schedule_date + relativedelta(weeks=1)
        elif self.frequency == 'monthly':
            return schedule_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            return schedule_date + relativedelta(months=4)
        elif self.frequency == 'half_yearly':
            return schedule_date + relativedelta(months=6)
        elif self.frequency == 'yearly':
            return schedule_date + relativedelta(years=1)
        else:
            return schedule_date + relativedelta(days=1)

    def action_equipment_schudule(self, equipment, schedule_date):
        MaintenanceRequest = self.env['maintenance.request']
        schedule = [line.schedule_date.date() for line in self.maintenance_equipment_request_ids]
        year = schedule_date.year
        month = schedule_date.month
        day = schedule_date.day
        dayNumber = calendar.weekday(year, month, day)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        resource = self.working_schedule_id.attendance_ids.filtered(lambda x: x.dayofweek == str(dayNumber))
        current_year = datetime.today().year

        public_holidays_list = self.env['resource.calendar.leaves'].search([]).filtered(
            lambda x: x.date_from.year == current_year)
        public_holidays_date_list = public_holidays_list.mapped('date_from')
        if schedule_date not in schedule and resource and schedule_date not in public_holidays_date_list:
            MaintenanceRequest.create({
                'name': equipment.name,
                'equipment_id': equipment.id,
                'category_id': equipment.category_id.id,
                'company_id': equipment.company_id.id,
                'user_id': equipment.technician_user_id.id,
                'schedule_date': schedule_date,
            })
        next_schedule_date = self.get_increment_shedule(schedule_date)
        if self.end_date > next_schedule_date:
            self.action_equipment_schudule(equipment, next_schedule_date)

    def action_generate_schudule(self):
        for equipment in self:
            resource_calendar = equipment.working_schedule_id
            schedule_date = equipment.state_date
            if not equipment.state_date:
                raise ValidationError("Start Date Required to Schedule")
            if not equipment.end_date:
                raise ValidationError("End Date Required to Schedule")

            self.action_equipment_schudule(equipment, schedule_date, )

    @api.onchange('category_id')
    def onchange_equioment_category(self):
        for rec in self:
            if rec.category_id:
                rec.working_schedule_id = rec.category_id.working_schedule_id.id


class MaintenanceStage(models.Model):
    _inherit = "maintenance.stage"

    def _get_default_color(self):
        return randint(1, 11)

    job_work = fields.Boolean('Job Work/Purchase')

    y_color = fields.Integer('Color', default=_get_default_color)


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.team"

    sequence_id = fields.Many2one('ir.sequence')


class MaintenanceTaskRequest(models.Model):
    _name = 'maintenance.task.request'
    _description = "Maintenance Task Request"

    maintenance_request_id = fields.Many2one('maintenance.request')
    serial_no = fields.Char(string="#", compute="_compute_serial_no")

    active = fields.Boolean(default=True, copy=False)
    name = fields.Char(string="Name", tracking=True)
    maintenance_type = fields.Selection(
        [('corrective', 'Corrective'), ('preventive', 'Preventive'), ('breakdown', 'Break Down')],
        string='Maintenance Type', default="corrective", tracking=True)
    technician_user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.uid, tracking=True)
    lead_time = fields.Integer(string="Lead Time")
    lead_type = fields.Selection([('sequencial', 'Sequencial'), ('parallel', 'Parallel')], string='Lead Type',
                                 default="sequencial", tracking=True)
    lead_period = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='hours', string="UOM")
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', ondelete='restrict')
    category_id = fields.Many2one('maintenance.equipment.category', string='Category')
    maintenance_request_task_line_id = fields.Many2one('maintenance.request.task.line')
    planned_start_date = fields.Datetime(string="Planned Start Date")
    planned_end_date = fields.Datetime(string="Planned End Date")
    actual_start_date = fields.Datetime(string="Actual Start Date")
    actual_end_date = fields.Datetime(string="Actual End Date")

    y_remark = fields.Char(string="Remark")
    y_resposible_person = fields.Char(string="Responsible Person")
    y_observation = fields.Char(string="Observation")

    @api.constrains('lead_time')
    def _check_lead_time(self):
        for task in self:
            if task.lead_time < 1:
                raise UserError("Lead time should be greater than zero.")

    @api.depends('name')
    def _compute_serial_no(self):
        number = 1
        self.serial_no = number
        for line in self.maintenance_request_id.maintenance_task_ids:
            if line.name:
                line.serial_no = str(number)
                number += 1
            else:
                line.serial_no = str(number)

    def write(self, vals):
        if not vals.get('maintenance_request_task_line_id') and (
                vals.get('lead_time') or vals.get('lead_type') or vals.get('lead_period')):
            for rec in self:
                if rec.id == rec.maintenance_request_id.maintenance_task_ids.mapped('id')[0]:
                    rec.planned_start_date = rec.maintenance_request_id.schedule_date
                    if rec.lead_period == 'hours':
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            hours=rec.lead_time)
                    else:
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            days=rec.lead_time)
                else:
                    if rec.lead_type == 'sequencial':
                        filterd_line_ids = rec.maintenance_request_id.maintenance_task_ids.mapped('id')
                        previos_record_id = filterd_line_ids[filterd_line_ids.index(rec.id) - 1]
                        previos_record = previos_record = rec.env['maintenance.task.request'].browse(previos_record_id)
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.planned_start_date + relativedelta(hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.planned_start_date + relativedelta(days=rec.lead_time)

                    else:
                        rec.planned_start_date = rec.maintenance_request_id.schedule_date
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                days=rec.lead_time)

        return super().write(vals)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not vals.get('maintenance_request_task_line_id'):
            for rec in res:
                if rec.id == rec.maintenance_request_id.maintenance_task_ids.mapped('id')[0]:
                    rec.planned_start_date = rec.maintenance_request_id.schedule_date
                    if rec.lead_period == 'hours':
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            hours=rec.lead_time)
                    else:
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            days=rec.lead_time)
                else:
                    if rec.lead_type == 'sequencial':
                        filterd_line_ids = rec.maintenance_request_id.maintenance_task_ids.mapped('id')
                        previos_record_id = filterd_line_ids[filterd_line_ids.index(rec.id) - 1]
                        previos_record = previos_record = rec.env['maintenance.task.request'].browse(previos_record_id)
                        rec.planned_start_date = previos_record.planned_end_date
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.planned_start_date + relativedelta(hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.planned_start_date + relativedelta(days=rec.lead_time)

                    else:
                        rec.planned_start_date = rec.maintenance_request_id.schedule_date
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                days=rec.lead_time)

        return res


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    name = fields.Char(default=lambda self: _('New'), readonly=True, required=False, copy=False)
    jobwork_challan_no = fields.Char(default="/", readonly=True)
    maintenance_type = fields.Selection(selection_add=[('breakdown', 'Break Down')])
    maintenance_task_ids = fields.One2many('maintenance.task.request', 'maintenance_request_id')
    member_ids = fields.Many2many('res.users', 'maintenance_request_user_rel', string="Team Members",
                                  domain="[('company_ids', 'in', company_id)]")
    y_show_allocation = fields.Boolean(compute="_compute_show_allocation")
    y_allowed_equipment_ids = fields.Many2many('maintenance.equipment', compute='_compute_allowed_equipment_ids')
    y_parent_equipment_id = fields.Many2one('maintenance.equipment', string="Parent Equipment",
        compute='_compute_parent_equipment', store=True, readonly=True)

    @api.depends('equipment_id')
    def _compute_parent_equipment(self):
        for rec in self:
            rec.y_parent_equipment_id = False

            if not rec.equipment_id:
                continue

            allocation_line = self.env['equipment.allocation.line'].search([('y_equipment_id', '=', rec.equipment_id.id)], limit=1)
            if allocation_line:
                rec.y_parent_equipment_id = allocation_line.y_allocation_id.y_equipment_id

    @api.depends('equipment_id')
    def _compute_allowed_equipment_ids(self):
        for rec in self:
            allocation = self.env['equipment.allocation'].search([('y_equipment_id', '=', rec.equipment_id.id)], limit=1)

            rec.y_allowed_equipment_ids = allocation.y_line_ids.mapped('y_equipment_id')

    @api.depends('equipment_id')
    def _compute_show_allocation(self):
        for rec in self:
            rec.y_show_allocation = rec.equipment_id.y_type == 'parent'


    def action_generate_tasks(self):
        for request in self:
            vals = []
            task_ids = request.env['maintenance.request.task'].search(
                [('maintenance_type', '=', request.maintenance_type), '|',
                 ('equipment_id', '=', request.equipment_id.id), ('category_id', '=', request.category_id.id)])
            for task in task_ids.mapped('maintenance_request_task_line_ids'):
                if task.id not in request.maintenance_task_ids.mapped('maintenance_request_task_line_id.id'):
                    vals.append((0, 0, {'maintenance_request_task_line_id': task.id,
                                        'name': task.name,
                                        'technician_user_id': request.user_id.id,
                                        'lead_time': task.lead_time,
                                        'lead_type': task.lead_type,
                                        'lead_period': task.lead_period,
                                        'maintenance_request_id': request.id,
                                        }))

            if vals:
                request.write({'maintenance_task_ids': vals})

            task_line_ids = request.maintenance_task_ids
            for rec in task_line_ids:
                if rec.id == task_line_ids.mapped('id')[0]:
                    rec.planned_start_date = rec.maintenance_request_id.schedule_date
                    if rec.lead_period == 'hours':
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            hours=rec.lead_time)
                    else:
                        rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                            days=rec.lead_time)
                else:
                    if rec.lead_type == 'sequencial':
                        previos_record = rec.env['maintenance.task.request'].browse(rec.id - 1)
                        rec.planned_start_date = previos_record.planned_end_date
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.planned_start_date + relativedelta(hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.planned_start_date + relativedelta(days=rec.lead_time)

                    else:
                        rec.planned_start_date = rec.maintenance_request_id.schedule_date
                        if rec.lead_period == 'hours':
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                hours=rec.lead_time)
                        else:
                            rec.planned_end_date = rec.maintenance_request_id.schedule_date + relativedelta(
                                days=rec.lead_time)

    @api.model
    def create(self, vals):
        request = super(MaintenanceRequest, self).create(vals)
        if request.maintenance_team_id and request.maintenance_team_id.sequence_id:
            request.name = request.maintenance_team_id.sequence_id.next_by_id()
        else:
            raise UserError(
                "Maintenance Request Not Sequence Configured {} Team".format(request.maintenance_team_id.name))
        if request.equipment_id:
            request.equipment_id.state = 'under_maintenance'
        return request

    @api.onchange('stage_id')
    def change_equipment_state(self):
        if self.equipment_id:
            if self.stage_id.done == True:
                self.equipment_id.state = 'available'
            else:
                self.equipment_id.state = 'under_maintenance'
