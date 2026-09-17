from odoo import models, fields, api, _


class PurchaseRegisterReportWizard(models.TransientModel):
    _name = "purchase.analysis.wizard"
    _description = " "


    y_name  = fields.Char()
    y_start_date = fields.Date('Start Date')
    y_end_date = fields.Date('End Date')


    # Calling report method
    def retrieve_register(self):
        return self.env['purchase.analysis.report'].purchase_register_query(self.y_start_date, self.y_end_date)
        

    # Validation for start date and end date
    @api.onchange('y_start_date','y_end_date')
    def date_validation(self):
        if self.y_start_date and self.y_end_date:
            if not self.y_start_date < self.y_end_date:
                self.y_end_date = False
                return {'warning': {
            'title': _('User Warning'),
            'message': _('Selected End Date must be greater than Selected Start Date!')
        }}
