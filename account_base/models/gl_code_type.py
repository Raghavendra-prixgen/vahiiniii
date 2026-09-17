# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import tools


class AccountAccount(models.Model):
    _inherit = 'account.account'

    y_gl_code_type = fields.Selection([('assi','ASSI'),('asso','ASSO'),('asex','ASEX'),('aslc','ASLC')],string="Recon Code",copy=False,tracking=True,help="ASSI - for GR IR \n ASSO - for COGS interim \nASEX - for COGS \nASLC - for clearing account")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    y_gl_code_type = fields.Selection(related="account_id.y_gl_code_type",string="Recon Code",store=True,copy=False,tracking=True,help="ASSI - for GR IR \n ASSO - for COGS interim \nASEX - for COGS \nASLC - for clearing account")

