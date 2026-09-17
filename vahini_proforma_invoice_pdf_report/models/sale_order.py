# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from num2words import num2words


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    def fetch_warehouse_address(self):
        address = self.env['res.partner']
        if self.y_warehouse_address_id:
            address = self.y_warehouse_address_id
        if not address:
            address = self.company_id.partner_id
        return address

    def amount_in_words(self, amount):
        formatted_amount = "{:,.2f}".format(amount)
        amt = formatted_amount.split(".")
        amt[0] = amt[0].replace(",", "")

        currency = self.currency_id.currency_unit_label

        if int(amt[1]) > 0:
            second_part = (
                currency
                + ""
                + " and "
                + num2words(int(amt[1]), lang="en_IN")
                + " Paise only"
            )
            remove_and_new = second_part.replace(".", " and ")
            remove_and_pro = remove_and_new.replace("-", " ")
        else:
            second_part = "only"

        first_part = num2words(int(amt[0]), lang="en_IN").replace(" and", " ")
        first_part_new = first_part.replace(",", "")

        first_part_pro = first_part_new.replace("-", " ")
        if int(amt[1]) == 0:
            result = first_part_pro + " " + currency + " " + second_part
        else:
            result = first_part_pro + " " + remove_and_pro
        results = " ".join(word.capitalize() for word in result.split())
        final_result = results.replace("And", " and ")

        return final_result