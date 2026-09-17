from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit='sale.order'
    
    y_enquiry_date = fields.Datetime(string="Enquiry Date",related="opportunity_id.create_date") 
    y_advance_amount = fields.Char(string="Advance Amount",store=True)
   
    y_delivered_to = fields.Char(string="Deliver To")
    
    y_po_date = fields.Date(String='PO Date', store=True)
    y_custom_po_no = fields.Char(string="Customer PO no", store=True)
    

    y_proforma_sequence = fields.Char(string="Proforma Invoice Number",readonly=True)
    
    y_product_as_per_is = fields.Char(string="Product As Per IS", tracking=True)
    



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order') or _('New')
                vals['y_proforma_sequence'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('proforma.sale.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
                vals['y_proforma_sequence'] = self.env['ir.sequence'].next_by_code('proforma.sale.order') or _('New')
        
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result
        
    def _prepare_invoice(self):
        res = super()._prepare_invoice()        
        if self.y_po_date:
            res["y_custom_po_no"] = self.y_custom_po_no
            res["y_po_date"]=self.y_po_date
        return res  
    
    
                
    @api.depends('partner_id', 'user_id')
    def _compute_team_id(self):
        res = super(SaleOrder, self)._compute_team_id()
        for order in self:
            if order.partner_id:
                order.team_id = order.partner_id.y_team_id
                order.user_id = order.partner_id.user_id.id
        return res





