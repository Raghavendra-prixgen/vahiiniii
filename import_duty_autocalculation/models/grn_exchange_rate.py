
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero, float_round
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    y_valuation_based_on =  fields.Selection([('bankrate','Bank Rate'),('boerate','BOE Rate')], string='Valuation Based On')
   
    
class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'   

    y_valuation_based_on = fields.Selection([('bankrate','Bank Rate'),('boerate','BOE Rate')], string='Valuation Based On', readonly=False,copy=False,related="company_id.y_valuation_based_on")



class StockPicking(models.Model):
    _inherit = "stock.picking"

    y_valuation_exchange_rate = fields.Float(string="Exchange Rate for valuation")

    def button_validate(self):
        for picking in self:
            if picking.company_id:
                company_id = picking.company_id
                if picking.company_id.sudo().parent_id:
                    company_id = picking.company_id.sudo().parent_id
                valuation_based_on = company_id.y_valuation_based_on
                if valuation_based_on == 'bankrate':
                    picking.update_exchange_rate()


        return super().button_validate()

    def update_exchange_rate(self):
        for res in self:
            company_id = res.company_id
            if res.company_id.sudo().parent_id:
                company_id = res.company_id.sudo().parent_id
            valuation_based_on = company_id.y_valuation_based_on
            purchase_id = self.env['purchase.order'].search([('name','=',res.origin),('company_id','=',res.company_id.id)])
            if purchase_id:
                if purchase_id.currency_id != res.company_id.currency_id:
                    if valuation_based_on == 'bankrate':
                        currency = purchase_id.currency_id
                        if currency.inverse_rate < 1:
                                res.y_valuation_exchange_rate = currency.rate
                        else:
                            res.y_valuation_exchange_rate = currency.inverse_rate
                    else:
                        currency = purchase_id.currency_id

                        exim_currency_id = self.env['exim.currency'].search([('y_currency_id','=',currency.id)])
                        company_currency = res.company_id.currency_id
                        exim_company_currency_id = self.env['exim.currency'].search([('y_currency_id','=',company_currency.id)])
                        currency_rate = self.env['exim.currency']._get_conversion_rate(exim_currency_id, exim_company_currency_id, res.company_id , fields.Date.context_today(res))
                        res.y_valuation_exchange_rate = currency_rate




       
       
    
    @api.model
    def create(self,vals):
        res = super().create(vals)
        if res.company_id :
            company_id = res.company_id
            if res.company_id.sudo().parent_id:
                company_id = res.company_id.sudo().parent_id
            valuation_based_on = company_id.y_valuation_based_on
            purchase_id = self.env['purchase.order'].search([('name','=',res.origin),('company_id','=',res.company_id.id)])
            if purchase_id:
                if purchase_id.currency_id != res.company_id.currency_id:
                    if valuation_based_on == 'bankrate':
                        currency = purchase_id.currency_id
                        if currency.inverse_rate < 1:
                                res.y_valuation_exchange_rate = currency.rate
                        else:
                            res.y_valuation_exchange_rate = currency.inverse_rate
                    else:
                        currency = purchase_id.currency_id

                        exim_currency_id = self.env['exim.currency'].search([('y_currency_id','=',currency.id)])
                        company_currency = res.company_id.currency_id
                        exim_company_currency_id = self.env['exim.currency'].search([('y_currency_id','=',company_currency.id)])
                        currency_rate = self.env['exim.currency']._get_conversion_rate(exim_currency_id, exim_company_currency_id, res.company_id , fields.Date.context_today(res))
                        res.y_valuation_exchange_rate = currency_rate
        return res


class StockMove(models.Model):
    _inherit = "stock.move"



    #overriding standard to take exchange rate from custom field instead of taking from standard currency table
    def _get_price_unit(self):

        price_unit = super()._get_price_unit()
        
        line = self.purchase_line_id
        if line:
            po_gross_price_unit = line._get_gross_price_unit()
            order = line.order_id
            if order.currency_id != order.company_id.currency_id and self.picking_id.y_valuation_exchange_rate:
                po_price_unit = self.picking_id.y_valuation_exchange_rate * po_gross_price_unit
                precision = self.env['decimal.precision'].precision_get('Product Price')
                if not float_is_zero(po_price_unit, precision) or self._should_force_price_unit():
                    if self.product_id.lot_valuated:
                        return dict.fromkeys(self.lot_ids, po_price_unit)
                    else:
                        return {self.env['stock.lot']: po_price_unit}
                else:
                    return price_unit
            else:
                return price_unit

        else:
            return price_unit


# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"

#     # Override field to disable precompute so our compute method fires normally
#     # amount_currency = fields.Monetary(
#     #     string='Amount in Currency',
#     #     compute='_compute_amount_currency',
#     #     inverse='_inverse_amount_currency',
#     #     store=True,
#     #     readonly=False,
#     #     precompute=False,  # <-- disable this
#     # )

#     @api.depends('currency_rate', 'balance', 'move_id.stock_move_id', 
#                  'move_id.stock_move_id.picking_id.y_valuation_exchange_rate',
#                  'move_id.stock_valuation_layer_ids')
#     def _compute_amount_currency(self):
#         _logger.info("Entering compute method")
#         super()._compute_amount_currency()
#         _logger.info("After super compute method")
#         for line in self:
#             if (
#                 line.move_id.stock_move_id
#                 and line.move_id.stock_move_id.picking_id.y_valuation_exchange_rate
#                 and line.move_id.stock_valuation_layer_ids
#                 and line.currency_id != line.company_id.currency_id
#             ):
#                 _logger.info("Entering custom if block for line: %s", line)
#                 line.amount_currency = line.currency_id.round(
#                     line.balance / line.move_id.stock_move_id.picking_id.y_valuation_exchange_rate
#                 )
#                 _logger.info("line.amount_currency: %s", line.amount_currency)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends('currency_rate', 'balance', 'move_id.stock_move_id', 
                 'move_id.stock_move_id.picking_id.y_valuation_exchange_rate',
                 'move_id.stock_valuation_layer_ids')
    def _compute_amount_currency(self):
        _logger.info("Entering compute method")
        super()._compute_amount_currency()
        _logger.info("After super compute method")
        for line in self:
            if (
                line.move_id.stock_move_id
                and line.move_id.stock_move_id.picking_id.y_valuation_exchange_rate
                and line.move_id.stock_valuation_layer_ids
                and line.currency_id != line.company_id.currency_id
            ):
                _logger.info("Entering custom if block for line: %s", line)
                line.amount_currency = line.currency_id.round(
                    line.balance / line.move_id.stock_move_id.picking_id.y_valuation_exchange_rate
                )
                _logger.info("line.amount_currency: %s", line.amount_currency)

