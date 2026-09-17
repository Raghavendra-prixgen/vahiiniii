	# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError,ValidationError
from odoo import api, fields, models, _
import pdb
import pytz
from odoo.tools import (
    create_index,
    date_utils,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    index_exists,
    OrderedSet,
    SQL,
)



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def get_sequence_date_range(self):
        now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
        today = now.today()
        fiscalyear_last_day = self.env.company.fiscalyear_last_day
        fiscalyear_last_month = int(self.env.company.fiscalyear_last_month)
        date_start, date_end = date_utils.get_fiscal_year(today, day=fiscalyear_last_day, month=fiscalyear_last_month)
        fiscalyear_prefix = "{}-{}".format(date_start.strftime('%y'),date_end.strftime('%y'))
        

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def get_sequence_date_range(self,fiscalyear_code,effective_date,range_date):
        today = effective_date.today()
        fiscalyear_last_day = self.env.company.fiscalyear_last_day
        fiscalyear_last_month = int(self.env.company.fiscalyear_last_month)
        date_start, date_end = date_utils.get_fiscal_year(effective_date, day=fiscalyear_last_day, month=fiscalyear_last_month)

        range_date_start, range_date_end = date_utils.get_fiscal_year(range_date, day=fiscalyear_last_day, month=fiscalyear_last_month)

        current_date_start, current_date_end = date_utils.get_fiscal_year(today, day=fiscalyear_last_day, month=fiscalyear_last_month)
        if fiscalyear_code == 'financial_year':
            now_prefix = "{}-{}".format(date_start.strftime('%Y'),date_end.strftime('%Y'))
            range_prefix = "{}-{}".format(range_date_start.strftime('%Y'),range_date_end.strftime('%Y'))
            current_prefix = "{}-{}".format(current_date_start.strftime('%Y'),current_date_end.strftime('%Y'))

        else:
            now_prefix = "{}-{}".format(date_start.strftime('%y'),date_end.strftime('%y'))
            range_prefix = "{}-{}".format(range_date_start.strftime('%y'),range_date_end.strftime('%Y'))
            current_prefix = "{}-{}".format(current_date_start.strftime('%Y'),current_date_end.strftime('%Y'))
            
        return now_prefix,range_prefix,current_prefix


    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))
            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S','financial_year':'%Y','f_y':'%y'
            }
            res = {}
            for key, format in sequences.items():
                if key == 'financial_year':
                    fiscalyear_prefix,effective_prefix,range_prefix = self.get_sequence_date_range('financial_year',effective_date,range_date)
                    res[key] = fiscalyear_prefix
                    res['range_' + key] = effective_prefix
                    res['current_' + key] = range_prefix
                elif key == 'f_y':
                    fiscalyear_prefix,effective_prefix,range_prefix = self.get_sequence_date_range('f_y',effective_date,range_date)
                    res[key] = fiscalyear_prefix
                    res['range_' + key] = effective_prefix
                    res['current_' + key] = range_prefix
                else:
                    res[key] = effective_date.strftime(format)
                    res['range_' + key] = range_date.strftime(format)
                    res['current_' + key] = now.strftime(format)
            return res

        self.ensure_one()
        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except (ValueError, TypeError):
            raise UserError(_('Invalid prefix or suffix for sequence “%s”', self.name))
        return interpolated_prefix, interpolated_suffix
    
