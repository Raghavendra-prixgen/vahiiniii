from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError




class EximCurrency(models.Model):
    _name = "exim.currency"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EXIM Currency'
    _rec_names_search = ['y_name', 'y_full_name']
    _rec_name = 'y_name'
    _order = 'active desc, y_name'


    y_name = fields.Char(string="Currency")
    y_full_name = fields.Char(string="Name")
    active = fields.Boolean()
    y_symbol = fields.Char(string="Symbol")
    y_currency_unit_label = fields.Char(string="Currency Unit")
    y_currency_subunit_label = fields.Char(string="Currency Subunit")
    y_date = fields.Date(compute='_compute_date',)

    y_rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=0,
                        help='The rate of the currency to the currency of rate 1.')
    y_inverse_rate = fields.Float(compute='_compute_current_rate', digits=0, readonly=True,
                                help='The currency of rate 1 to the rate of the currency.')
    y_rate_string = fields.Char(compute='_compute_current_rate')
    y_currency_id = fields.Many2one('res.currency',string="Currency")

    # y_rate = fields.Float(compute=False, string='Current Rate', digits=0,
    #                     help='The rate of the currency to the currency of rate 1.')
    # y_inverse_rate = fields.Float(compute=False, digits=0, readonly=True,
    #                             help='The currency of rate 1 to the rate of the currency.')
    # y_rate_string = fields.Char(compute=False)

    y_company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company.id)

    y_exim_currency_line_ids = fields.One2many('exim.currency.rate','y_exim_currency_id')

    @api.onchange('y_currency_id')
    def onchange_currency(self):
        for currency in self:
            if currency.y_currency_id:
                parent_currency = currency.y_currency_id
                currency.write({'y_name':parent_currency.name,'y_full_name':parent_currency.full_name,'active':parent_currency.active,'y_symbol':parent_currency.symbol,'y_currency_unit_label':parent_currency.currency_unit_label,'y_currency_subunit_label':parent_currency.currency_subunit_label})

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company=None, date=None):
        if from_currency == to_currency:
            return 1
        company = company or self.env.company
        date = date or fields.Date.context_today(self)
        return from_currency.with_company(company).with_context(to_currency=to_currency.id, date=str(date)).y_inverse_rate




    # @api.model
    # def _get_conversion_rate(self, from_currency, date=None):
    #     date = date or fields.Date.context_today(self)
    #     if from_currency.y_inverse_rate < 1:
    #         from_currency_rate = from_currency.y_rate
    #     else:
    #         from_currency_rate = from_currency.y_inverse_rate
    #     return from_currency_rate

    
    def _get_rates(self, company, y_date):
        if not self.ids:
            return {}
        self.env['exim.currency.rate'].flush_model(['y_rate', 'y_exim_currency_id', 'y_company_id', 'y_name'])
        query = """SELECT c.id,
                          COALESCE((SELECT r.y_rate FROM exim_currency_rate r
                                  WHERE r.y_exim_currency_id = c.id AND r.y_name <= %s
                                    AND (r.y_company_id IS NULL OR r.y_company_id = %s)
                               ORDER BY r.y_company_id, r.y_name DESC
                                  LIMIT 1), 1.0) AS rate
                   FROM exim_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (y_date, company.root_id.id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates



    @api.depends('y_exim_currency_line_ids.y_rate')
    @api.depends_context('to_currency', 'y_date', 'company', 'company_id')
    def _compute_current_rate(self):
        date = self._context.get('date') or fields.Date.context_today(self)
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
        company = company.root_id
        to_currency = self.browse(self.env.context.get('to_currency')) or company.currency_id
        # the subquery selects the last rate before 'date' for the given currency/company
        currency_rates = (self )._get_rates(self.env.company, date)
        for currency in self:
           
            if currency_rates:

                currency.y_rate = currency_rates.get(currency.id) 
                if currency.y_rate>0:
                    currency.y_inverse_rate = 1 / currency.y_rate
                else:
                    currency.y_inverse_rate = 1

                if currency != company.currency_id:
                    currency.y_rate_string = ''
                else:
                    currency.y_rate_string = ''
            else:
                currency.y_rate = 1
                currency.y_inverse_rate = 1
                currency.y_rate_string = ''



    @api.depends('y_exim_currency_line_ids.y_name')
    def _compute_date(self):
        for currency in self:
            currency.y_date = currency.y_exim_currency_line_ids[:1].y_name


    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree', 'form'):
            currency_name = (self.env['res.company'].browse(self._context.get('company_id')) or self.env.company.root_id).currency_id.name
            fields_maps = [
                [['y_company_rate', 'y_rate'], _('Unit per %s', currency_name)],
                [['y_inverse_company_rate', 'y_inverse_rate'], _('%s per Unit', currency_name)],
            ]
            for fnames, label in fields_maps:
                xpath_expression = '//list//field[' + " or ".join(f"@name='{f}'" for f in fnames) + "][1]"
                node = arch.xpath(xpath_expression)
                if node:
                    node[0].set('string', label)
        return arch, view



class EximCurrencyRate(models.Model):
    _name = "exim.currency.rate"
    _description = "EXIM Currency Rate Lines"
    _rec_names_search = ['y_name', 'y_rate']
    _order = "y_name desc"


    y_exim_no = fields.Char(string="Exim Notification Number")
    y_exim_currency_id = fields.Many2one('exim.currency',string="Exim Currency")
    y_name = fields.Date(string="Date",required=True, index=True,
                           default=fields.Date.context_today)
    y_company_id = fields.Many2one('res.company',string="Company",related="y_exim_currency_id.y_company_id",store=True)
    y_company_rate = fields.Float(string="Company rate", digits=0,
        compute="_compute_company_rate",
        inverse="_inverse_company_rate",
        group_operator="avg",
        help="The currency of rate 1 to the rate of the currency.")
    y_inverse_company_rate = fields.Float(string="Inverse Company rate",digits=0,
        compute="_compute_inverse_company_rate",
        inverse="_inverse_inverse_company_rate",
        group_operator="avg",
        help="The rate of the currency to the currency of rate 1 ",
    )
    y_rate = fields.Float(
        digits=0,
        group_operator="avg",
        help='The rate of the currency to the currency of rate 1',
        string='Technical Rate'
    )

    _sql_constraints = [
        ('unique_name_per_day', 'unique (y_name,y_exim_currency_id,y_company_id)', 'Only one currency rate per day allowed!'),
        ('currency_rate_check', 'CHECK (y_rate>0)', 'The currency rate must be strictly positive.'),
    ]

    def _get_latest_rate(self):
        # Make sure 'name' is defined when creating a new rate.
        if not self.y_name:
            raise UserError(_("The name for the current rate is empty.\nPlease set it."))
        return self.y_exim_currency_id.y_exim_currency_line_ids.sudo().filtered(lambda x: (
            x.y_rate
            and x.y_company_id == (self.y_company_id or self.env.company.root_id)
            and x.y_name < (self.y_name or fields.Date.today())
        )).sorted('y_name')[-1:]

    @api.depends('y_exim_currency_id', 'y_company_id', 'y_name')
    def _compute_rate(self):
        for currency_rate in self:
            currency_rate.y_rate = currency_rate.y_rate or currency_rate._get_latest_rate().y_rate or 1.0


    def _get_last_rates_for_companies(self, companies):
        return {
            company: company.currency_id.y_exim_currency_line_ids.sudo().filtered(lambda x: (
                x.y_rate
                and x.y_company_id == company or not x.y_company_id
            )).sorted('y_name')[-1:].y_rate or 1
            for company in companies
        }


    @api.depends('y_rate', 'y_name', 'y_exim_currency_id', 'y_company_id', 'y_exim_currency_id.y_exim_currency_line_ids.y_rate')
    @api.depends_context('company')
    def _compute_company_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.y_company_id | self.env.company.root_id)
        for currency_rate in self:
            company = currency_rate.y_company_id or self.env.company.root_id
            currency_rate.y_company_rate = (currency_rate.y_rate or currency_rate._get_latest_rate().y_rate or 1.0) / last_rate[company]



    @api.onchange('y_company_rate')
    def _inverse_company_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.y_company_id | self.env.company.root_id)
        for currency_rate in self:
            company = currency_rate.y_company_id or self.env.company.root_id
            currency_rate.y_rate = currency_rate.y_company_rate * last_rate[company]


    @api.depends('y_company_rate')
    def _compute_inverse_company_rate(self):
        for currency_rate in self:
            if not currency_rate.y_company_rate:
                currency_rate.y_company_rate = 1.0
            currency_rate.y_inverse_company_rate = 1.0 / currency_rate.y_company_rate

    @api.onchange('y_inverse_company_rate')
    def _inverse_inverse_company_rate(self):
        for currency_rate in self:
            if not currency_rate.y_inverse_company_rate:
                currency_rate.y_inverse_company_rate = 1.0
            currency_rate.y_company_rate = 1.0 / currency_rate.y_inverse_company_rate


    @api.onchange('y_company_rate')
    def _onchange_rate_warning(self):
        latest_rate = self._get_latest_rate()
        if latest_rate:
            diff = (latest_rate.y_rate - self.y_rate) / latest_rate.y_rate
            if abs(diff) > 0.2:
                return {
                    'warning': {
                        'title': _("Warning for %s", self.y_exim_currency_id.y_name),
                        'message': _(
                            "The new rate is quite far from the previous rate.\n"
                            "Incorrect currency rates may cause critical problems, make sure the rate is correct!"
                        )
                    }
                }


    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree'):
            names = {
                'company_currency_name': (self.env['res.company'].browse(self._context.get('company_id')) or self.env.company.root_id).currency_id.name,
                'rate_currency_name': self.env['res.currency'].browse(self._context.get('active_id')).y_name or 'Unit',
            }
            for field in [['y_company_rate', _('%(rate_currency_name)s per %(company_currency_name)s', **names)],
                          ['y_inverse_company_rate', _('%(company_currency_name)s per %(rate_currency_name)s', **names)]]:
                node = arch.xpath("//list//field[@name='%s']" % field[0])
                if node:
                    node[0].set('string', field[1])
        return arch, view

