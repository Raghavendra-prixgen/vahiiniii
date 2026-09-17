# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.tools.float_utils import float_round
from num2words import num2words
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'
        
    def get_packing_list_bags_box_data(self):
        box_bag = 0
        for line in self.invoice_line_ids:
            grn_stock_move = line.y_stock_move_id
            package_type = grn_stock_move.product_packaging_id
            if package_type.package_type_id.name == 'Bags' or package_type.package_type_id.name == 'Box':
                bags = line.quantity / package_type.qty if package_type.qty > 0 else 0 
                box_bag += bags
              
        return box_bag
    
        
    def get_packing_list_bundle_data(self):
        value = 0
        for line in self.invoice_line_ids:
            grn_stock_move = line.y_stock_move_id
            package_type = grn_stock_move.product_packaging_id
            if package_type.package_type_id.name == 'Bundle' :
                value += (line.quantity / package_type.qty if package_type.qty > 0 else 0 )
        return value
        
    def get_packing_list_water_tank_data(self):
        value = sum(self.invoice_line_ids.filtered(lambda x:x.y_category_id.y_name == 'WATERTANK').mapped('quantity'))
        return value
        
        
    def get_packing_list_length_data(self):
        value = sum(self.invoice_line_ids.filtered(lambda x:x.y_stock_move_id.product_packaging_id.package_type_id.name == 'Length').mapped('quantity'))
        return value
        
        
    def get_packing_list_roll_data(self):
        value = sum(self.invoice_line_ids.filtered(lambda x:x.y_stock_move_id.product_packaging_id.package_type_id.name == 'Rolls').mapped('quantity'))
        return value

        
    def fetch_invoice_warehouse_address(self):
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

    
    def tax_calculation_gst(self):
        all_taxes = {"taxes": []}
        for line in self.invoice_line_ids:
            y_category_id = line.y_category_id.y_name
            y_discount_amt = line.y_total_discount_amt  
            
            for each_line in line.tax_ids:
                taxes_res = each_line.compute_all(
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=self.partner_id,
                    price_unit=line.price_unit,
                    is_refund=False,
                )
                parent_tax_name = each_line.name
                parent_tax_group = each_line.tax_group_id.name
                parent_tax_amt = line.price_subtotal

                parent_tax_entry = next(
                    (
                        tax
                        for tax in all_taxes["taxes"]
                        if tax["parent_tax"] == parent_tax_name
                        and tax["y_category_id"] == y_category_id
                    ),
                    None,
                )

                if not parent_tax_entry:
                    parent_tax_entry = {
                        "parent_tax": parent_tax_name,
                        "parent_tax_group": parent_tax_group,
                        "parent_tax_amount": 0,
                        "child_taxes": {},
                        "y_category_id": y_category_id,
                        "price_subtotal": parent_tax_amt,
                        "y_total_discount_amt": 0,  # Initialize discount amount
                    }
                    all_taxes["taxes"].append(parent_tax_entry)

                parent_tax_entry["parent_tax_amount"] += float_round(
                    parent_tax_amt, precision_digits=2
                )
                parent_tax_entry["y_total_discount_amt"] += float_round(
                    y_discount_amt, precision_digits=2
                )

                for tax in taxes_res["taxes"]:
                    tax_id = tax["id"]
                    amount = tax["amount"]

                    tax_record = self.env["account.tax"].browse(tax_id)
                    tax_name = tax_record.name
                    tax_group = tax_record.tax_group_id.name
                    rate = tax_record.amount

                    if tax_id in parent_tax_entry["child_taxes"]:
                        parent_tax_entry["child_taxes"][tax_id][
                            "amount"
                        ] += float_round(amount, precision_digits=2)
                    else:
                        parent_tax_entry["child_taxes"][tax_id] = {
                            "tax_id": tax_id,
                            "name": tax_name,
                            "rate": rate,
                            "amount": float_round(amount, precision_digits=2),
                            "tax_group": tax_group,
                            "y_category_id": y_category_id,
                        }

        for parent_tax_entry in all_taxes["taxes"]:
            parent_tax_entry["child_taxes"] = list(
                parent_tax_entry["child_taxes"].values()
            )
        
        # The key fix - group by category name only
        final_categories = {}
        for tax in all_taxes["taxes"]:
            if tax.get("parent_tax_group") in ("IGST", "GST"):  # Filter only IGST and GST
                category = tax["y_category_id"]
                
                # Add new category if it doesn't exist yet
                if category not in final_categories:
                    final_categories[category] = {
                        "y_category_id": category,
                        "parent_tax_amount": 0,
                        "price_subtotal": 0,
                        "y_total_discount_amt": 0,  # Initialize discount in final categories
                        "child_taxes": []
                    }
                    
                # Add amounts
                final_categories[category]["parent_tax_amount"] += tax["parent_tax_amount"]
                final_categories[category]["price_subtotal"] += tax["price_subtotal"]
                final_categories[category]["y_total_discount_amt"] += tax["y_total_discount_amt"]  # Add discount amounts
                
                # Process child taxes
                for child in tax.get("child_taxes", []):
                    # Check if we already have this tax rate
                    existing = next((c for c in final_categories[category]["child_taxes"] if c["rate"] == child["rate"]), None)
                    if existing:
                        existing["amount"] += child["amount"]
                    else:
                        final_categories[category]["child_taxes"].append(child)
        
        # For INR currency, ensure we have both CGST and SGST with same rate
        for category, data in final_categories.items():
            if self.currency_id.name == 'INR' and data["child_taxes"] and len(data["child_taxes"]) == 1:
                # If there's only one tax entry and it's for INR, duplicate it for SGST
                cgst_entry = data["child_taxes"][0]
                sgst_entry = cgst_entry.copy()
                data["child_taxes"].append(sgst_entry)
        
        # Convert to list format
        result = {"taxes": list(final_categories.values())}
        print(result,"jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj")
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
        
        
# class CreditDebitPdfReport(models.AbstractModel):
#     _name = 'report.credit_debit_report.account_creditdebitnote_template'
#     _template = 'credit_debit_report.account_creditdebitnote_template'
#     _description = 'Credit Debit Report'
    
#     @api.model
#     def _get_report_values(self, docids, data=None):
#         docs = self.env['account.move'].browse(docids)        
#         if docs.state in ('draft'):
#             raise ValidationError("The Credit Note/Debit Note is in draft stage, Print can be taken only when the record is in Confirmed stage.")
        
#         return {
#             'doc_ids': docids,
#             'doc_model': 'account.move',
#             'docs': docs,
#             'data': data,
#         }

            
