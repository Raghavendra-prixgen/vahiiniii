from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
# from odoo.tests.common import Form
from odoo.tools.float_utils import float_round

class AccountMove(models.Model):
    _inherit = "account.move"

    y_btb_id = fields.Many2one('branch.to.branch.transfer',string='Branch To Branch Transfer Order')
    y_btb_in_picking_id = fields.Many2one('stock.picking',string='Receipt Note')
    y_btb_out_picking_id = fields.Many2one('stock.picking',string='Delivery Slip')
    y_branch_sale_btb_id = fields.Many2one('branch.to.branch.transfer',string="Branch Sale BTB")
    y_branch_purchase_btb_id = fields.Many2one('branch.to.branch.transfer',string="Branch Purchase BTB")
    y_offset_entry_id = fields.Many2one('account.move',string="Offset Entry")

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        lines_vals_list = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for move in self:
            if move.y_btb_id and move.y_btb_in_picking_id or move.y_btb_out_picking_id:
                lines_vals_list = []
        return lines_vals_list

    def _prepare_invoice_line(self,line,price):  
        account_id = False
        if self.move_type == 'in_invoice':
            account_id = self.y_btb_id.y_btb_config_id.y_branch_purchase_account_id.id
        if self.move_type == 'out_invoice':
            account_id = self.y_btb_id.y_btb_config_id.y_branch_sale_account_id.id

        values = {
            'name':'{}:{}'.format(self.y_btb_id.y_name,line.product_id.name),
            'move_id':self.id,
            'product_id':line.product_id.id,
            'product_uom_id':line.product_uom.id,
            'account_id': account_id,
            'price_unit':price,
            'quantity':line.quantity,
            'y_stock_move_id':line.id,
            'y_stock_picking_ref':line.picking_id.id,
            'tax_ids':[(6,0,line.product_id.taxes_id.ids)],
        }
        # Updated Unit Price and Quantity From Invoice
        if self.move_type == 'in_invoice':
            # Below search funciton for access other branch data with using sudo => y_btb_id.y_invoice_ids(not working) 
            invoice_ids = self.env['account.move'].sudo().search([('y_btb_id','=',self.y_btb_id.id),('move_type','=','out_invoice'),('state','=','posted')])
            if invoice_ids:
                invoice_line_ids = invoice_ids.invoice_line_ids.filtered(lambda x:x.product_id == line.product_id)
                if invoice_line_ids:
                    values['price_unit'] = sum(invoice_line_ids.mapped('price_unit'))
                    values['quantity'] = sum(invoice_line_ids.mapped('quantity'))
        return values
    
    def _generate_sto_invoice_lines(self, lines):
        invoice_lines = self.env['account.move.line']
        for line in lines:    
            svl = line.with_context(active_test=False).mapped('stock_valuation_layer_ids').filtered(lambda l: l.quantity != 0)
            layers_qty = sum(svl.mapped('quantity'))
            layers_values = sum(svl.mapped('value'))
            svl_price = 0
            if layers_qty != 0:
                svl_price = float_round((layers_values / layers_qty), precision_rounding=line.product_uom.rounding)

            price = line.product_id.with_company(line.company_id).standard_price if not svl else svl_price
            invoice_line = invoice_lines.new(self._prepare_invoice_line(line,price))
            price = invoice_line.price_unit
            invoice_line._sto_onchange_mark_recompute_taxes()
            invoice_line._sto_onchange_mark_recompute_taxes_analytic()
            invoice_line._sto_onchange_product_id()
            invoice_line.price_unit = price # to overide the standared price unit 
            invoice_line._sto_onchange_account_id()
            invoice_line._sto_onchange_balance()
            invoice_line._sto_onchange_debit()
            invoice_line._sto_onchange_credit()
            invoice_line._sto_onchange_amount_currency()
            invoice_line._sto_onchange_price_subtotal()
            invoice_line._sto_onchange_currency()
            invoice_lines += invoice_line
            self.line_ids=[(5,0,0)]
        return invoice_lines

    @api.onchange('y_btb_in_picking_id')
    def _onchange_y_btb_in_picking_id(self):
        if self.y_btb_in_picking_id:
            if self.y_btb_id:
                self.partner_id = self.y_btb_id.y_from_partner_id.id
            for line in self.line_ids:
                self.line_ids = [(2, line.id, 0)]
            if self.y_btb_in_picking_id:
                self.y_btb_in_picking_id.y_btb_id = self.y_btb_id.id
                invoice_lines = self._generate_sto_invoice_lines(self.y_btb_in_picking_id.move_ids_without_package.filtered(lambda x:x.quantity > 0))
                self._onchange_partner_id()
                invoice_lines._sto_onchange_mark_recompute_taxes()
            if self.y_btb_id:
                self.company_id = self.y_btb_in_picking_id.company_id.id

            if self.move_type == 'in_invoice':
                payable_line_id = self.line_ids.filtered(lambda x:x.account_id == self.partner_id.property_account_payable_id)
                if payable_line_id:
                    payable_line_id.write({'account_id':self.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id})
            
    @api.onchange('y_btb_out_picking_id')
    def _onchange_y_btb_out_picking_id(self):
        if self.y_btb_id:
            self.partner_id = self.y_btb_id.y_to_partner_id.id            
        for line in self.line_ids:
            self.line_ids = [(2, line.id, 0)]
        if self.y_btb_out_picking_id:
            self.y_btb_out_picking_id.y_btb_id = self.y_btb_id.id
            invoice_lines = self._generate_sto_invoice_lines(self.y_btb_out_picking_id.move_ids_without_package.filtered(lambda x:x.quantity > 0))
            # self._onchange_currency()
            self._onchange_partner_id()
            invoice_lines._sto_onchange_mark_recompute_taxes()
        if self.y_btb_id:
            self.company_id = self.y_btb_out_picking_id.company_id.id

        if self.move_type == 'out_invoice':
            receivable_line_id = self.line_ids.filtered(lambda x:x.account_id == self.partner_id.property_account_receivable_id)
            if receivable_line_id:
                receivable_line_id.write({'account_id':self.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id})
    
    
    def action_post(self):
        for move in self:
            if move.move_type == 'out_invoice' and move.y_btb_out_picking_id:
                receivable_line_id = move.line_ids.filtered(lambda x:x.account_id == move.partner_id.property_account_receivable_id)
                if receivable_line_id:
                    receivable_line_id.write({'account_id':move.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id})
        
            if move.move_type == 'in_invoice' and move.y_btb_in_picking_id:
                payable_line_id = move.line_ids.filtered(lambda x:x.account_id == move.partner_id.property_account_payable_id)
                if payable_line_id:
                    payable_line_id.write({'account_id':move.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id})
            
        res = super(AccountMove,self).action_post()
        for rec in self:
            picking = rec.y_btb_in_picking_id or rec.y_btb_out_picking_id or False
            if picking:
                picking.y_account_move_id = rec.id
        return res

    def button_draft(self):
        for rec in self:
            picking = rec.y_btb_in_picking_id or rec.y_btb_out_picking_id
            if picking:
                picking.y_account_move_id = False
        return super(AccountMove,self).button_draft()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_btb_id = fields.Many2one('branch.to.branch.transfer',string="BTB Transfer",compute="_compute_stock_valuation_layer_ids_btb_records",store=True)

    @api.depends('move_id.stock_valuation_layer_ids')
    def _compute_stock_valuation_layer_ids_btb_records(self):
        for line in self:
            line.y_btb_id = False
            if line.move_id.y_btb_id:
                line.y_btb_id = line.move_id.y_btb_id.id


    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        for line in self:
            account_type = line.account_id.account_type
            if not line.move_id.y_btb_id and (not line.move_id.y_btb_in_picking_id or not line.move_id.y_btb_out_picking_id):
                if line.move_id.is_sale_document(include_receipts=True):
                    if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
                        raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
                if line.move_id.is_purchase_document(include_receipts=True):
                    if (line.display_type == 'payment_term') ^ (account_type == 'liability_payable'):
                        raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))


    y_stock_transfer_order_id = fields.Many2one('branch.to.branch.transfer',related='move_id.y_btb_id',store=True)
    y_recompute_tax_line = fields.Boolean(store=False, readonly=True,string="Recompute Tax Line")

    # -------------------------------------------------------------------------
    # INITIATION METHODS BEGIN
    # -------------------------------------------------------------------------

    def _sto_onchange_mark_recompute_taxes(self):
        ''' Recompute the dynamic onchange based on taxes.
        If the edited line is a tax line, don't recompute anything as the user must be able to
        set a custom value.
        '''
        for line in self:
            if not line.tax_repartition_line_id:
                line.y_recompute_tax_line = True

    def _sto_onchange_mark_recompute_taxes_analytic(self):
        ''' Trigger tax recomputation only when some taxes with analytics
        '''
        for line in self:
            if not line.tax_repartition_line_id and any(tax.analytic for tax in line.tax_ids):
                line.y_recompute_tax_line = True

    def _get_computed_uom(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id.uom_id
        return False
    
    def _sto_onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue
            line.tax_ids = line._get_computed_taxes()
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._compute_price_unit()

            
            # Convert the unit price to the invoice's currency.
            company = line.move_id.company_id      
            line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company, line.move_id.date)

    def _sto_onchange_account_id(self):
        ''' Recompute 'tax_ids' based on 'account_id'.
        /!\ Don't remove existing taxes if there is no explicit taxes set on the account.
        '''
        if not self.display_type and (self.account_id.tax_ids or not self.tax_ids):
            taxes = self._get_computed_taxes()

            if taxes and self.move_id.fiscal_position_id:
                taxes = self.move_id.fiscal_position_id.map_tax(taxes, partner=self.partner_id)

            self.tax_ids = taxes

    def _sto_onchange_balance(self):
        for line in self:
            if line.currency_id == line.move_id.company_id.currency_id:
                line.amount_currency = line.balance
            else:
                continue
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            # line.update(line._get_fields_onchange_balance())

    def _sto_onchange_debit(self):
        if self.debit:
            self.credit = 0.0
        self._sto_onchange_balance()

    def _sto_onchange_credit(self):
        if self.credit:
            self.debit = 0.0
        self._sto_onchange_balance()

    def _sto_onchange_amount_currency(self):
        for line in self:
            company = line.move_id.company_id
            balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date)
            line.debit = balance if balance > 0.0 else 0.0
            line.credit = -balance if balance < 0.0 else 0.0
            if not line.move_id.is_invoice(include_receipts=True):
                continue

    def _sto_onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
                
    def _sto_onchange_currency(self):
        for line in self:
            company = line.move_id.company_id

            if line.move_id.is_invoice(include_receipts=True):
                line._sto_onchange_price_subtotal()
            elif not line.move_id.reversed_entry_id:
                balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, line.move_id.date or fields.Date.context_today(line))
                line.debit = balance if balance > 0.0 else 0.0
                line.credit = -balance if balance < 0.0 else 0.0
    
    # -------------------------------------------------------------------------
    # INITIATION METHODS END
    # -------------------------------------------------------------------------