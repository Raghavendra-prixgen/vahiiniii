# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from contextlib import ExitStack, contextmanager


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_groupby_account_ids = fields.Many2many('account.analytic.account',compute="get_analytic_distribution",store=True,string="Analytical Account")
    account_analytic_plan_ids = fields.Many2many('account.analytic.plan',compute="get_analytic_account_plan_ids",store=True)



    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if 'analytic_distribution' in vals and not vals.get('analytic_distribution') and vals.get('display_type')=='tax' and vals.get('move_id'):
                move_id = self.env['account.move'].browse(vals.get('move_id'))
                if move_id.line_ids:
                    analytic_distribution = move_id.line_ids[0].analytic_distribution
                    vals['analytic_distribution'] = analytic_distribution
        return super().create(vals_list)




    def _prepare_exchange_difference_move_vals(self, amounts_list, company=None, exchange_date=None, **kwargs):
        res = super()._prepare_exchange_difference_move_vals(amounts_list,company,exchange_date,**kwargs)
        for i, line in enumerate(res['move_values']['line_ids']):
            command, zero, line_dict = line
            line_dict['analytic_distribution'] = self[0].analytic_distribution
            res['move_values']['line_ids'][i] = (command, zero, line_dict)  # Update the tuple

        return res


    @api.depends("analytic_distribution")
    def get_analytic_distribution(self):
        all_ids = set()
        record_to_ids = {}
        for rec in self:
            analytic_ids = []
            if rec.analytic_distribution:
                for k in rec.analytic_distribution.keys():
                    # Split comma-separated keys like "1,26"
                    for part in str(k).split(","):
                        if part.strip().isdigit():
                            analytic_ids.append(int(part.strip()))

            record_to_ids[rec] = analytic_ids
            all_ids.update(analytic_ids)

        # Fetch all accounts in one query
        accounts = (
            self.env["account.analytic.account"]
            .browse(all_ids)
            .filtered(lambda a: a.active)
        )

        # Assign per record without extra queries
        for rec, ids in record_to_ids.items():
            rec.analytic_groupby_account_ids = accounts.filtered(lambda a: a.id in ids)
   

    @api.depends("analytic_groupby_account_ids")
    def get_analytic_account_plan_ids(self):
        plan_map = {
            rec.id: rec.analytic_groupby_account_ids.mapped("plan_id")
            for rec in self
        }
        for rec in self:
            rec.account_analytic_plan_ids = plan_map.get(rec.id, False)


    def _validate_analytic_distribution(self):
        for line in self.filtered(lambda line: line.display_type not in ('line_section','line_note')):
            line._validate_distribution(**{
                        'product': line.product_id.id,
                        'account': line.account_id.id,
                        'business_domain': line.move_id.move_type in ['out_invoice', 'out_refund', 'out_receipt'] and 'invoice'
                                           or line.move_id.move_type in ['in_invoice', 'in_refund', 'in_receipt'] and 'bill'
                                           or 'general',
                        'company_id': line.company_id.id,
            })

    @api.depends('account_id', 'partner_id', 'product_id','purchase_line_id','sale_line_ids')
    def _compute_analytic_distribution(self):
        for line in self:
            distribution = False
            #Purchase
            if line.purchase_line_id:
                distribution = line.purchase_line_id.analytic_distribution 
            
            #Payment
            elif line.payment_id:

                distribution = line.payment_id.analytic_distribution
            
            # #Expense
            # elif line.expense_id:
            #     distribution = line.expense_id.analytic_distribution

            #sale
            elif line.sale_line_ids:
                distribution = line.sale_line_ids.analytic_distribution 


            #Move Valuation
            elif line.move_id.stock_valuation_layer_ids:
                if line.move_id.stock_valuation_layer_ids.filtered(lambda svl: svl.product_id == line.product_id):
                    if line.move_id.stock_valuation_layer_ids.filtered(lambda svl: svl.product_id == line.product_id)[0].stock_move_id:
                        distribution = line.move_id.stock_valuation_layer_ids.filtered(lambda svl: svl.product_id == line.product_id)[0].stock_move_id.analytic_distribution
                    elif line.move_id.stock_valuation_layer_ids.filtered(lambda svl: svl.product_id == line.product_id)[0].account_move_line_id:
                        distribution = line.move_id.stock_valuation_layer_ids.filtered(lambda svl: svl.product_id == line.product_id)[0].account_move_line_id.analytic_distribution
            
            #Move Valuation
            # elif line.move_id.stock_valuation_layer_ids:
            #     distribution = line.move_id.stock_valuation_layer_ids.stock_move_id.analytic_distribution or line.move_id.stock_valuation_layer_ids.stock_valuation_layer_id.stock_move_id.analytic_distribution
            
            #Non-Tax
            elif not line.tax_tag_ids:
                distribution = line.move_id.line_ids[0].analytic_distribution if line.move_id.line_ids else False
            
            #Standard
            elif line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
                distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": line.product_id.id,
                    "product_categ_id": line.product_id.categ_id.id,
                    "partner_id": line.partner_id.id,
                    "partner_category_id": line.partner_id.category_id.ids,
                    "account_prefix": line.account_id.code,
                    "company_id": line.company_id.id,
                })

            
            line.analytic_distribution = distribution or line.analytic_distribution

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'
    
    def write(self, vals):
        res =  super().write(vals)
        if vals.get('account_move_id'):
            self.account_move_id.line_ids._compute_analytic_distribution()
        return res
    
    
    
class AnalyticAccountAsset(models.Model):
    _inherit = 'account.asset'

    analytic_groupby_account_ids = fields.Many2many('account.analytic.account',compute="get_analytic_distribution",store=True,string="Analytical Account")
    

    @api.depends("analytic_distribution")
    def get_analytic_distribution(self):
        all_ids = set()
        record_to_ids = {}
        for rec in self:
            analytic_ids = []
            if rec.analytic_distribution:
                for k in rec.analytic_distribution.keys():
                    # Split comma-separated keys like "1,26"
                    for part in str(k).split(","):
                        if part.strip().isdigit():
                            analytic_ids.append(int(part.strip()))

            record_to_ids[rec] = analytic_ids
            all_ids.update(analytic_ids)

        # Fetch all accounts in one query
        accounts = (
            self.env["account.analytic.account"]
            .browse(all_ids)
            .filtered(lambda a: a.active)
        )

        # Assign per record without extra queries
        for rec, ids in record_to_ids.items():
            rec.analytic_groupby_account_ids = accounts.filtered(lambda a: a.id in ids)

