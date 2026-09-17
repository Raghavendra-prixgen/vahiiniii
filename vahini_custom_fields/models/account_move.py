from odoo import models, fields, api, _
import json
from datetime import date, datetime
import statistics


class VahiniAccountMove(models.Model):
    _inherit='account.move'
    
    paid_date = fields.Date(string="Paid Date",compute="compute_paid_date",store=True)
    
 
    @api.depends('name','invoice_payments_widget')
    def compute_paid_date(self):
        for bill in self:
            bill.paid_date = False
            if bill.state == 'posted' and bill.invoice_payments_widget:
                payment_dict = bill.invoice_payments_widget
                if payment_dict:
                    em_list = []
                    for record in payment_dict.get('content'):
                        em_list.append(record.get('date'))
                    bill.paid_date = max(em_list)



# report apps-------------------------------
    y_confirmation_date = fields.Datetime(string='Confirmation Date')
    y_custom_po_no = fields.Char(string='PO No', store=True)
    y_po_date = fields.Date(String='PO Date', store=True)
    #Export related fields
    y_transporter = fields.Char(string="Dispatched Through")
    y_proforma_sequence = fields.Char(string="Proforma Invoice Number",readonly=True)
    y_delivered_to = fields.Char(string="Delivered To")

    y_farmer_share = fields.Float(string="Farmer Share", compute="compute_farmer_share")
    y_government_share = fields.Float(string="Government Share")
    y_custom_farmer_share = fields.Float(string="Farmer/Kisan Share")
 
    def compute_farmer_share(self):
        for rec in self:
            rec.y_farmer_share = rec.amount_total - rec.amount_residual

            
