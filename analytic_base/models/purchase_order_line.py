from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError
# from odoo.tools.float_utils import float_round, float_compare
# import logging
# _logger = logging.getLogger(__name__)





class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

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
