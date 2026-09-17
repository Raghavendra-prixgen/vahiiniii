from odoo import models, fields, api, _


class TransportationOrder(models.Model):
    _inherit = 'transportation.order'

    y_invoice_ids = fields.Many2many('account.move',compute="get_account_move_invoices",string="Invoices")
    y_invoice_name = fields.Char(compute="_compute_invoice_names",store=True,string="Invoice Names")

    @api.depends('y_invoice_ids')
    def _compute_invoice_names(self):
        for rec in self:
            rec.y_invoice_name = ''
            if rec.y_invoice_ids:
                rec.y_invoice_name = ",".join(rec.y_invoice_ids.mapped('name'))

    
    def get_account_move_invoices(self):
        for rec in self:
            rec.y_invoice_ids = False 
            query = """SELECT account_move_id FROM invoice_transportation_rel WHERE transportation_order_id = {}""".format(rec.id)
            self.env.cr.execute(query)
            invoice_ids = [row[0] for row in self.env.cr.fetchall()]
            if invoice_ids:
                rec.y_invoice_ids = [(6,0,invoice_ids)]
 
class StockMove(models.Model):
    _inherit='stock.move'   

    def get_receipt_lines(self):
        res = super().get_receipt_lines()
        account_val = self.env['account.move'].browse(self._context.get('ref_move_id'))
        # Tranportaion Detils
        if self.picking_id.mapped('y_transportation_order_id'):
            lr_no = self.mapped('picking_id').filtered(lambda x:x.y_lr_number).mapped('y_lr_number')
            if lr_no:
                lr_no = ','.join(lr_no)
                account_val.write({'y_lr_number':lr_no})
        
        return res


class AccountMove(models.Model):
    _inherit='account.move'
    
    y_transportation_order_ids = fields.Many2many('transportation.order','invoice_transportation_rel',copy=False,string="Transportation Orders",compute="_compute_transportation_orders",store=True)
    y_gate_management_ids = fields.Many2many('gate.management','invoice_gate_management_rel',copy=False,string="Gate Management",compute="_compute_gate_management_orders")



    @api.depends('invoice_line_ids.y_stock_move_id')
    def _compute_transportation_orders(self):
        for move in self:
            move.y_transportation_order_ids = False
            if move.invoice_line_ids.y_stock_move_id.picking_id.mapped('y_transportation_order_id'):
                transportor_ids = move.invoice_line_ids.y_stock_move_id.picking_id.mapped('y_transportation_order_id')
                if transportor_ids:
                    move.write({'y_transportation_order_ids':[(6,0,transportor_ids.ids)]})

    def _compute_gate_management_orders(self):
        for move in self:
            move.y_gate_management_ids = False
            if move.invoice_line_ids.y_stock_move_id.picking_id.mapped('y_stock_gate_management_ids'):
                gage_management_ids = move.invoice_line_ids.y_stock_move_id.picking_id.mapped('y_stock_gate_management_ids')
                if gage_management_ids:
                    move.write({'y_gate_management_ids':[(6,0,gage_management_ids.ids)]})

