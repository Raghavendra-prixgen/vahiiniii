from odoo import models, fields, api, _
from datetime import datetime

class CrmLead(models.Model):
    _inherit = "crm.lead"

    y_coordinator_id = fields.Many2one('res.users','Responsible By')
    y_expected_date = fields.Datetime(string='Expected Closing', copy=False, default=fields.Datetime.now)
    y_cust_user_ids = fields.Many2many('res.users', 'cust_user_crm_ref','cust_lead_id','cust_user_id',string='Users')
    y_cust_type_of_sale = fields.Selection([('standard','Standard'),('project','Project')],string='Type of Sale')
    y_crm_product_line_ids = fields.One2many('cust.crm.lead.prduct.line','y_cust_crm_lead_id')
    y_customer_title=fields.Many2one('res.partner.title')
    y_sequence_name = fields.Char("Lead No",readonly=True)

    @api.onchange('y_expected_date')
    def onchange_date(self):
        for rec in self:
            if rec.y_expected_date:
                rec.date_deadline = rec.y_expected_date

    @api.onchange('y_crm_product_line_ids')
    def calc_planned_revenue(self):
        self.expected_revenue = sum(self.y_crm_product_line_ids.mapped('y_cust_subtotal'))

    @api.onchange('team_id')
    def get_uer_ids(self):
        for each_lead in self:
            if each_lead.team_id:
                each_lead.y_cust_user_ids = [(6, 0, each_lead.team_id.member_ids.ids)]

    def update_data(self):
        for record in self.y_crm_product_line_ids:
            record.y_cust_price = record.y_cust_product_id.lst_price
            quant_ids = self.env['stock.quant'].search([('product_id','=',record.y_cust_product_id.id),('product_id.default_code','=',record.y_cust_product_id.default_code)])
            record.y_available_quantity = sum(quant_ids.filtered(lambda x:x.location_id.usage == 'internal' and x.location_id.location_id and x.available_quantity > 0).mapped('available_quantity'))

    @api.model
    def create(self,vals):
        if vals.get('y_sequence_name', _('New')) == _('New'):
            vals['y_sequence_name'] = self.env['ir.sequence'].next_by_code('crm.leads') or _('New')
        res = super(CrmLead, self).create(vals)
        return res


    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        # set default value in context, if not already set (Put stage to 'new' stage)
        context = dict(self._context)
        context.setdefault('default_type', self.type)
        context.setdefault('default_team_id', self.team_id.id)
        # Set date_open to today if it is an opp
        default = default or {}
        default['date_open'] = fields.Datetime.now() if self.type == 'opportunity' else False
        # Do not assign to an archived user
        if not self.user_id.active:
            default['user_id'] = False
        default['y_sequence_name'] = self.env['ir.sequence'].next_by_code('crm.leads') or _('New')
        return super(CrmLead, self.with_context(context)).copy(default=default)

 

class CRMLeadProductLine(models.Model):
    _name = "cust.crm.lead.prduct.line" 
    _description = "CUST CRM LEAD PRODUCT LINE"

    y_cust_crm_lead_id = fields.Many2one('crm.lead')
    y_cust_product_id = fields.Many2one('product.product','Product')
    y_cust_qty = fields.Float('Quantity')
    y_cust_price = fields.Float('Price')
    y_cust_subtotal = fields.Float('Subtotal',compute='_calc_subtotal', store=True)
    y_company_currency = fields.Many2one("res.currency",string='Currency' )
    y_available_quantity=fields.Float(string="Available Quantity")

    @api.depends('y_cust_qty','y_cust_price','y_cust_subtotal')
    def _calc_subtotal(self):
        for rec in self:
            rec.y_cust_subtotal = rec.y_cust_qty * rec.y_cust_price

    @api.onchange('y_cust_product_id')
    def _change_cust_price(self):       
        for record in self:
            self.y_cust_price = self.y_cust_product_id.lst_price
            quant_ids = self.env['stock.quant'].search([('product_id','=',record.y_cust_product_id.id),('product_id.default_code','=',record.y_cust_product_id.default_code)])
            record.y_available_quantity = sum(quant_ids.filtered(lambda x:x.location_id.usage == 'internal' and x.location_id.location_id and x.available_quantity > 0).mapped('available_quantity'))


    def refreshtochange(self):
        for record in self:
            self.y_cust_price = self.y_cust_product_id.lst_price
            quant_ids = self.env['stock.quant'].search([('product_id','=',record.y_cust_product_id.id),('product_id.default_code','=',record.y_cust_product_id.default_code)])                   
            record.y_available_quantity = sum(quant_ids.filtered(lambda x:x.location_id.usage == 'internal' and x.location_id.location_id and x.available_quantity > 0).mapped('available_quantity'))

    def update_data(self):
        for record in self:
            self.y_cust_price = self.y_cust_product_id.lst_price
            quant_ids = self.env['stock.quant'].search([('product_id','=',record.y_cust_product_id.id),('product_id.default_code','=',record.y_cust_product_id.default_code)])
            record.y_available_quantity = sum(quant_ids.filtered(lambda x:x.location_id.usage == 'internal' and x.location_id.location_id and x.available_quantity > 0).mapped('available_quantity'))

class CRMTAGACTIVE(models.Model):
    _inherit = 'crm.tag'

    active = fields.Boolean(default=True)

