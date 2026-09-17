# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.float_utils import float_round
from datetime import datetime, timedelta,date
from num2words import num2words

class AccountMove(models.Model):
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

        if int(amt[1]) > 0:
            second_part = "and " + num2words(int(amt[1]), lang='en_IN') + ' Paise only'
            remove_and_new = second_part.replace('.', " and ")
            remove_and_pro = remove_and_new.replace('-', ' ')
        else:
            second_part = 'only'

        first_part = 'Rupees ' + num2words(int(amt[0]), lang='en_IN').replace(' and', ' ')
        first_part_new = first_part.replace(',', '')
        first_part_pro = first_part_new.replace('-', ' ')
        if int(amt[1]) == 0:
            result = first_part_pro + ' ' + second_part
        else:
            result = first_part_pro + ' ' + remove_and_pro
        results = ' '.join(word.capitalize() for word in result.split())
        final_result = results.replace('And', " and ")

        return result
    
    
    def roundoff_amount(self):
        rounding_amount = 0
        for line in self.line_ids:
            if line.display_type == 'rounding':
                rounding_amount = -(line.balance)
                rounding_amount = rounding_amount * self.invoice_currency_rate
            else:
                rounding_amount = 0
        return round(rounding_amount,2)
    
    # def tax_calculation(self):
    #     all_taxes = {"taxes": []}
    #     for line in self.invoice_line_ids:
    #         y_category_id = line.y_category_id.y_name
    #         for each_line in line.tax_ids:
    #             taxes_res = each_line.compute_all(
    #                 quantity=line.quantity,
    #                 currency=line.currency_id,
    #                 product=line.product_id,
    #                 partner=self.partner_id,
    #                 price_unit=line.price_unit,
    #                 is_refund=False,
    #             )
    #             parent_tax_name = each_line.name
    #             parent_tax_group = each_line.tax_group_id.name
    #             parent_tax_amt = line.price_subtotal

    #             parent_tax_entry = next(
    #                 (
    #                     tax
    #                     for tax in all_taxes["taxes"]
    #                     if tax["parent_tax"] == parent_tax_name
    #                     and tax["y_category_id"] == y_category_id
    #                 ),
    #                 None,
    #             )

    #             if not parent_tax_entry:
    #                 parent_tax_entry = {
    #                     "parent_tax": parent_tax_name,
    #                     "parent_tax_group": parent_tax_group,
    #                     "parent_tax_amount": 0,
    #                     "child_taxes": {},
    #                     "y_category_id": y_category_id,
    #                     "price_subtotal": parent_tax_amt,
    #             }
    #                 all_taxes["taxes"].append(parent_tax_entry)

    #             parent_tax_entry["parent_tax_amount"] += float_round(
    #                 parent_tax_amt, precision_digits=2
    #             )

    #             for tax in taxes_res["taxes"]:
    #                 tax_id = tax["id"]
    #                 amount = tax["amount"]

    #                 tax_record = self.env["account.tax"].browse(tax_id)
    #                 tax_name = tax_record.name
    #                 tax_group = tax_record.tax_group_id.name
    #                 rate = tax_record.amount

    #                 if tax_group in ["CGST", "SGST"]:  # Grouping CGST and SGST by rate
    #                     tax_key = f"{tax_group} {rate}%"

    #                     existing_tax_entry = next(
    #                         (t for t in all_taxes["taxes"] if t["parent_tax"] == tax_key), None
    #                     )

    #                     if not existing_tax_entry:
    #                         existing_tax_entry = {
    #                             "parent_tax": tax_key,
    #                             "parent_tax_group": tax_group,
    #                             "parent_tax_amount": 0,
    #                             "child_taxes": {},
    #                             "y_category_id": y_category_id,
    #                         }
    #                         all_taxes["taxes"].append(existing_tax_entry)

    #                     existing_tax_entry["parent_tax_amount"] += float_round(
    #                         amount, precision_digits=2
    #                     )

    #                 if tax_id in parent_tax_entry["child_taxes"]:
    #                     parent_tax_entry["child_taxes"][tax_id]["amount"] += float_round(amount, precision_digits=2)
    #                 else:
    #                     parent_tax_entry["child_taxes"][tax_id] = {
    #                         "tax_id": tax_id,
    #                         "name": tax_name,
    #                         "rate": rate,
    #                         "amount": float_round(amount, precision_digits=2),
    #                         "tax_group": tax_group,
    #                         "y_category_id": y_category_id,
    #                     }

    #     for parent_tax_entry in all_taxes["taxes"]:
    #         parent_tax_entry["child_taxes"] = list(parent_tax_entry["child_taxes"].values())

    #     return all_taxes
