from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = "stock.move"

    y_btb_line_id = fields.Many2one('branch.to.branch.transfer.line',string="BTB Line")

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        lines = super(StockMove,self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)
        
        # STO OUT Transfer Valuation Account Entry Replace Debit Account
        if self.picking_id.y_btb_id and not self.picking_id.y_btb_picking_out_id and not self.picking_id.y_btb_picking_in_id:            
            if lines.get('debit_line_vals'):
                lines.get('debit_line_vals').update({'account_id':self.picking_id.y_btb_id.y_btb_config_id.y_intranit_account_id.id})

        # STO IN Transfer Valuation Account Entry Replace Credit Account
        if self.picking_id.y_btb_id and self.picking_id.y_btb_picking_out_id:            
            if lines.get('credit_line_vals'):
                lines.get('credit_line_vals').update({'account_id':self.picking_id.y_btb_id.y_btb_config_id.y_intranit_account_id.id})

        return lines

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        res = super()._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        for stock_move_obj in self:
            if stock_move_obj.picking_id.y_btb_id:
                res['y_btb_id'] = stock_move_obj.picking_id.y_btb_id.id
        return res





    # def _get_in_svl_vals(self, forced_quantity):
    #     svl_vals_list = super()._get_in_svl_vals(forced_quantity)
    #     if self.picking_id.y_btb_picking_out_id:
    #         for val in svl_vals_list:
    #             product_id = val['product_id']
    #             lot_id = val['lot_id']
    #             quantity = val['quantity']
    #             valuation = self.picking_id.sudo().y_btb_picking_out_id.move_ids.stock_valuation_layer_ids.filtered(lambda x:x.product_id.id == product_id and x.lot_id.id == lot_id)
    #             val.update({'unit_cost':valuation.unit_cost,'value': quantity * valuation.unit_cost})
    #     return svl_vals_list

    #Overriding Standard To Take Cost From BTB Out 
    # def _get_price_unit(self):
    #     price_unit = super()._get_price_unit()
    #     if self.picking_id.y_btb_picking_out_id and price_unit:
    #         for lot in price_unit.keys():
    #             layer_ids = out_picking.move_ids.stock_valuation_layer_ids.filtered(
    #                 lambda x: x.product_id == self.product_id and x.lot_id == lot
    #             )
    #             if len(layer_ids) > 1:
    #                 cost = sum(layer_ids.mapped('value'))/sum(layer_ids.mapped('quantity'))
    #                 price_unit.update({lot:cost})
    #             elif len(layer_ids) == 1:
    #                 price_unit.update({lot:layer_ids.unit_cost})
                    
    #     return price_unit

    def _get_price_unit(self):
        price_unit = super()._get_price_unit()

        out_picking = self.picking_id.sudo().y_btb_picking_out_id
        if out_picking and price_unit:
            for lot in list(price_unit.keys()):
                layer_ids = out_picking.move_ids.stock_valuation_layer_ids.filtered(
                    lambda l: l.product_id == self.product_id and l.lot_id == lot
                )
                if layer_ids:
                    if len(layer_ids) > 1:
                        total_qty = sum(layer_ids.mapped('quantity')) or 0
                        total_value = sum(layer_ids.mapped('value')) or 0
                        if total_qty:
                            price_unit[lot] = total_value / total_qty
                    else:
                        price_unit[lot] = layer_ids[0].unit_cost

        return price_unit


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.constrains('quantity')
    def _constrains_qty_done(self):
        for rec in self:
            if sum(rec.move_id.move_line_ids.mapped('quantity')) > rec.move_id.product_uom_qty and rec.picking_id.y_btb_id:
                raise ValidationError(_('''Can not process more quantities than demand'''))

    @api.onchange('lot_id','quant_id','product_id')
    def _check_btb_picking_out_access(self):
        for line in self:
            if line.move_id.picking_id.sudo().y_btb_picking_out_id and line.lot_id:
                raise ValidationError("You can't change the lot and product transfer from {} company.".format(line.move_id.picking_id.sudo().y_btb_picking_out_id.company_id.name))

class StockPicking(models.Model):
    _inherit = "stock.picking"

    y_btb_id = fields.Many2one('branch.to.branch.transfer',string='Branch To Branch Transfer')
    y_account_move_id = fields.Many2one('account.move',string="Account Move")
    y_btb_picking_out_id = fields.Many2one('stock.picking',string="Btb Picking Out")
    y_btb_picking_in_id = fields.Many2one('stock.picking',string="Btb Picking In")
    company_id = fields.Many2one('res.company', string='Company', related=False,readonly=True, store=True, index=True,default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('backorder_id') and not vals.get('y_btb_picking_in_id') and not vals.get('y_btb_picking_out_id') and vals.get('y_btb_id'):
                btb_id = self.env['branch.to.branch.transfer'].search([('id','=',vals.get('y_btb_id'))])
                vals['name'] = btb_id.y_btb_config_id.y_shipment_sequence_id.next_by_id()
            if vals.get('backorder_id') and vals.get('y_btb_picking_out_id') and vals.get('y_btb_id'):
                btb_id = self.env['branch.to.branch.transfer'].search([('id','=',vals.get('y_btb_id'))])
                vals['name'] = btb_id.y_btb_config_id.y_receipt_sequence_id.next_by_id()
        return super().create(vals_list)


    # def action_detailed_operations(self):
    #     action = super().action_detailed_operations()
    #     for rec in self:
    #         if rec.y_btb_picking_out_id:
    #             context = action.get('context')
    #             context.update({'create':False,'edit':False})
        
    #     return action
    def _prepare_grn(self):
        stock_transfer_operation = self.env['stock.picking.type'].search([('y_is_branch_to_branch_operation','=',True)])
        if not stock_transfer_operation:
            raise ValidationError(_('''Branch Transfer Operation not Available'''))
        return {
            'name' : self.y_btb_id.y_btb_config_id.y_receipt_sequence_id.next_by_id(),
            'y_btb_picking_out_id':self.id,
            'partner_id':self.y_btb_id.y_from_partner_id.id,
            'y_btb_id':self.y_btb_id.id,
            'picking_type_id':stock_transfer_operation.id,
            'origin':self.y_btb_id.y_name,
            'location_id':stock_transfer_operation.default_location_src_id.id,
            'location_dest_id':self.y_btb_id.y_btb_config_id.y_to_location_id.id,
            'company_id':self.y_btb_id.y_to_warehouse_id.company_id.id,
        }
    
    def _prepare_grn_lines(self):
        stock_transfer_operation = self.env['stock.picking.type'].search([('y_is_branch_to_branch_operation','=',True)])
        if not stock_transfer_operation:
            raise ValidationError(_('''Branch Transfer Operation not Available'''))

        # analytic_distribution = False
        # account_analytic_distribution_id = self.env['account.analytic.distribution.model'].search([('warehouse_id','=',self.y_btb_id.y_to_warehouse_id.id)],limit=1)
        # if account_analytic_distribution_id:
        #     analytic_distribution = account_analytic_distribution_id.analytic_distribution

        return [(0,0,{
            'name':self.name,
            'product_id':line.product_id.id,
            'date_deadline':line.date_deadline,
            'product_uom':line.product_uom.id,
            'product_uom_qty':line.quantity,
            'location_id':stock_transfer_operation.default_location_src_id.id,
            'location_dest_id':self.y_btb_id.y_btb_config_id.y_to_location_id.id,
            # 'analytic_distribution':analytic_distribution,
            'company_id':self.y_btb_id.y_to_warehouse_id.company_id.id,
        })for line in self.move_ids_without_package]


    def button_validate(self):
        if self.y_btb_id:
            stock_transfer_operation = self.env['stock.picking.type'].search([('y_is_branch_to_branch_operation','=',True)])
            if not stock_transfer_operation:
                raise ValidationError(_('''Branch Transfer Operation not Available'''))
            if self.y_btb_id:
                if self.y_btb_id.y_status == 'close':
                    raise ValidationError(_('''Can not validate transfer of a closed Branch Transfer Order'''))
                if self.sudo().y_btb_picking_out_id:
                    if self.y_btb_id.y_is_interstate and self.sudo().y_btb_picking_out_id.y_account_move_id.state != 'posted':
                        raise ValidationError(_('''Invoice to be Processed'''))

        result = super(StockPicking, self).button_validate()
        if self.y_btb_id:
            # Intra Branch Transfer Entry
            if self.y_btb_id.y_btb_config_id.y_is_interstate == False:
                am_vals = []
                if not self.y_btb_id.y_branch_sale_entry_ids.filtered(lambda x:x.y_btb_out_picking_id.id == self.id) and self.y_btb_id and not self.y_btb_picking_out_id and not self.y_btb_picking_in_id:
                    if self.move_ids and self.move_ids.stock_valuation_layer_ids:
                        line_vals = []
                        ref = self.y_btb_id.y_name
                        am_vals = [{'ref':ref,
                                    'partner_id':self.partner_id.id,
                                    'date':fields.Date.context_today(self),
                                    'journal_id':self.y_btb_id.y_btb_config_id.y_branch_sale_journal_id.id,
                                    'y_branch_sale_btb_id':self.y_btb_id.id,
                                    'y_btb_out_picking_id':self.id,
                                    'move_type': 'entry',
                                    'line_ids':[]
                                    }]

                        for line in self.move_ids:
                            svl_quantity = sum(line.stock_valuation_layer_ids.mapped('quantity'))
                            svl_value = sum(line.stock_valuation_layer_ids.mapped('value'))
                            vals = (0,0,{'ref':ref + ' - ' + line.product_id.name,
                                         'name':ref + ' - ' + line.product_id.name,
                                         'partner_id':self.partner_id.id,
                                         'product_id':line.product_id.id,
                                         'product_uom_id':line.product_uom.id,
                                         'quantity':svl_quantity,
                                         'balance':svl_value,
                                         'account_id':self.y_btb_id.y_btb_config_id.y_branch_sale_account_id.id})
                            line_vals.append(vals)

                        svl_quantity = sum(self.move_ids.stock_valuation_layer_ids.mapped('quantity'))
                        svl_value = abs(sum(self.move_ids.stock_valuation_layer_ids.mapped('value')))
                        line_vals.append((0,0,{'ref':ref,
                                               'name':ref,
                                               'partner_id':self.partner_id.id,
                                               'product_id':False,
                                               'product_uom_id':False,
                                               'quantity':svl_quantity,
                                               'balance':svl_value,
                                               'account_id':self.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id}))
                        
                        am_vals[0]['line_ids'] = line_vals
                if am_vals:
                    account_moves = self.env['account.move'].sudo().create(am_vals)
                    account_moves.sudo()._post()

            if self.y_btb_id and self.y_btb_picking_out_id and self.move_ids.stock_valuation_layer_ids:
                for move in self.move_ids:
                    for move_line in move.move_line_ids:
                        out_qty = sum(self.sudo().y_btb_picking_out_id.move_ids.stock_valuation_layer_ids.filtered(lambda x:x.product_id == move_line.product_id and x.lot_id == move_line.lot_id).mapped('quantity'))
                        in_qty = sum(move.picking_id.move_ids.stock_valuation_layer_ids.filtered(lambda x:x.product_id == move_line.product_id and x.lot_id == move_line.lot_id and not x.stock_landed_cost_id).mapped('quantity'))
                        if round(abs(out_qty)) != round(abs(in_qty)):
                            raise ValidationError("It is not allowed to receive a partial quantity.")

                

            # # Create Landed Cost for Diffrence Amount
            # if self.y_btb_id and self.y_btb_picking_out_id:
            #     for move in self.move_ids:
            #         if move.product_id.tracking == 'lot' and move.product_id.lot_valuated:
            #             for move_line in move.move_line_ids:
            #                 branch_out_valuation_ids = self.sudo().y_btb_picking_out_id.move_ids.stock_valuation_layer_ids.filtered(lambda x:x.product_id == move_line.product_id and x.lot_id == move_line.lot_id)
            #                 if branch_out_valuation_ids:
            #                     branch_out_valuation_value = sum(branch_out_valuation_ids.mapped('value'))
            #                     branch_in_valuation_value = sum(move.stock_valuation_layer_ids.filtered(lambda x:x.product_id == move_line.product_id and x.lot_id == move_line.lot_id and not x.stock_landed_cost_id).mapped('value'))
            #                     if abs(branch_out_valuation_value) != abs(branch_in_valuation_value):
            #                         price_unit = abs(branch_out_valuation_value) - abs(branch_in_valuation_value)
            #                         landed_costs = self.env['stock.landed.cost'].sudo().create({'picking_ids': [(6,0,self.ids)],
            #                                                                                     'account_journal_id':self.y_btb_id.y_btb_config_id.y_branch_purchase_journal_id.id,
            #                                                                                     'cost_lines': [(0, 0, {
            #                                                                                     'product_id': self.y_btb_id.y_btb_config_id.y_lanaded_cost_product_id.id,
            #                                                                                     'name': self.y_btb_id.y_btb_config_id.y_lanaded_cost_product_id.name,
            #                                                                                     'account_id': self.y_btb_id.y_btb_config_id.y_intranit_account_id.id,
            #                                                                                     'price_unit': price_unit,
            #                                                                                     'split_method': 'by_quantity',
            #                                                                                 })],
            #                                                                             })
                                    
            #                         landed_costs.sudo().compute_landed_cost()
            #                         landed_costs.valuation_adjustment_lines.filtered(lambda x:x.move_id != move).unlink()
            #                         landed_costs.valuation_adjustment_lines.filtered(lambda x:x.move_id == move).sudo().write({'additional_landed_cost':price_unit})
            #                         landed_costs.sudo().with_company(landed_costs.company_id.id).sudo().button_validate()
            #                         landed_costs.stock_valuation_layer_ids.sudo().write({'description':"{} - {}".format(landed_costs.name,",".join(landed_costs.cost_lines.product_id.mapped('name')))})

            #         else:
            #             branch_out_valuation_ids = self.sudo().y_btb_picking_out_id.move_ids.filtered(lambda x:x.product_id == move.product_id).stock_valuation_layer_ids
            #             if branch_out_valuation_ids:
            #                 branch_out_valuation_value = sum(branch_out_valuation_ids.mapped('value'))
            #                 if abs(branch_out_valuation_value) != sum(move.stock_valuation_layer_ids.filtered(lambda x:not x.stock_landed_cost_id).mapped('value')):
            #                     price_unit = abs(branch_out_valuation_value) - sum(move.stock_valuation_layer_ids.filtered(lambda x:not x.stock_landed_cost_id).mapped('value'))
            #                     landed_costs = self.env['stock.landed.cost'].sudo().create({'picking_ids': [(6,0,self.ids)],
            #                                                                                 'account_journal_id':self.y_btb_id.y_btb_config_id.y_branch_purchase_journal_id.id,
            #                                                                                 'cost_lines': [(0, 0, {
            #                                                                                 'product_id': self.y_btb_id.y_btb_config_id.y_lanaded_cost_product_id.id,
            #                                                                                 'name': self.y_btb_id.y_btb_config_id.y_lanaded_cost_product_id.name,
            #                                                                                 'account_id': self.y_btb_id.y_btb_config_id.y_intranit_account_id.id,
            #                                                                                 'price_unit': price_unit,
            #                                                                                 'split_method': 'by_quantity',
            #                                                                             })],
            #                                                                         })
                                
            #                     landed_costs.sudo().compute_landed_cost()
            #                     landed_costs.valuation_adjustment_lines.filtered(lambda x:x.move_id != move).unlink()
            #                     landed_costs.valuation_adjustment_lines.filtered(lambda x:x.move_id == move).sudo().write({'additional_landed_cost':price_unit})
            #                     landed_costs.sudo().with_company(landed_costs.company_id.id).sudo().button_validate()
            #                     landed_costs.stock_valuation_layer_ids.sudo().write({'description':"{} - {}".format(landed_costs.name,",".join(landed_costs.cost_lines.product_id.mapped('name')))})

            if self.y_btb_id.y_btb_config_id.y_is_interstate == False:
                am_vals = []
                if not self.y_btb_id.y_branch_purchase_entry_ids.filtered(lambda x:x.y_btb_in_picking_id.id == self.id) and self.y_btb_id and self.sudo().y_btb_picking_out_id:
                    if self.move_ids and self.move_ids.stock_valuation_layer_ids:
                        line_vals = []
                        ref = self.y_btb_id.y_name
                        am_vals = [{'ref':ref,
                                    'partner_id':self.partner_id.id,
                                    'date':fields.Date.context_today(self),
                                    'journal_id':self.y_btb_id.y_btb_config_id.y_branch_purchase_journal_id.id,
                                    'y_branch_purchase_btb_id':self.y_btb_id.id,
                                    'y_btb_in_picking_id':self.id,
                                    'move_type': 'entry',
                                    'line_ids':[]
                                    }]

                        for line in self.move_ids:
                            svl_quantity = sum(line.stock_valuation_layer_ids.mapped('quantity'))
                            svl_value = sum(line.stock_valuation_layer_ids.mapped('value'))
                            vals = (0,0,{'ref':ref + ' - ' + line.product_id.name,
                                         'name':ref + ' - ' + line.product_id.name,
                                         'partner_id':self.partner_id.id,
                                         'product_id':line.product_id.id,
                                         'product_uom_id':line.product_uom.id,
                                         'quantity':svl_quantity,
                                         'balance':svl_value,
                                         'account_id':self.y_btb_id.y_btb_config_id.y_branch_purchase_account_id.id})
                            line_vals.append(vals)

                        svl_quantity = sum(self.move_ids.stock_valuation_layer_ids.mapped('quantity'))
                        svl_value = -(sum(self.move_ids.stock_valuation_layer_ids.mapped('value')))
                        line_vals.append((0,0,{'ref':ref,
                                               'name':ref,
                                               'partner_id':self.partner_id.id,
                                               'product_id':False,
                                               'product_uom_id':False,
                                               'quantity':svl_quantity,
                                               'balance':svl_value,
                                               'account_id':self.y_btb_id.y_btb_config_id.y_receivable_payable_offset_account_id.id}))
                        
                        am_vals[0]['line_ids'] = line_vals
                if am_vals:
                    account_moves = self.env['account.move'].sudo().create(am_vals)
                    account_moves.sudo()._post()

            


            if result == True and self.y_btb_id and not self.sudo().y_btb_picking_out_id:
                grn = self.env['stock.picking'].sudo().create(self.sudo()._prepare_grn())
                grn.sudo().write({
                            'move_ids_without_package':self.sudo()._prepare_grn_lines(),
                            'scheduled_date':self.y_btb_id.y_delivery_date,
                            'company_id':self.y_btb_id.y_to_warehouse_id.company_id.id,
                            })

                self.sudo().y_btb_picking_in_id = grn.id
                grn.state = 'assigned'

                # move_lines_ids = []
                # for component in self.move_line_ids_without_package:
                    
                #     vals = ({
                #     'company_id':component.company_id.id,
                #     'lot_id':component.lot_id.id,
                #     'qty_done': component.qty_done,
                #     'product_uom_id': component.product_uom_id.id,
                #     'location_id': component.location_id.id,
                #     'location_dest_id': component.location_dest_id.id,
                #     'product_id': component.product_id.id,
                #     'picking_type_id': component.picking_type_id.id,
                #     'move_id':grn.move_ids_without_package.filtered(lambda x:x.product_id == component.product_id).id,
                #     'state':'assigned'

                #     })
                #     move_line = self.env['stock.move.line'].create(vals)
                #     move_lines_ids.append(move_line.id) 
                # grn.move_line_ids_without_package = [(6, 0, move_lines_ids)]

                move_lines_ids = []
                vals_list = []
                for component in self.move_line_ids_without_package:
                    vals = (0,0,{
                    'company_id':self.sudo().y_btb_id.y_to_warehouse_id.company_id.id,
                    'lot_id':component.lot_id.id,
                    'quantity': component.quantity,
                    'product_uom_id': component.product_uom_id.id,
                    'location_id': stock_transfer_operation.default_location_src_id.id,
                    'location_dest_id': self.sudo().y_btb_id.y_btb_config_id.y_to_location_id.id,
                    'product_id': component.product_id.id,
                    'picking_type_id': component.picking_type_id.id,
                    'state':'assigned',
                    })
                    vals_list.append(vals)
                    
                grn.move_line_ids_without_package = vals_list
        return result

    #auto placing of lot based on previous btb
    def action_confirm(self):
        result = super().action_confirm()
        if self.y_btb_picking_out_id:
            lot_list = self.y_btb_picking_out_id.move_line_ids_without_package.mapped('lot_id')
            index = 0
            for move_line_ids in self.move_line_ids_without_package:
                try:
                    move_line_ids.lot_id = lot_list[index].id
                    index += 1
                except:
                    pass
        return result