from datetime import date
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import SQL

_logger = logging.getLogger(__name__)


class BankReconciliationReportCustomHandler(models.AbstractModel):
    _inherit = 'account.bank.reconciliation.report.handler'

    def _get_last_bank_statement(self, journal, options):
        """
            Retrieve the last bank statement created using this journal.
            :param journal: The journal used.
            :param domain:  An additional domain to be applied on the account.bank.statement model.
            :return:        An account.bank.statement record or an empty recordset.
        """
        report_date = fields.Date.from_string(options['date']['date_to'])
        last_statement_domain = [('journal_id', '=', journal.id), ('statement_id', '!=', False), ('date', '<=', report_date)]
        last_st_line = self.env['account.bank.statement.line'].search(last_statement_domain, order='date desc, id asc', limit=1)
        return last_st_line.statement_id