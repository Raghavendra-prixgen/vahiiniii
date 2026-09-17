from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    y_posting_date = fields.Date(
        string='Posting Date',copy=False,default=False,
        help='Date to be used for stock move and line and valuation and accounting entries.', # Link to the security group
    )

    @api.constrains('y_posting_date')
    def _check_posting_date(self):
        today = fields.Date.today()
        for rec in self:
            if rec.y_posting_date and rec.y_posting_date > today:
                raise ValidationError("Posting Date cannot be a future date.")


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        moves = self.filtered(lambda m: m.picking_id.picking_type_code == 'incoming' and m.purchase_line_id and m.picking_id.y_posting_date)
        if moves:
            ctx = dict(self.env.context)
            ctx['force_posting_date'] = moves[0].picking_id.y_posting_date
            return super(StockMove, self.with_context(ctx))._action_done(cancel_backorder=cancel_backorder)

        return super()._action_done(cancel_backorder=cancel_backorder)

class AccountMove(models.Model):
    _inherit = 'account.move'

    # @api.model
    # def create(self, vals):
    #     posting_date = self.env.context.get('force_posting_date')
    #     if posting_date:
    #         vals['date'] = posting_date
    #     return super().create(vals)

    @api.model
    def create(self, vals):
        moves = super().create(vals)
        for move in moves:
            if self.env.context.get('force_posting_date') and move.stock_move_id:
                for stock_move in move.stock_move_id.filtered(lambda x:x.picking_id.picking_type_code == 'incoming' and x.purchase_line_id and x.picking_id.y_posting_date):
                    posting_date = stock_move.picking_id.y_posting_date
                    new_datetime = posting_date
                    new_date = posting_date
                    if posting_date:
                        self.env.cr.execute(
                            "UPDATE account_move SET date = '%s', create_date = '%s', write_date = '%s' WHERE id=%s" %
                            (new_date, new_datetime, new_datetime, move.id)
                        )
                        self.env.cr.execute(
                                "UPDATE account_move_line SET date = '%s', create_date = '%s', write_date = '%s' WHERE move_id=%s" %
                                (new_date, new_datetime, new_datetime, move.id))

        return moves

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model
    def create(self, vals):
        svls = super().create(vals)
        for svl in svls:
            for move in svl.stock_move_id.filtered(lambda x:x.picking_id.picking_type_code == 'incoming' and x.purchase_line_id):
                if not move.picking_id.sudo().y_posting_date:
                    continue
                new_datetime = move.picking_id.y_posting_date
                new_date = move.picking_id.y_posting_date
                svls = move.stock_valuation_layer_ids
                move.write({
                    'date': new_datetime,
                    'create_date': new_datetime,
                    'write_date': new_datetime,
                })
                for move_line in move.move_line_ids:
                    move_line.write({
                        'date': new_datetime,
                        'create_date': new_datetime,
                        'write_date': new_datetime,
                    })

                self.env.cr.execute("UPDATE stock_valuation_layer SET create_date = '%s', write_date = '%s' WHERE id=%s" %(new_datetime, new_datetime, svl.id))
        return svls
