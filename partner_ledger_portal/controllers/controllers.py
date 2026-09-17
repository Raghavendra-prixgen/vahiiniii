from collections import OrderedDict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json
import io
import base64

from odoo import http, fields, _
from odoo.http import request, content_disposition
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
# from odoo.addons.web.controllers.main import Binary

class CustomerPortalPartnerLedger(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        
        # values['ledger_count'] = 1
        
        if 'ledger_count' in counters:
            AccountMoveLine = request.env['account.move.line'].sudo()
            values['ledger_count'] = AccountMoveLine.search_count([
                ('partner_id', '=', partner.id),
                ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
                ('parent_state', '=', 'posted'),
            ])
        return values
    
    def _get_partner_ledger_values(self, page=1, date_begin=None, date_end=None, journal_type=None, outstanding_only=False, sortby=None, **kw):
        partner = request.env.user.partner_id
        AccountMoveLine = request.env['account.move.line'].sudo()
        
        # Default date range (last 12 months)
        if not date_begin:
            date_begin = fields.Date.to_string(date.today() - relativedelta(months=12))
        if not date_end:
            date_end = fields.Date.to_string(date.today())
            
        # Calculate initial balance (all entries before date_begin)
        initial_balance_domain = [
            ('partner_id', '=', partner.id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('parent_state', '=', 'posted'),
            ('date', '<', date_begin),
        ]
        
        initial_balance_lines = AccountMoveLine.search(initial_balance_domain)
        initial_balance = 0
        
        for line in initial_balance_lines:
            if line.account_id.account_type == 'asset_receivable':
                initial_balance += line.debit - line.credit
            else:  # payable
                initial_balance += line.credit - line.debit
        
        # Rest of the domain for current period
        domain = [
            ('partner_id', '=', partner.id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('parent_state', '=', 'posted'),
            ('date', '>=', date_begin),
            ('date', '<=', date_end),
        ]
        
        # Filter by journal type
        if journal_type and journal_type != 'all':
            if journal_type == 'invoice':
                domain.append(('journal_id.type', 'in', ['sale', 'purchase']))
            elif journal_type == 'payment':
                domain.append(('journal_id.type', '=', 'bank'))
            elif journal_type == 'other':
                domain.append(('journal_id.type', 'not in', ['sale', 'purchase', 'bank']))
        
        # Filter for outstanding only
        if outstanding_only:
            domain.append(('reconciled', '=', False))
            
        # Sorting
        order = 'date desc'
        if sortby == 'date_asc':
            order = 'date asc'
        elif sortby == 'amount_desc':
            order = 'balance desc'
        elif sortby == 'amount_asc':
            order = 'balance asc'
            
        # Count for pager
        ledger_count = AccountMoveLine.search_count(domain)
        
        # Pager
        url = "/my/partner_ledger"
        pager = portal_pager(
            url=url,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'journal_type': journal_type, 'outstanding_only': outstanding_only, 'sortby': sortby},
            total=ledger_count,
            page=page,
            step=self._items_per_page
        )
        
        # Fetch records
        ledger_lines = AccountMoveLine.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        # Get the company currency (fallback) - ensure it's a valid record
        company_currency = request.env.company.currency_id
        if not company_currency:
            # If no company currency is found, use USD as fallback
            company_currency = request.env.ref('base.USD')
        
        # Compute running balance starting from initial balance
        running_balance = initial_balance
        ledger_data = []
        
        # Initialize totals
        total_debit = 0
        total_credit = 0
        
        today = fields.Date.today()

        for line in ledger_lines:
            # For receivable accounts, debit increases the balance, credit decreases
            # For payable accounts, credit increases the balance, debit decreases
            if not outstanding_only:
                if line.account_id.account_type == 'asset_receivable':
                    running_balance += line.debit - line.credit
                    amount = line.amount_currency if line.currency_id != line.company_currency_id else ""
                else:  # payable
                    running_balance += line.credit - line.debit
                    amount = line.amount_currency if line.currency_id != line.company_currency_id else ""
            else:
                running_balance = line.amount_residual
                amount = (line.amount_residual * line.currency_rate) if line.currency_id != line.company_currency_id else ""
            
            # Update totals
            total_debit += line.debit
            total_credit += line.credit
            
            # Get the correct amounts in the respective currencies
            debit_amount = line.debit 
            credit_amount = line.credit

            # Create a single dictionary with all the data
            line_data = {
                'id': line.id,
                'date': line.date,
                'name': line.name,
                'journal_name': line.journal_id.name,
                'matching_number': line.matching_number,
                'move_name': line.move_id.name,
                'debit': debit_amount,
                'credit': credit_amount,
                'running_balance': running_balance,
                'due_date': line.date_maturity,
                'reconciled': line.reconciled,
                'company_currency': line.company_currency_id or company_currency,
                'currency': line.move_id.currency_id,
                'currency_symbol': line.currency_id.symbol,
                'move_type': line.move_id.move_type,
                'move_id': line.move_id.id,
            }
            
            # Add amount_currency based on condition
            if not outstanding_only:
                line_data['amount_currency'] = line.amount_currency
                line_data['amount'] = round(float(amount), 2) if amount not in ["", None] else 0.0
            else:
                # line_data['amount_currency'] = round(amount,2)
                line_data['amount_currency'] = round(float(amount), 2) if amount not in ["", None] else 0.0

            
            line_data['is_overdue'] = False
            if line.date_maturity and line.date_maturity < today:
                line_data['is_overdue'] = True
            
            # Append the complete dictionary to ledger_data
            ledger_data.append(line_data)
        
        # Add totals to values - using company currency for totals
        totals = {
            'total_debit': total_debit,
            'total_credit': total_credit,
            'final_balance': running_balance,
            'currency': company_currency,  # Always use company currency for totals
        }
            
        # Filter options
        journal_types = [
            ('all', _('All')),
            ('invoice', _('Invoices & Bills')),
            ('payment', _('Payments')),
            ('other', _('Other')),
        ]
        
        # Sorting options
        sortby_options = [
            ('date_desc', _('Date (newest)')),
            ('date_asc', _('Date (oldest)')),
            ('amount_desc', _('Balance (highest)')),
            ('amount_asc', _('Balance (lowest)')),
        ]
        
        values = {
            'date_begin': date_begin,
            'date_end': date_end,
            'journal_type': journal_type or 'all',
            'outstanding_only': outstanding_only,
            'sortby': sortby or 'date_desc',
            'ledger_lines': ledger_data,
            'page_name': 'partner_ledger',
            'pager': pager,
            'default_url': url,                                         
            'journal_types': OrderedDict(journal_types),
            'sortby_options': OrderedDict(sortby_options),
            'totals': totals,
            'initial_balance': initial_balance,
            'company_currency': company_currency,
        }
        
        return values

    @http.route(['/my/partner_ledger', '/my/partner_ledger/page/<int:page>'], type='http', auth="user", website=True)
    def portal_partner_ledger(self, page=1, date_begin=None, date_end=None, journal_type=None, outstanding_only=False, sortby=None, **kw):
        values = self._get_partner_ledger_values(page, date_begin, date_end, journal_type, outstanding_only, sortby, **kw)
        values['page_name'] = 'partner_ledger'
        
        return request.render("partner_ledger_portal.portal_partner_ledger", values)
        
    @http.route(['/my/partner_ledger/filter'], type='json', auth="user", website=True)
    def portal_partner_ledger_filter(self, page=1, date_begin=None, date_end=None, journal_type=None, outstanding_only=False, sortby=None, **kw):
        values = self._get_partner_ledger_values(page, date_begin, date_end, journal_type, outstanding_only, sortby, **kw)
        
        return request.env['ir.ui.view'].sudo()._render_template("partner_ledger_portal.portal_partner_ledger_lines", values)
    
    @http.route(['/my/partner_ledger/pdf'], type='http', auth="user", website=True)
    def portal_partner_ledger_pdf(self, date_begin=None, date_end=None, journal_type=None, outstanding_only=False, sortby=None, **kw):
        # Convert outstanding_only from string to boolean if needed
        if isinstance(outstanding_only, str):
            outstanding_only = outstanding_only.lower() == 'true'
            
        # Get all ledger data without pagination for PDF
        values = self._get_partner_ledger_values(
            page=1, 
            date_begin=date_begin, 
            date_end=date_end, 
            journal_type=journal_type, 
            outstanding_only=outstanding_only, 
            sortby=sortby, 
            **kw
        )
        
        # Get partner info
        partner = request.env.user.partner_id
        
        # Add company info and report title
        values.update({
            'partner': partner,
            'company': request.env.company,
            'report_date': fields.Date.today(),
        })
        
        # Generate PDF using Qweb - updated for Odoo 18
        report_action = request.env.ref('partner_ledger_portal.action_report_partner_ledger').sudo()
        pdf_content = report_action._render_qweb_pdf(
            report_ref=report_action.report_name,
            data=values
        )[0]
        
        # Prepare the response with the PDF
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition', content_disposition(f'Partner_Ledger_{partner.name}_{date_begin}_to_{date_end}.pdf'))
        ]
        
        return request.make_response(pdf_content, headers=pdfhttpheaders)


