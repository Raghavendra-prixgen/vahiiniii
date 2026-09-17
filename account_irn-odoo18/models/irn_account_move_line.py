from odoo import api, fields, models, _
from odoo.exceptions import  UserError, ValidationError, AccessError


class AccountMoveIrnLine(models.Model):
    _name = "irn.account.move.line"
    _description = "Journal Entries Irn Line"

    irn_id = fields.Many2one('irn.account.move')
    
    SlNo = fields.Char("Serial No.")
    @api.constrains('SlNo')
    def _check_sl_no(self):
        for rec in self:
            slno_len = len(rec.SlNo or '')
            if slno_len < 1 or slno_len > 6:
                raise ValidationError(_('Serial Number does not match expected format'))
    
    IsServc = fields.Selection(string="Is Service", help="Specify whether the supply is service or not", selection=[('Y','Yes'),('N','No')])
    
    PrdDesc  = fields.Char("Item Description")
    @api.constrains('PrdDesc')
    def _check_item_desc(self):
        for rec in self:
            item_len = len(rec.PrdDesc or '')
            if item_len < 1 or item_len > 250:
                raise ValidationError(_('Item Description is not valid'))
            
    HsnCd = fields.Char("HSN Code")
    @api.constrains('HsnCd')
    def _check_hsn(self):
        for rec in self:
            hsn_len = len(rec.HsnCd or '')
            if hsn_len < 4 or hsn_len > 8:
                raise ValidationError(_('HSN Code is not valid'))
    
    Qty = fields.Float("Quantity")
    @api.constrains('Qty')
    def _check_qty(self):
        for rec in self:
            if rec.Qty < 0 or rec.Qty > 999999999999.999:
                raise ValidationError(_('Qty out of range'))

    Unit = fields.Char()
    @api.constrains('Unit')
    def _check_unit(self):
        for rec in self:
            unit_len = len(rec.Unit or '')
            if unit_len < 3 or unit_len > 8:
                raise ValidationError(_('Unit is not valid'))
    
    UnitPrice = fields.Float("Unit Price")
    @api.constrains('UnitPrice')
    def _check_unit_price(self):
        for rec in self:
            if rec.UnitPrice < 0 or rec.UnitPrice > 999999999999.999:
                raise ValidationError(_('Unit price out of range'))
    
    TotAmt = fields.Float("Gross Amount")
    @api.constrains('TotAmt')
    def _check_tot_amt(self):
        for rec in self:
            if rec.TotAmt < 0 or rec.TotAmt > 999999999999.99:
                raise ValidationError(_('Gross amount out of range'))
    
    AssAmt = fields.Float("Taxable Amount")
    @api.constrains('AssAmt')
    def _check_ass_amt(self):
        for rec in self:
            if rec.AssAmt < 0 or rec.AssAmt > 999999999999.99:
                raise ValidationError(_('Taxable amount out of range'))
    
    GstRt = fields.Float("GST Rate")
    @api.constrains('GstRt')
    def _check_gst(self):
        for rec in self:
            if rec.GstRt < 0 or rec.GstRt > 999.999:
                raise ValidationError(_('GST rate out of range'))
    
    IgstAmt = fields.Float("Amount of IGST payable")
    @api.constrains('IgstAmt')
    def _check_Igst(self):
        for rec in self:
            if rec.IgstAmt < 0 or rec.IgstAmt > 999999999999.99:
                raise ValidationError(_('IGST amount out of range'))

    OthChrg = fields.Float("TCS")
    @api.constrains('OthChrg')
    def _check_tcs(self):
        for rec in self:
            if rec.OthChrg < 0 or rec.OthChrg > 999999999999.99:
                raise ValidationError(_('TCS amount out of range'))

    Discount = fields.Float("Discount")
    @api.constrains('Discount')
    def _check_discount(self):
        for rec in self:
            if rec.Discount < 0 or rec.Discount > 999999999999.99:
                raise ValidationError(_('Discount amount out of range'))
    
    CgstAmt = fields.Float("Amount of CGST payable")
    @api.constrains('CgstAmt')
    def _check_Cgst(self):
        for rec in self:
            if rec.CgstAmt < 0 or rec.CgstAmt > 999999999999.99:
                raise ValidationError(_('CGST amount out of range'))
    
    SgstAmt = fields.Float("Amount of SGST payable")
    @api.constrains('SgstAmt')
    def _check_Sgst(self):
        for rec in self:
            if rec.SgstAmt < 0 or rec.SgstAmt > 999999999999.99:
                raise ValidationError(_('SGST amount out of range'))
    
    TotItemVal = fields.Float("Total Value")
    @api.constrains('TotItemVal')
    def _check_total(self):
        for rec in self:
            if rec.TotItemVal < 0 or rec.TotItemVal > 999999999999.99:
                raise ValidationError(_('Total Value out of range'))
            
    