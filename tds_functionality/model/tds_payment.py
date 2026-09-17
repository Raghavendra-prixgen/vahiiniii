from odoo.exceptions import ValidationError
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta,date
import json
import base64
class TdsPayment(models.Model):
    _name = "tds.payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "TDS Payment"
    _rec_name = "y_doc_no"

    def get_year_selection(self):
        current_year = datetime.now().year

        # Generate previous, current, next financial years
        years = []
        for year in range(current_year - 1, current_year + 1):
            fy = f"{year}-{year + 1}"
            years.append((fy, fy))

        return years
    y_month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string="Month")

    y_year = fields.Selection(
        selection=get_year_selection,
        string="Financial Year"
    )
    y_original = fields.Boolean(string="Original")
    y_reversed = fields.Boolean(string="Reversed")
    y_doc_no = fields.Char(string="Doc No")
    y_payment_ids = fields.Many2many('account.payment',string="Payment")

    y_state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),

    ],default='draft' ,string='State')

    y_tds_payment_line_ids = fields.One2many('tds.payment.line','y_tds_payment_id',string="TDS Payment Line")

    def action_post(self):
        for rec in self:
            if rec.y_state == 'draft':
                rec.write({'y_state':'posted'})

    def action_draft(self):
        for rec in self:
            if rec.y_state == 'posted':
                rec.write({'y_state':'draft'})
    
    
    def download_json_format(self):
        self.ensure_one()

        if not self.y_tds_payment_line_ids:
            raise ValidationError("No TDS Payment Lines found.")

        line = self.y_tds_payment_line_ids[0]  # Example: first line

        json_data = {
            "challanDetails": {
                "challanNumber": "ITNS 281N",
                "assessmentYear": "2026-27",
                "financialYear": self.y_year or "",
                "majorHeadCode": "0021",
                "minorHeadCode": "200",
                "tanNumber": "XYZD12345E"
            },
            "taxpayerInfo": {
                "name": "ABC Tech Solutions Pvt Ltd",
                "address": "123 MG Road",
                "city": "Tumkur",
                "state": "Karnataka",
                "pinCode": "572101"
            },
            "paymentDetails": {
                "natureOfPayment": line.y_tds_nature_id.y_name if line.y_tds_nature_id else "",
                "incomeTax": line.y_amount,
                "surcharge": 0.00,
                "educationCess": 0.00,
                "interest": 0.00,
                "penalty": 0.00,
                "totalAmount": line.y_amount
            },
            "bankAcknowledgement": {
                "cin": line.y_brc or "",
                "bsrCode": "",
                "challanSerialNumber": line.y_challan_no or "",
                "dateOfDeposit": "",
                "bankReferenceNumber": line.y_token_number or ""
            }
        }

        file_content = json.dumps(
            json_data,
            indent=4,
            ensure_ascii=False
        )

        attachment = self.env['ir.attachment'].create({
            'name': f'{self.y_doc_no}.json',
            'type': 'binary',
            'datas': base64.b64encode(file_content.encode('utf-8')),
            'mimetype': 'application/json',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['y_doc_no'] = self.env['ir.sequence'].next_by_code('tds.payment')
        return super(TdsPayment, self).create(vals_list)     

class TdsPaymentLine(models.Model):
    _name = "tds.payment.line"
    _description = "Tds Payment line"

    y_tds_payment_id = fields.Many2one('tds.payment',string="TDS Payment")
    # y_tds_nature_id = fields.Many2one('tds.nature',string="TDS nature")
    y_tds_nature_id = fields.Many2one('tax.code',string="Tax Code")
    y_tds_tax_ids = fields.Many2one('account.tax',string="TDS Tax")
    y_amount = fields.Float(string="Amount")
    y_brc = fields.Char(string="BRC")
    y_challan_no = fields.Char(string="Challan No")
    y_filling = fields.Boolean(string="Filling")
    y_token_number = fields.Char(string="Token number")
    y_matched = fields.Boolean(string="Matched")


    @api.onchange('y_tds_nature_id')
    def _onchange_y_tds_nature_id(self):
        self.y_tds_tax_ids = self.y_tds_nature_id.y_tax_ids if self.y_tds_nature_id else False

    @api.onchange('y_tds_tax_ids')
    def _onchange_y_tds_tax_ids(self):
        if self.y_tds_tax_ids and self.y_tds_tax_ids.y_tax_code:
            self.y_tds_nature_id = self.y_tds_tax_ids.y_tax_code

