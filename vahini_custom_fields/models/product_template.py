from datetime import datetime
import json
from odoo import api, fields, models, tools, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    y_min_thickness = fields.Float(string="Minimum Thickness")
    y_max_thickness = fields.Float(string="Maximum Thickness")
    y_prod_length = fields.Float(string="Length")
    y_retail_print_product = fields.Boolean (help='The Product which should be Print Separately',string = "Retail Print Product")

 
class ResPartner(models.Model):
    _inherit = 'res.partner'

    y_average_collection_days = fields.Integer(string="Average collection days",group_operator='avg')
   
    def action_calculate_average_collection_days(self):
        for rec in self:
            payment_diff_list = []
            invoice_ids = rec.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted' and inv.payment_state != 'not_paid')
            for invoice in invoice_ids:
                invoice_date = invoice.invoice_date
                payment_dict = json.loads(invoice.invoice_payments_widget)
                if payment_dict:
                    em_list = []
                    for record in payment_dict.get('content'):
                        em_list.append(record.get('date'))
                    payment_date = max(em_list)
                    latest_payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
                    payment_diff = (latest_payment_date - invoice_date).days
                    payment_diff_list.append(payment_diff)
            if payment_diff_list:
                payment_average = sum(payment_diff_list) / len(payment_diff_list)
                rec.y_average_collection_days = payment_average
            else:
                rec.y_average_collection_days = 0


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(ResPartner, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        for rec in res:
            if rec.get('__domain', False):
                recs = self.search(rec['__domain'])
                total_due = 0.0
                for row in recs:
                    total_due = total_due + row.total_due
                rec['total_due'] = total_due
                total_overdue = 0.0
                for row in recs:
                    total_overdue = total_overdue + row.total_overdue
                rec['total_overdue'] = total_overdue
        return res

    class ProductProduct(models.Model):
        _inherit = 'product.product'

        y_retail_print_product = fields.Boolean (help='The Product which should be Print Separately',related='product_tmpl_id.y_retail_print_product',string = "Retail Print Product")


