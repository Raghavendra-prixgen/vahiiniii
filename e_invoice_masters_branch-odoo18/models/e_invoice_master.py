from odoo import api, fields, models, _
from odoo.exceptions import  UserError, ValidationError, AccessError
from datetime import date, datetime
import pdb
import logging
import json
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    type = fields.Selection(selection_add=
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ("private", "Private Address"),
         ("register", "Register Address"),
        ], string='Address Type',
        default='contact',
        help="Invoice & Delivery addresses are used in sales orders. Private addresses are only visible by authorized users.")
    
    supply_type = fields.Selection(
        [('B2B', 'B2B'),
         ('B2C','B2C'),
         ('SEZWP', 'SEZWP'),
         ('SEZWOP', 'SEZWOP'),
         ('EXPWP', 'EXPWP'),
         ("EXPWOP", "EXPWOP"),
         ("DEXP", "DEXP"),
        ], string='Supply Type',
        default='B2B',)
    
    owner_id = fields.Char()




class CountryState(models.Model):
    _inherit = 'res.country.state'

    gst_state_code= fields.Char("GST State Code")


class AccountMove(models.Model):
    _inherit = 'account.move'

    irn_id = fields.Many2one('irn.account.move')

    place_of_supply = fields.Many2one("res.country.state", string='Place of Supply', related="l10n_in_state_id",store=True)

    igst_on_intra = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No')],string='IGST on Intra',compute='get_igs_intra',stroe=True)
    

    transporter_id = fields.Char("Transporter Id", copy=False)
    transporter_name = fields.Char("Transporter Name", copy=False)
    transporter_mode = fields.Selection(
        [('1', 'Road'),
         ('2', 'Rail'),
         ('3', 'Air'),
         ('4', 'Ship')],string="Transporter Mode", copy=False)
    transporter_doc_num = fields.Char("Transporter Doc Number",copy=False)
    transporter_doc_date = fields.Date("Transporter Doc Date",copy=False)
    vehicle_number=  fields.Char("Vehicle Number",copy=False)
    # gstnin=  fields.Char("Vehicle Number")

    Irn=  fields.Char("IRN",  copy=False)
    AckDt=  fields.Datetime("AckDt", copy=False)
    CancelDate=  fields.Datetime("CancelDate", copy=False)
    AckNo=  fields.Char("AckNo",  copy=False)
    SignedQRCode=  fields.Binary("SignedQRCode",  copy=False)

    vehicle_type = fields.Selection(
        [('R', 'Regular'),
         ('O', 'ODC')],string='Vehicle Type',copy=False)
    distance = fields.Integer(default=1,copy=False)
    # copy=False, compute='_compute_qty_delivered', inverse='_inverse_qty_delivered', compute_sudo=True, store=True, digits='Product Unit of Measure', default=0.0)
    
    EwbNo = fields.Char("EwbNo", copy=False)
    EwbDt = fields.Datetime("EwbDt", copy=False)
    EwbValidTill = fields.Datetime("EwbValidTill", copy=False)
    Remarks = fields.Char("Remarks", copy=False)


    @api.depends('partner_id')
    def get_igs_intra(self):
        for each in self:
            if each.partner_id.supply_type:
                if each.partner_id.supply_type in ['SEZWP','SEZWOP']:

                    each.igst_on_intra='yes'
                else:
                    each.igst_on_intra = 'no'
            else:
                each.igst_on_intra = False

    # @api.onchange('place_of_supply')
    # def _inverse_get_igs_intra(self):
    #     for each in self:
    #         if each.place_of_supply:
    #             each.place_of_supply=each.place_of_supply.id
    #         else:
    #             each.place_of_supply = False


    def cancel_irn(self):

        for each in self:

            each.irn_id.cancel_irn()
    
    def generate_ewb(self):

        for each in self:

            each.irn_id.generate_e_way()

   

    def get_total_invoice_value(self):
        """
        Returns the total invoice value based on the currency.
        For INR currency, it returns the total amount of the invoice.
        For other currencies, it calculates the sum of the credit values from journal items
        based on the display_type of the line items.
        """
        self.ensure_one()
        if self.currency_id.name == 'INR':
            has_free_of_cost = any(line.y_is_free_of_charge_visible for line in self.invoice_line_ids)
        
            if not has_free_of_cost:
                return self.amount_total
            
            else:
            
                price_total = sum(self.invoice_line_ids.filtered(lambda x:x.display_type=='product').mapped('price_total'))
                if self.invoice_cash_rounding_id:
                    rounded_value = self.invoice_cash_rounding_id.round(price_total)
                else:
                    rounded_value = self.currency_id.round(price_total) 
                    
                return rounded_value
            
                                    
        else:
            credit_sum = sum(self.line_ids.filtered(lambda line: line.display_type == 'product').mapped('credit'))
            return credit_sum
        
    def get_assval(self):
        """
        Returns the total invoice value based on the currency.
        For INR currency, it returns the assval amount of the invoice.
        For other currencies, it calculates the sum of the credit values and amount_untaxed
        from journal items based on the display_type of the line items.
        """
        self.ensure_one()
        if self.currency_id.name == 'INR':
            rounding_value = self.line_ids.filtered(lambda x:x.display_type=='rounding')

            return self.amount_untaxed - rounding_value.credit if rounding_value.credit else self.amount_untaxed + rounding_value.debit
        else:
            total_sum = sum(
                line.credit
                for line in self.line_ids
                if line.display_type and line.display_type == 'product'
            )
            return total_sum
        
    def generate_irn(self):

        for each in self:
           
            if each.move_type == 'out_invoice' and not each.debit_origin_id:
                type_inv ='INV'
            elif each.move_type == 'out_refund':
                type_inv ='CRN'
            else:
                type_inv ='DBN'

            

            seller_gst = self.env.company.einv_gst_src
            seller_gst = each.company_id.partner_id
            rounding_value = self.line_ids.filtered(lambda x:x.display_type=='rounding')
            
            
            _logger.info("\n\n{}\n{}\n{}\n{}\n\n".format(seller_gst,seller_gst,seller_gst.vat,seller_gst.owner_id))
            irn_vals={

            'SupTyp': each.partner_id.supply_type,
            'Typ': type_inv,
            'TaxSch':'GST',
            'No' :each.name,
            'Dt': datetime.strftime( each.invoice_date,"%d/%m/%Y"),
            'owner_id': seller_gst.owner_id,
            'SellGstin': seller_gst.vat,
            'SellLglNm': seller_gst.name,
            'SellAddr1': seller_gst.street,
            'SellAddr2': seller_gst.street2,
            'SellLoc': seller_gst.city,
            'SellPin': seller_gst.zip,
            'SellStcd': int(seller_gst.state_id.l10n_in_tin) if seller_gst.state_id.l10n_in_tin else 0,


            'BuyGstin': each.partner_id.vat,
            'BuyLglNm':each.partner_id.name,
            'BuyAddr1':each.partner_id.street,
            'BuyAddr2':each.partner_id.street2,
            'BuyLoc': each.partner_id.city,
            'BuyPin': each.partner_id.zip,
            'BuyPos': each.place_of_supply.l10n_in_tin,
            'BuyStcd': int(each.partner_id.state_id.l10n_in_tin) if each.partner_id.state_id.l10n_in_tin else 0,
            'Assval' : round(each.get_assval(),2) ,
            'RndOffAmt': rounding_value.credit if rounding_value.credit else rounding_value.debit,
            'TotInvVal': round(each.get_total_invoice_value(),2),
            # 'RndOffAmt': round_off[0]['round'] if round_off else 0.0,
            'move_id': each.id,

            }
            
            new_id =self.env['irn.account.move'].create(irn_vals)
            sl_no=1
            inv_tot_isgt=0.0
            inv_tot_csgt=0.0
            inv_tot_tcs=0.0
            inv_tot_dis=0.0
            for each_line in each.invoice_line_ids:
               
                currency_rate = 1/each_line.currency_rate
                if each_line.product_id:
                    curr_val = each_line.price_subtotal
                    tot_rax_rate =0.0
                    tot_igst_rax_rate =0.0
                    igst_val =0.0
                    sgst_val =0.0
                    tcs_val =0.0
                    # cgst_val =0.0
                    for each_tax in each_line.tax_ids:
                        if each_tax.amount_type == 'group':
                            
                            if each_tax.tax_group_id.name == 'GST':
                                for each_group_line in  each_tax.children_tax_ids:
                                    if each_group_line.tax_group_id.name == 'SGST' or each_group_line.tax_group_id.name == 'CGST' :
                                        tot_rax_rate +=each_group_line.amount
                                        sgst_val =curr_val * (each_group_line.amount/100)
                                    elif each_group_line.tax_group_id.name == 'TCS':
                                        tcs_val = (curr_val+sgst_val*2) * (each_group_line.amount/100)
                            elif  each_tax.tax_group_id.name == 'IGST':
                                for each_group_line in  each_tax.children_tax_ids:
                                    if each_group_line.tax_group_id.name == 'IGST' :
                                        tot_rax_rate =each_group_line.amount
                                        igst_val =curr_val * (each_group_line.amount/100)
                                    elif each_group_line.tax_group_id.name == 'TCS':
                                        tcs_val = (curr_val+igst_val) * (each_group_line.amount/100)
                        else:
                            if each_tax.tax_group_id.name == 'IGST':
                                tot_rax_rate +=each_tax.amount
                                igst_val =curr_val * (each_tax.amount/100)
                            if each_tax.tax_group_id.name == 'TCS':
                                tcs_val = (curr_val+igst_val) * (each_tax.amount/100)

                    dis=((each_line.quantity*each_line.price_unit)*each_line.discount/100)* currency_rate
                    
                    product_list={
                    'SlNo': sl_no ,
                    'IsServc': 'Y' if each_line.product_id.type == 'service' else 'N',
                    'PrdDesc': each_line.name,
                    'HsnCd': each_line.product_id.l10n_in_hsn_code,
                    'Unit': each_line.product_id.uom_id.l10n_in_code.split('-')[0],
                    'UnitPrice': round((each_line.price_unit * currency_rate),2),
                    'Qty': each_line.quantity,
                    'TotAmt': round((each_line.quantity * (each_line.price_unit*currency_rate)),2),
                    'AssAmt': round((each_line.price_subtotal * currency_rate) , 2),
                    'GstRt': tot_rax_rate,
                    'IgstAmt':round(igst_val,2),
                    'CgstAmt':round(sgst_val,2),
                    'SgstAmt':round(sgst_val,2),
                    'OthChrg':round(tcs_val,2),
                    'Discount':round(dis,2) if dis else 0.0,
                    'TotItemVal': round(((each_line.price_total)*currency_rate),2) ,
                    
                    'irn_id': new_id.id
                    }
                    _logger.info("\n\n{}\n\n".format(product_list))
                    self.env['irn.account.move.line'].create(product_list)
                    sl_no +=1
                    inv_tot_csgt +=sgst_val
                    inv_tot_isgt +=igst_val
                    inv_tot_tcs +=tcs_val
                    inv_tot_dis +=dis
            new_id.write({
                        'IgstVal':round(inv_tot_isgt,2),
                        'SgstVal':round(inv_tot_csgt,2),
                        'CgstVal':round(inv_tot_csgt,2),
                        'OthChrg':round(inv_tot_tcs,2),
                        'Discount':round(inv_tot_dis,2),
                        })

            
            new_id.generate_irn()
            each.irn_id = new_id.id
               
class ResCompany(models.Model):
    _inherit='res.company'

    einv_engine = fields.Char(string="Einv Engine")
    Version = fields.Char(string="Schema Version")
    einv_engine_uname = fields.Char(string="Einv Engine Uname")
    einv_engine_pass = fields.Char(string="Einv Engine Pass")
    einv_server = fields.Selection([('sand','Sandbox'),('prod','Production')],default='sand', string="Einv Server")

