from odoo import api,models,fields, _
from odoo.exceptions import UserError
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


class ReportJobworkChallan(models.AbstractModel):
    _inherit = 'report.maintenance_base.report_jobwork_challan'

    def _get_report_values(self, docids, data):
        docs = self.env['maintenance.request'].browse(docids)
        if len(set(docs.mapped('y_purchase_order'))) > 1:
            raise UserError(_('Please select Material request having same purchase order reference'))

        # --- NOT calling super() anymore, since base's _get_report_values
        #     contains the jobwork_challan_no sequence-generation logic ---

        grouped_docs = [g for k, g in groupbyelem(docs, itemgetter('jobwork_challan_no'))]
        return {
            'doc_ids': docs.ids,
            'doc_model': 'maintenance.request',
            'docs': grouped_docs,
        }
    

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq_id = self.env['ir.config_parameter'].sudo().get_param(
            'maintenance_integ_with_purchase.jobwork_challan_sequence_id')
        sequence = self.env['ir.sequence'].browse(int(seq_id)) if seq_id else self.env['ir.sequence']

        for rec in records:
            rec.jobwork_challan_no = sequence.next_by_id() if sequence else \
                self.env['ir.sequence'].next_by_code('maintenance.jobwork.challan.number')
        return records


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    job_work_sequence_id = fields.Many2one(
        'ir.sequence',
        string="Jobwork Sequence",
        config_parameter='maintenance_integ_with_purchase.jobwork_challan_sequence_id',
    )