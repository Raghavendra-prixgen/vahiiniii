import io
import re
import json
import base64
import qrcode
import requests
import odoorpc
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import  UserError, ValidationError, AccessError
# import pdb

import logging
_logger = logging.getLogger(__name__)


class AccountMoveIrn(models.Model):
    _name = "irn.account.move"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Journal Entries Irn"

    miscnt = fields.Integer(default=0)

    sto_id = fields.Many2one('stock.picking')

    move_id = fields.Many2one('account.move')
    name = fields.Char(related='move_id.name')
    
    Version = fields.Char("Version of the schema",
                default=lambda self: self.env.company.Version)
    @api.constrains('Version')
    def _check_version(self):
        for rec in self:
            version_len = len(rec.Version or '')
            if version_len < 1 or version_len > 6:
                raise ValidationError(_('Version name does not match expected format'))
    
    
    Irn = fields.Char("IRN", help="Invoice Reference Number")
    @api.constrains('Irn')
    def _check_irn(self):
        for rec in self:
            if len(rec.Irn or '') != 64:
                raise ValidationError(_('IRN number does not match expected format'))
    

    #TranDtls Transaction Details
    TaxSch = fields.Char("Tax Scheme", help="GST- Goods and Services Tax Scheme")
    @api.constrains('TaxSch')
    def _check_tax_sch(self):
        for rec in self:
            tax_len = len(rec.TaxSch or '')
            if tax_len < 3 or tax_len > 10:
                raise ValidationError(_('Tax Scheme name does not match expected format'))
    
    
    SupTypeOptions = [
        ('B2C', 'B2C'),
        ('B2B', 'B2B'),
        ('SEZWP', 'SEZWP'),
        ('SEZWOP', 'SEZWOP'),
        ('EXPWP', 'EXPWP'),
        ('EXPWOP', 'EXPWOP'),
        ('DEXP', 'DEXP')]
    SupTyp = fields.Selection(string="Supply Type", help="Type of Supply", selection=SupTypeOptions)

    
    #DocDtls Document Details
    DocTypOptions = [
        ('INV','INV'),
        ('CRN','CRN'),
        ('DBN','DBN')]
    Typ = fields.Selection(string="Document Type", help="Type of Document", selection=DocTypOptions)
    @api.constrains('Typ')
    def _check_typ(self):
        for rec in self:
            if len(rec.Typ or '') != 3:
                raise ValidationError(_('Document Type name does not match expected format'))

    No = fields.Char("Document Number")
    @api.constrains('No')
    def _check_doc_no(self):
        for rec in self:
            no_len = len(rec.No or '')
            if no_len < 1 or no_len > 16:
                raise ValidationError(_('Document Number does not match expected format'))
    
    Dt = fields.Char("Document Date")
    @api.constrains('Dt')
    def _check_doc_dt(self):
        exp = re.compile(r"^[0-3][0-9]/[0-1][0-9]/[2][0][1-2][0-9]$")
        for rec in self:
            if len(rec.Dt or '') != 10 or exp.match(rec.Dt) == None:
                raise ValidationError(_('Document Date does not match expected format'))


    
    #Seller Details
    owner_id = fields.Char()

    SellGstin = fields.Char("Seller GSTIN", help="GSTIN of supplier")
    @api.constrains('SellGstin')
    def _check_seller_gstin(self):
        for rec in self:
            if len(rec.SellGstin or '') != 15:
                raise ValidationError(_('Seller GSTIN does not match expected format'))
    
    SellLglNm = fields.Char("Seller Legal Name")
    @api.constrains('SellLglNm')
    def _check_seller_lglnm(self):
        for rec in self:
            lgl_len = len(rec.SellLglNm or '')
            if lgl_len < 3 or lgl_len > 100:
                raise ValidationError(_('Seller Legal Name does not match expected format'))
    
    SellAddr1 = fields.Char("Seller Address Line 1", help="Building/Flat no, Road/Street")
    @api.constrains('SellAddr1')
    def _check_seller_addr1(self):
        for rec in self:
            addr1_len = len(rec.SellAddr1 or '')
            if addr1_len < 3 or addr1_len > 100:
                # import pdb
                # pdb.set_trace()
                raise ValidationError(_('Seller Address Line 1 does not match expected format'))
    
    SellAddr2 = fields.Char("Seller Address Line 2", help="Floor no., Name of the premises/building")
    @api.constrains('SellAddr2')
    def _check_seller_addr2(self):
        for rec in self:
            addr2_len = len(rec.SellAddr2 or '')
            if addr2_len < 3 or addr2_len > 100 and rec.SellAddr2:
                raise ValidationError(_('Seller Address Line 2 does not match expected format'))
    
    SellLoc = fields.Char("Seller Location")
    @api.constrains('SellLoc')
    def _check_seller_loc(self):
        for rec in self:
            rec_len = len(rec.SellLoc or '')
            if rec_len < 3 or rec_len > 50:
                raise ValidationError(_('Seller Location does not match expected format'))
    
    SellPin = fields.Integer("Seller Pincode")
    @api.constrains('SellPin')
    def _check_seller_pin(self):
        for rec in self:
            if rec.SellPin < 100000 or rec.SellPin > 999999:
                raise ValidationError(_('Seller Pincode does not match expected format'))
    
    SellStcd = fields.Char("Seller State Code")
    @api.constrains('SellStcd')
    def _check_seller_stdc(self):
        for rec in self:
            stdc_len = len(rec.SellStcd or '')
            if stdc_len < 1 or stdc_len > 2:
                raise ValidationError(_('Seller State Code does not match expected format'))
    


    
    #Buyer Details
    BuyGstin = fields.Char("Buyer GSTIN", help="GSTIN of buyer")
    @api.constrains('BuyGstin')
    def _check_buyer_gstin(self):
        for rec in self:
            if len(rec.BuyGstin or '') != 15 and rec.SupTyp not in ['EXPWP','EXPWOP','DEXP','B2C']:
                raise ValidationError(_('Buyer GSTIN does not match expected format'))
    
    BuyLglNm = fields.Char("Buyer Legal Name")
    @api.constrains('BuyLglNm')
    def _check_buyer_lglnm(self):
        for rec in self:
            lgl_len = len(rec.BuyLglNm or '')
            if lgl_len < 3 or lgl_len > 100:
                raise ValidationError(_('Buyer Legal Name does not match expected format'))
    
    BuyPos = fields.Char("Buyer Place of Supply")
    @api.constrains('BuyPos')
    def _check_buyer_pos(self):
        for rec in self:
            pos_len = len(rec.BuyPos or '')
            if pos_len < 1 or pos_len > 2:
                raise ValidationError(_('Buyer Place of Supply does not match expected format'))
    
    BuyAddr1 = fields.Char("Buyer Address Line 1", help="Building/Flat no, Road/Street")
    @api.constrains('BuyAddr1')
    def _check_buyer_addr1(self):
        for rec in self:
            addr1_len = len(rec.BuyAddr1 or '')
            if addr1_len < 3 or addr1_len > 100:
                raise ValidationError(_('Buyer Address Line 1 does not match expected format'))
    
    BuyAddr2 = fields.Char("Buyer Address Line 2", help="Floor no., Name of the premises/building")
    @api.constrains('BuyAddr2')
    def _check_buyer_addr2(self):
        for rec in self:
            addr2_len = len(rec.BuyAddr2 or '')
            if addr2_len < 3 or addr2_len > 100 and rec.BuyAddr2:
                raise ValidationError(_('Buyer Address Line 2 does not match expected format'))
    
    BuyLoc = fields.Char("Buyer Location")
    @api.constrains('BuyLoc')
    def _check_buyer_loc(self):
        for rec in self:
            rec_len = len(rec.BuyLoc or '')
            if rec_len < 3 or rec_len > 50:
                raise ValidationError(_('Buyer Location does not match expected format'))
    
    BuyPin = fields.Integer("Buyer Pincode")
    @api.constrains('BuyPin')
    def _check_buyer_pin(self):
        for rec in self:
            if rec.BuyPin < 100000 or rec.BuyPin > 999999:
                raise ValidationError(_('Buyer Pincode does not match expected format'))
    
    BuyStcd = fields.Char("Buyer State Code")
    @api.constrains('BuyStcd')
    def _check_buyer_stdc(self):
        for rec in self:
            stdc_len = len(rec.BuyStcd or '')
            if stdc_len < 1 or stdc_len > 2:
                raise ValidationError(_('Buyer State Code does not match expected format'))
    



    ItemList = fields.One2many('irn.account.move.line','irn_id')


    #Value Details
    Assval = fields.Float("Assessable value", help="Total Assessable value of all items")
    @api.constrains('Assval')
    def _check_assval(self):
        for rec in self:
            if rec.Assval < 0 or rec.Assval > 99999999999999.99:
                raise ValidationError(_('Assessable value out of range'))
    
    CgstVal = fields.Float("Total CGST value of all items")
    @api.constrains('CgstVal')
    def _check_Igst(self):
        for rec in self:
            if rec.CgstVal < 0 or rec.CgstVal > 999999999999.99:
                raise ValidationError(_('IGST amount out of range'))
    
    SgstVal = fields.Float("Total SGST value of all items")
    @api.constrains('SgstVal')
    def _check_Cgst(self):
        for rec in self:
            if rec.SgstVal < 0 or rec.SgstVal > 999999999999.99:
                raise ValidationError(_('CGST amount out of range'))

    OthChrg = fields.Float("Total TCS value of all items")
    @api.constrains('OthChrg')
    def _check_tcs(self):
        for rec in self:
            if rec.OthChrg < 0 or rec.OthChrg > 999999999999.99:
                raise ValidationError(_('TCS amount out of range'))

    Discount = fields.Float("Total Discount value of all items")
    @api.constrains('Discount')
    def _check_dis(self):
        for rec in self:
            if rec.Discount < 0 or rec.Discount > 999999999999.99:
                raise ValidationError(_('Discount amount out of range'))
    
    IgstVal = fields.Float("Total IGST value of all items")
    @api.constrains('IgstVal')
    def _check_Sgst(self):
        for rec in self:
            if rec.IgstVal < 0 or rec.IgstVal > 999999999999.99:
                raise ValidationError(_('SGST amount out of range'))
    
    RndOffAmt = fields.Float("Rounded Off Amt")
    @api.constrains('RndOffAmt')
    def _check_rndoff(self):
        for rec in self:
            if rec.RndOffAmt < -99.99 or rec.RndOffAmt > 99.99:
                raise ValidationError(_('Round off amount out of range'))
    
    TotInvVal = fields.Float("Total value", help="Final Invoice value")
    @api.constrains('TotInvVal')
    def _check_total(self):
        for rec in self:
            if rec.TotInvVal < 0 or rec.TotInvVal > 99999999999999.99:
                raise ValidationError(_('Final Invoice value out of range'))
    
    # fields for E-way Bill 
    TransId = fields.Char("Transporter Id")
    TransName = fields.Char("Transporter Name")
    TransMode = fields.Char("Transporter Mode")
    Distance = fields.Float("Distance")
    TransDocNo = fields.Char("Transporter Doc Number")
    TransDocDt = fields.Char("Transporter Doc Date")
    VehNo = fields.Char("Vehicle No")
    VehType = fields.Char("Vehicle Type")
    def _generate_qr_code(self, qr_string):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
    
        img = qr.make_image()
        temp = io.BytesIO()
        img.save(temp, format="PNG")
        return base64.b64encode(temp.getvalue())
    

    def generate_b2c_qr(self):
        self.move_id.b2c_qr = self._generate_qr_code(self._prepare_json())
        

    download_json_data = fields.Binary()
    def generate_json(self):
        self.download_json_data = base64.encodestring(json.dumps(self._prepare_json()).encode('utf-8'))
        query = """update ir_attachment set mimetype = 'application/json' where 
        res_model = 'irn.account.move' and res_field = 'download_json_data' and res_id = %s"""
        self.env.cr.execute(query%(self.id))
    
    upload_json_data = fields.Binary()
    @api.onchange('upload_json_data')
    def process_upload_json_data(self):
        json_data = json.loads(base64.decodebytes(self.upload_json_data).decode('utf-8'))

        self.move_id.AckNo = json_data['AckNo']
        self.move_id.AckDt = datetime.strptime(json_data['AckDt'],"%Y-%m-%d %H:%M:%S")
        self.move_id.Irn = json_data['Irn']
        self.move_id.SignedQRCode = self._generate_qr_code(json_data['SignedQRCode'])

    def _save_irn_fields(self, record, gov):
        """Reusable helper to save IRN response fields."""
        record.AckNo = gov.get('AckNo')
        ack_dt = gov.get('AckDt')
        if ack_dt:
            record.AckDt = datetime.strptime(ack_dt, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
        record.Irn = gov.get('Irn')
        signed_qr = gov.get('SignedQRCode')
        if signed_qr:
            record.SignedQRCode = self._generate_qr_code(signed_qr)

    def generate_irn(self):
        server = self.env.company.einv_server
        odoo = odoorpc.ODOO('e-invoice-production1.odoo.com', protocol='jsonrpc+ssl', port=443) if server == 'prod' else \
            odoorpc.ODOO('prixgen-sandbox.odoo.com', protocol='jsonrpc+ssl', port=443)
        pxn_uname = self.env.company.einv_engine_uname
        pxn_pwd = self.env.company.einv_engine_pass
        pxn_srvr = self.env.company.einv_engine
        auth = {'miscnt': self.miscnt, 'txn_key': self.owner_id}
        data = self._prepare_json()
        odoo.login(pxn_srvr, pxn_uname, pxn_pwd)
        response = odoo.execute('einvoicing.transaction.manager', 'get_irn', [], {'auth': auth, 'data': data})

        _logger.info("{} response Received from irn".format(response))
        if response.get('Success'):

            gov = response.get('GovResponse') or {}
            self._save_irn_fields(self.move_id, gov)
            return

        gov = response.get('GovResponse') or {}
        error_details = gov.get('ErrorDetails') or []
        error_codes = [str(e.get('ErrorCode', '')) for e in error_details]

        if '2150' in error_codes:
            info_dtls = gov.get('InfoDtls') or []
            irn_info = next(
                (i for i in info_dtls if i.get('InfCd') == 'DUPIRN'),
                None
            )
            if irn_info:
                desc = irn_info.get('Desc') or {}  # ← unwrap 'Desc'
                self.move_id.AckNo = desc.get('AckNo')
                ack_dt = desc.get('AckDt')
                if ack_dt:
                    self.move_id.AckDt = datetime.strptime(ack_dt, "%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
                irn_val = desc.get('Irn')
                if irn_val:
                    self.move_id.Irn = irn_val
                    self.move_id.SignedQRCode = self._generate_qr_code(irn_val)
                return
            else:
                raise ValidationError(_(
                    "Duplicate IRN (2150) but InfoDtls missing from response.\n\nGov Response:\n{}".format(str(gov))
                ))

        raise ValidationError(_(
            "Payload\n{}\n\neInvoicing Error\n{}\n\nGov Response\n{}".format(
                data, response.get('Error'), str(gov)
            )
        ))
        

    

    

    def cancel_irn(self):
        server = self.env.company.einv_server
        odoo = odoorpc.ODOO('e-invoice-production1.odoo.com', protocol='jsonrpc+ssl', port=443) if server == 'prod' else\
            odoorpc.ODOO('prixgen-sandbox.odoo.com', protocol='jsonrpc+ssl', port=443)
        pxn_uname = self.env.company.einv_engine_uname
        pxn_pwd = self.env.company.einv_engine_pass
        pxn_srvr = self.env.company.einv_engine
        auth = {'miscnt':self.miscnt,'txn_key':self.owner_id}
        data = self._prepare_cancel()
        odoo.login(pxn_srvr,pxn_uname,pxn_pwd)
        response = odoo.execute('einvoicing.transaction.manager','cancel_irn',[],{'auth':auth,'data':data})
        if response.get('Success'):
            response = response.get('GovResponse')
            self.move_id.CancelDate = datetime.strptime(response.get('CancelDate'),"%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
            self.move_id.Irn = "(CANCELLED)" + response.get('Irn')
        
        else:
            raise ValidationError(_("""Payload\n{}\n\neInvoicing Error\n{}\n\nGov Response\n{}""".format(data,response.get('Error'),str(response.get('GovResponse') or ''))))
    
    def generate_sto_irn(self):
        server = self.env.company.einv_server
        odoo = odoorpc.ODOO('e-invoice-production1.odoo.com', protocol='jsonrpc+ssl', port=443) if server == 'prod' else\
            odoorpc.ODOO('prixgen-sandbox.odoo.com', protocol='jsonrpc+ssl', port=443)
        pxn_uname = self.env.company.einv_engine_uname
        pxn_pwd = self.env.company.einv_engine_pass
        pxn_srvr = self.env.company.einv_engine
        auth = {'miscnt':self.miscnt,'txn_key':self.owner_id}
        data = self._prepare_json()
        odoo.login(pxn_srvr,pxn_uname,pxn_pwd)
        response = odoo.execute('einvoicing.transaction.manager','get_irn',[],{'auth':auth,'data':data})
        if response.get('Success'):
            response = response.get('GovResponse')
            self.sto_id.AckNo = response.get('AckNo')
            # self.sto_id.e_way_billno = response.get('EwbNo') if response.get('EwbNo') else " "
            self.sto_id.AckDt = datetime.strptime(response.get('AckDt'),"%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
            self.sto_id.Irn = response.get('Irn')
            self.sto_id.SignedQRCode = self._generate_qr_code(response.get('SignedQRCode'))
        
        else:
            raise ValidationError(_("""Payload\n{}\n\neInvoicing Error\n{}\n\nGov Response\n{}""".format(data,response.get('Error'),str(response.get('GovResponse') or ''))))
    
    def generate_e_way(self):
        server = self.env.company.einv_server
        odoo = odoorpc.ODOO('e-invoice-production1.odoo.com', protocol='jsonrpc+ssl', port=443) if server == 'prod' else\
            odoorpc.ODOO('prixgen-sandbox.odoo.com', protocol='jsonrpc+ssl', port=443)
        pxn_uname = self.env.company.einv_engine_uname
        pxn_pwd = self.env.company.einv_engine_pass
        pxn_srvr = self.env.company.einv_engine
        auth = {'miscnt':self.miscnt,'txn_key':self.owner_id}
        data = self._prepare_e_way()
        odoo.login(pxn_srvr,pxn_uname,pxn_pwd)
        response = odoo.execute('einvoicing.transaction.manager','get_ewb',[],{'auth':auth,'data':data})
        if response.get('Success'):
            response = response.get('GovResponse')
            self.move_id.EwbNo = response.get('EwbNo')
            self.move_id.EwbDt = datetime.strptime(response.get('EwbDt'),"%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
            self.move_id.EwbValidTill = datetime.strptime(response.get('EwbValidTill'),"%Y-%m-%d %H:%M:%S") - timedelta(hours=5.5)
            self.move_id.Remarks = response.get('Remarks')
        else:
            raise ValidationError(_("""Payload\n{}\n\neWaybill Error\n{}\n\nGov Response\n{}""".format(data,response.get('Error'),str(response.get('GovResponse') or ''))))


    def _prepare_cancel(self):
        irn = self.move_id.Irn or ""
        if not irn:
            raise ValidationError(_("""No Irn on this doc"""))
        return {
            "Irn": irn,
            "CnlRsn":"1",
            "CnlRem":"Wrong entry"
        }


    def _prepare_json(self):
        
        if self.SupTyp == 'B2C':
            return {
                # "Version":self.Version or None,
                # "TranDtls":{
                #     "TaxSch":self.TaxSch or None,
                #     "SupTyp":self.SupTyp or None
                # },
                "DocDtls":{
                    "Typ":self.Typ or None,
                    "No":self.No or None,
                    "Dt":self.Dt or None
                },
                "SellerDtls":{
                    "Gstin":self.SellGstin or None,
                    "LglNm":self.SellLglNm or None,
                    "Addr1":self.SellAddr1 or None,
                    "Addr2":self.SellAddr2 or None,
                    "Loc":self.SellLoc or None,
                    "Pin":self.SellPin or None,
                    "Stcd":self.SellStcd or None
                },
                "BuyerDtls":{
                    # "Gstin":self.BuyGstin or "URP",
                    "LglNm":self.BuyLglNm or None,
                    # "Pos":self.BuyPos or None,
                    # "Addr1":self.BuyAddr1 or None,
                    # "Addr2":self.BuyAddr2 or None,
                    # "Loc":self.BuyLoc or None,
                    # "Pin":self.BuyPin or None,
                    # "Stcd":self.BuyStcd or None
                },

                "ItemList":[{
                    "SlNo":item.SlNo or None,
                    "IsServc":item.IsServc or None,
                    # "ItemDesc": item.ItemDesc or None,
                    "PrdDesc": item.PrdDesc or None,
                    "HsnCd":item.HsnCd or None,
                    "Qty":item.Qty or 0.0,
                    "Unit":item.Unit or None,
                    "UnitPrice":item.UnitPrice or None,
                    "TotAmt":item.TotAmt or 0.0,
                    "AssAmt":item.AssAmt or 0.0,
                    "GstRt":item.GstRt or 0.0,
                    # "IgstAmt":item.IgstAmt or 0.0,
                    "CgstAmt":item.CgstAmt or 0.0,
                    "SgstAmt":item.SgstAmt or 0.0,
                    "OthChrg":item.OthChrg or 0.0,
                    "Discount":item.Discount or 0.0,
                    "TotItemVal":item.TotItemVal or 0.0
                } for item in self.ItemList],
                "ValDtls":{
                    "AssVal":self.Assval or 0.0,
                    "CgstVal":self.CgstVal or 0.0,
                    "SgstVal":self.SgstVal or 0.0,
                    # "IgstVal":self.IgstVal or 0.0,
                    "RndOffAmt":self.RndOffAmt or 0.0,
                    "TotInvVal":self.TotInvVal or 0.0
                }
            }
            
        else:
            return {
                "Version":self.Version or None,
                "TranDtls":{
                    "TaxSch":self.TaxSch or None,
                    "SupTyp":self.SupTyp or None
                },
                "DocDtls":{
                    "Typ":self.Typ or None,
                    "No":self.No or None,
                    "Dt":self.Dt or None
                },
                "SellerDtls":{
                    "Gstin":self.SellGstin or None,
                    "LglNm":self.SellLglNm or None,
                    "Addr1":self.SellAddr1 or None,
                    "Addr2":self.SellAddr2 or None,
                    "Loc":self.SellLoc or None,
                    "Pin":self.SellPin or None,
                    "Stcd":self.SellStcd or None
                },
                "BuyerDtls":{
                    "Gstin":self.BuyGstin or "URP",
                    "LglNm":self.BuyLglNm or None,
                    "Pos":self.BuyPos or None,
                    "Addr1":self.BuyAddr1 or None,
                    "Addr2":self.BuyAddr2 or None,
                    "Loc":self.BuyLoc or None,
                    "Pin":self.BuyPin or None,
                    "Stcd":self.BuyStcd or None
                },
                "ShipDtls": {
                    "Gstin": self.move_id.partner_shipping_id.vat or "URP",
                    "LglNm": self.move_id.partner_shipping_id.name or None,
                    "TrdNm": None,
                    "Addr1": self.move_id.partner_shipping_id.street or None,
                    "Addr2": self.move_id.partner_shipping_id.street2 or None,
                    "Loc": self.move_id.partner_shipping_id.city or None,
                    "Pin": self.move_id.partner_shipping_id.zip or None,
                    "Stcd": self.move_id.partner_shipping_id.state_id.l10n_in_tin or None
                  },
                "ItemList":[{
                    "SlNo":item.SlNo or None,
                    "IsServc":item.IsServc or None,
                    # "ItemDesc": item.ItemDesc or None,
                    "PrdDesc": item.PrdDesc or None,
                    "HsnCd":item.HsnCd or None,
                    "Qty":item.Qty or 0.0,
                    "Unit":item.Unit or None,
                    "UnitPrice":item.UnitPrice or None,
                    "TotAmt":item.TotAmt or 0.0,
                    "AssAmt":item.AssAmt or 0.0,
                    "GstRt":item.GstRt or 0.0,
                    "IgstAmt":item.IgstAmt or 0.0,
                    "CgstAmt":item.CgstAmt or 0.0,
                    "SgstAmt":item.SgstAmt or 0.0,
                    "OthChrg":item.OthChrg or 0.0,
                    "Discount":item.Discount or 0.0,
                    "TotItemVal":item.TotItemVal or 0.0
                } for item in self.ItemList],
                "ValDtls":{
                    "AssVal":self.Assval or 0.0,
                    "CgstVal":self.CgstVal or 0.0,
                    "SgstVal":self.SgstVal or 0.0,
                    "IgstVal":self.IgstVal or 0.0,
                    "RndOffAmt":self.RndOffAmt or 0.0,
                    "TotInvVal":self.TotInvVal or 0.0
                }
            }
    
    
    
    def _prepare_e_way(self):
        return  {
                    "Irn": self.move_id.Irn,
                    "Distance": self.move_id.distance or 0.0,
                    "TransMode": self.move_id.transporter_mode or None,
                    "TransId": self.move_id.transporter_id or None,  
                    "TransName": self.move_id.transporter_name or None,
                    "TransDocDt": datetime.strftime(self.move_id.transporter_doc_date,"%d/%m/%Y")  or None,
                    "TransDocNo": self.move_id.transporter_doc_num or None,
                    "VehNo": self.move_id.vehicle_number or None,
                    "VehType": self.move_id.vehicle_type or None,
                }
