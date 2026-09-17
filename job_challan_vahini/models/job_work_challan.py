from odoo.exceptions import UserError
from odoo import api, fields, models, _
from num2words import num2words
from odoo.exceptions import UserError, AccessError
import pdb

class saleorderdelivery(models.Model):
    _inherit = 'equipment.request.delivery'



    def get_transportation_details(self):
        doc_dict = {
            'request_no': '',
            'jobwork_challan_no': '',
        }

        maintenance_requests = self.equipment_request_line_ids.mapped('maintenance_request_id')

        if maintenance_requests:
            doc_dict['request_no'] = ", ".join(
                maintenance_requests.mapped('name')
            )

            doc_dict['jobwork_challan_no'] = ", ".join(
                maintenance_requests.mapped('jobwork_challan_no')
            )

        return doc_dict

    
    def amt_in_words_do(self, doamount):
        amount1=str(doamount)
        amt= amount1.split(".")
        if int(amt[1]) > 0:
            second_part = ' and '+ num2words(int(amt[1]), lang='en_IN') + ' Paise only '
        else:
            second_part = ' Only '
        return ' Rupees ' + num2words(int(amt[0]), lang='en_IN') + second_part

    def email_split(self,email):
        esplit=email.split(",")
        if esplit:
            current_name= ''
            for each_email in esplit:
                current_name +=each_email			
        return current_name



class deliveryorder(models.Model):
    _inherit = 'equipment.request.delivery'

    y_vehicle_no = fields.Char(string="Vehicle No")
    y_transporter = fields.Char(string="Transporter")
    y_customer_id = fields.Many2one('res.partner',string="Vendor",store=True)

    # -----------------------------------------------------------
    # 3. New field: Dispatch From -> res.partner, no create/edit
    # -----------------------------------------------------------
    y_dispatch_from_id = fields.Many2one(
        'res.partner',
        string="Dispatch From",tracking=True,
    )


    def email_split(self,email):
        esplit=email.split(",")
        if esplit:
            current_name= ''
            for each_email in esplit:
                current_name +=each_email
        return current_name

class PurchaseOrder(models.Model):
    _inherit = 'res.partner'
    
    def email_split(self,email):
        esplit=email.split(",")
        if esplit:
            current_name= ''
            for each_email in esplit:
                current_name +=each_email
            if len(current_name) >1:
                name = current_name

        return current_name
    

