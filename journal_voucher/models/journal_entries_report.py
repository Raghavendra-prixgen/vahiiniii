from odoo.exceptions import UserError
from odoo import api, fields, models, _
from num2words import num2words
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from functools import partial

class accountjournal(models.Model):
	_inherit = 'account.move'


	def fetch_sale_order(self):
		address = self.env['res.partner']
		if self.invoice_line_ids:
			sale_order_ids = self.invoice_line_ids.sale_line_ids.mapped('order_id')
			if sale_order_ids:
				warehouse_address_id = sale_order_ids.mapped('y_warehouse_address_id')
				if warehouse_address_id:
					address = warehouse_address_id[:1]
			if not address:
				purchase_order_ids = self.invoice_line_ids.purchase_line_id.mapped('order_id')
				if purchase_order_ids:
					warehouse_address_id = purchase_order_ids.mapped('y_warehouse_address_id')
					if warehouse_address_id:
						address = warehouse_address_id[:1]
		if not address:
			address = self.company_id.partner_id
		
		return address
 
	def amount_in_words(self, amount):
			formatted_amount = "{:,.2f}".format(amount)
			amt = formatted_amount.split(".")
			amt[0] = amt[0].replace(",", "")
			currency = self.currency_id.currency_unit_label
			if int(amt[1]) > 0:
					second_part = currency + '' + " and " + num2words(int(amt[1]), lang='en_IN') + ' Paise only'
					remove_and_new = second_part.replace('.', " and ")
					remove_and_pro = remove_and_new.replace('-', ' ')
			else:
					second_part = 'only'
			
			first_part =  num2words(int(amt[0]), lang='en_IN').replace(' and', ' ')
			first_part_new = first_part.replace(',', '')
			first_part_pro = first_part_new.replace('-', ' ')
			if int(amt[1]) == 0:
					result = first_part_pro + ' '+ currency +' ' + second_part
			else:
					result = first_part_pro + ' ' + remove_and_pro
			results = ' '.join(word.capitalize() for word in result.split())
			final_result = results.replace('And', " and ")
			return final_result



	# def get_prepared_by(self):
	# 	rec = self.env['mail.message'].sudo().search([('model','=','account.move'),('res_id','=',self.id),('subtype_id','=',self.env.ref('account.mt_invoice_validated').id)])
	# 	if rec:
	# 		return rec.create_uid.name
	# 	else:
	# 		return ''


	def email_split(self,email):
		esplit=email.split(",")
		if esplit:
			current_name= ''
			for each_email in esplit:
				current_name +=each_email
			if len(current_name) >1:
				name = current_name

		return current_name

class accountjournal(models.Model):
	_inherit = 'account.move.line'

	def amt_in_words(self, amount):
		amount1=str(amount)
		amt= amount1.split(".")
		print(amt[1],amt[0],amount)
		if int(amt[1]) > 0:
			second_part = ' and '+ num2words(int(amt[1]), lang='en_IN') + ' Paise only '
			print(amt[1],'*****************************************************************')
		else:
			second_part = ' Only '

		return ' Rupees ' + num2words(int(amt[0]), lang='en_IN') + second_part

	


