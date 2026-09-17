from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    y_is_a_quothation_customer = fields.Boolean(string="Is quotation number")
    y_team_id = fields.Many2one('crm.team',string="Sales Team",copy=False)
 
class SaleOrder(models.Model):
    _inherit = 'sale.order'

   # added the crm.lead model fields data to sale.order model  below to payment_term_id(09-07-2020)
    y_rel_company_name = fields.Char(string="Customer Name",related='opportunity_id.partner_name')
    y_rel_contact_name = fields.Char(string="Contact Name",related='opportunity_id.contact_name')
    y_lead_no = fields.Char(string="Lead No",compute='get_lead_no',store=True)
    y_team_id = fields.Many2one('crm.team',string="Sales Team",copy=False)


    @api.depends("opportunity_id")
    def get_lead_no(self):
        for each_lead in self:
            if each_lead.opportunity_id:
                each_lead.y_lead_no= each_lead.opportunity_id.y_sequence_name
            else:
                each_lead.y_lead_no =False

    @api.onchange("opportunity_id")
    def _onchange_opportunity_id(self):
        if self.opportunity_id.y_crm_product_line_ids:
            order_lines =[]
            for rec in self.opportunity_id.y_crm_product_line_ids:
                vals = ({
                    'name' : "[{}]{}".format(rec.y_cust_product_id.default_code,rec.y_cust_product_id.name),
                    'product_uom' : rec.y_cust_product_id.uom_po_id.id,
                    'product_id' :rec.y_cust_product_id.id,
                    'product_uom_qty' : rec.y_cust_qty,
                    'price_unit' : rec.y_cust_price,
                    })
                order_lines.append((0,0,vals))        
            self.order_line = order_lines
        else:
            self.order_line = False

    @api.onchange('partner_id')
    def onchange_partner_salesteam(self):
        for order in self:
            if order.partner_id:
                order.write({'y_team_id':order.partner_id.y_team_id.id})

   