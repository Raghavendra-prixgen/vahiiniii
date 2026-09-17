from odoo import _, api, fields, models
from odoo.exceptions import UserError

_STATES = [
    ("draft", "Open"),
    ("to_approve", "Pending for approval"),
    ("approved", "Purchase Request"),
    ("partial","Partial"),
    ("done", "Completed"),
    ("rejected", "Rejected"),
    ('cancel','Cancelled')
]

class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)


    name = fields.Char(string="Request Reference",required=True,copy=False,default=lambda self: _("New"),tracking=True)
    origin = fields.Char(string="Source Document")
    requested_by = fields.Many2one(comodel_name="res.users",required=True,copy=False,tracking=True,default=lambda self: self.env.uid,index=True)
    assigned_to = fields.Many2one(comodel_name="res.users",string="Approver",tracking=True,domain=lambda self: [("groups_id","in",self.env.ref("purchase_base_18.group_purchase_request_manager").id)],index=True)
    approver_ids = fields.Many2many(comodel_name="res.users",string="Approver",tracking=True,copy=False,index=True)
    description = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company",required=False,default=lambda self: self.env.company.id,tracking=True)
    parent_company_id = fields.Many2one('res.company',related="company_id.parent_id")
    line_ids = fields.One2many(comodel_name="purchase.request.line",inverse_name="request_id",string="Products to Purchase",readonly=False,copy=True,tracking=True,)
    product_id = fields.Many2one(comodel_name="product.product",related="line_ids.product_id",string="Product",readonly=True,)
    state = fields.Selection(selection=_STATES,string="Status",index=True,tracking=True,required=True,copy=False,default="draft",)
    is_editable = fields.Boolean(compute="_compute_is_editable", readonly=True)
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")
    
    line_count = fields.Integer(
        string="Purchase Request Line count",
        compute="_compute_line_count",
        readonly=True,
    )

    purchase_count = fields.Integer(
        string="Purchases count", compute="_compute_purchase_count", readonly=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    estimated_cost = fields.Monetary(
        compute="_compute_estimated_cost",
        string="Total Estimated Cost",
        store=True,
    )
    request_type_id = fields.Many2one('request.type',string="Request Type",tracking=True)
    y_is_short_closed = fields.Boolean(string="Short Close")

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',  default=_default_picking_type, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment")


    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        company_warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if not company_warehouse:
            self.env['stock.warehouse']._warehouse_redirect_warning()
        return picking_type[:1]
        
    def short_close_form_wizard(self):
        po_lines=self.line_ids.filtered(lambda line: line.y_is_short_close == False and line.product_qty != line.qty_received)            
        if self.state == 'purchase' and po_lines:    
            return {
                'name': ("Purchase Short Close Wizard"),

                'type': 'ir.actions.act_window',

                'res_model': 'purchase.short.close.wizard',

                'view_mode': 'form',

                'views': [(self.env.ref('purchase_base_18.view_purchase_short_close_wizard_form').id, 'form')],

                'target': 'new',
                
                'context': dict(self._context,default_y_purchase_id=self.id,default_sc_po_lines_ids = po_lines.ids)
            }
        elif self.state not in ['purchase']:
            raise UserError(_('Purchase Short Close can be processed only if the Order is in Purchase Order State!'))

    @api.depends("state")
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ("to_approve", "approved", "rejected", "done"):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.onchange('request_type_id')
    def flow_approver(self):
        for rec in self:
            if rec.request_type_id:
                rec.approver_ids = rec.request_type_id.approver_ids.ids

    @api.depends("line_ids", "line_ids.estimated_cost")
    def _compute_estimated_cost(self):
        for rec in self:
            rec.estimated_cost = sum(rec.line_ids.mapped("estimated_cost"))

    @api.depends("line_ids.purchase_lines")
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.mapped("line_ids.purchase_lines.order_id"))

    @api.depends("line_ids")
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.mapped("line_ids"))

    def action_view_purchase_order(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        lines = self.mapped("line_ids.purchase_lines.order_id")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [(self.env.ref("purchase.purchase_order_form").id, "form")]
            action["res_id"] = lines.id
        return action

    
    def action_view_purchase_request_line(self):
        action = (self.env.ref("purchase_base_18.purchase_request_line_form_action").sudo().read()[0])
        lines = self.mapped("line_ids")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [(self.env.ref("purchase_base_18.purchase_request_line_form").id, "form")]
            action["res_id"] = lines.ids[0]
        return action

    @api.depends("state", "line_ids.product_qty", "line_ids.cancelled")
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "draft" and any(not line.cancelled and line.product_qty for line in rec.line_ids)

    @api.model
    def _get_partner_id(self, request):
        user_id = request.assigned_to or self.env.user
        return user_id.partner_id.id

    @api.model_create_multi
    def create(self, vals_list):
        request_type_id = self.env['request.type'].search([('id','=',vals_list[0].get('request_type_id'))])
        vals_list[0].update({'approver_ids':[(6,0,request_type_id.approver_ids.ids)]})
        if vals_list[0].get('y_name', _('New')) == _('New'):
            if not request_type_id.sequence_id:
                raise UserError(_("'{}' Request Type Sequence Not Configured.".format(request_type_id.name)))
            vals_list[0].update({'name': request_type_id.sequence_id.next_by_id()})

        requests = super(PurchaseRequest, self).create(vals_list)
        for vals, request in zip(vals_list, requests):
            if vals.get("assigned_to"):
                partner_id = self._get_partner_id(request)
                request.message_subscribe(partner_ids=[partner_id])
        return requests

    def write(self, vals):
        res = super(PurchaseRequest, self).write(vals)
        for request in self:
            if vals.get("assigned_to"):
                partner_id = self._get_partner_id(request)
                request.message_subscribe(partner_ids=[partner_id])
        return res

    def _can_be_deleted(self):
        self.ensure_one()
        return self.state == "draft"

    def unlink(self):
        for request in self:
            if not request._can_be_deleted():
                raise UserError(("You cannot delete a purchase request which is not draft."))
        return super(PurchaseRequest, self).unlink()

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        self.write({"state": "draft"})

    def button_to_approve(self):
        if not self.line_ids:
            raise UserError (_("Hey, looks like those products aren't up for approval right now."))
        self.write({"state": "to_approve"})

    def button_approved(self):
        if self.env.user in self.approver_ids:
            self.write({"state": "approved"})
        else:
            raise UserError (_("Oops!!!! You can't approve the order"))

    def button_rejected(self):
        if self.env.user in self.approver_ids:
            self.mapped("line_ids").do_cancel()
            self.write({"state": "rejected"})
        else:
            raise UserError (_("Oops!!!! You can't reject the order"))

    def button_cancel(self):
        for request in self:
            request.write({'state':'cancel'})

    def button_done(self):
        self.write({"state": "done"})

    def check_auto_reject(self):
        """When all lines are cancelled the purchase request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({"state": "rejected"})

    def to_approve_allowed_check(self):
        for rec in self:
            if not rec.to_approve_allowed:
                raise UserError(_("You can't request an approval for a purchase request "
                        "which is empty. (%s)")% rec.name)
    
class ProductTemplate(models.Model):
    _inherit = "product.template"

    purchase_request = fields.Boolean(help="Check this box to generate Purchase Request instead of "
        "generating Requests For Quotation from procurement.",company_dependent=True,)

class RequestType(models.Model):
    _name = "request.type"
    _description = "Request Type"

    name = fields.Char(string="Request Type")
    active = fields.Boolean(string="Active",default=True)
    sequence_id = fields.Many2one('ir.sequence',string="Sequence")
    approver_ids = fields.Many2many('res.users')
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)