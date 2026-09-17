from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_utils, float_compare
from datetime import datetime
from lxml import html
import requests
from pprint import pprint



class AccMoveSMSInteg(models.Model):
	_inherit = "account.move"



	def send_message(self, sid, key_id, token, sms_to, sms_body):
			print("I'm From Send", "\n"*25)
			return requests.post('https://{}:{}@api.exotel.com/v1/Accounts/{}/Sms/send?From=VAHTMK&To={}& Body=Dear {} Your order has been dispatched Invoice number {} Invoice value {} Driver Number {} Thanks %26 Regards from Vahini Irrigation Pvt. Ltd.'.format(key_id, token, sid,sms_to, sms_body[0], sms_body[1], sms_body[2], sms_body[3]),	)

	def action_post(self):
		res = super(AccMoveSMSInteg, self).action_post()

		if self.move_type == "out_invoice" or self.state == "draft" :
			for rec in self: 
					sms_to = rec.partner_id.mobile
					
					sms_body = [ rec.partner_id.name, rec.name]
					sid = 'vahiniirrigation1'
					key_id = 'b88ccebbb1d2880834ac897e43f8d620cd94401bb4922b8e'
					token = 'da9cc35da599dea155b6662dad93855cdd224b20cb7c68fc'
					sms_from = '08069455075'
					
					varx = self.send_message( sid, key_id, token, sms_to ,sms_body)

					#start log code here
					self.message_post(body=_("SMS sent to {}".format(rec.partner_id.mobile)))

			
			return res

