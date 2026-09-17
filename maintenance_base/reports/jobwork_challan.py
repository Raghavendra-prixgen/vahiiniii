# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models,_
from odoo.tools import date_utils, groupby as groupbyelem
from operator import itemgetter


class report_jobwork_challan(models.AbstractModel):
    _name = 'report.maintenance_base.report_jobwork_challan'
    _description = 'Jobwork Challan'

    def _get_report_values(self, docids, data):
        docs = self.env['maintenance.request'].browse(docids)
        if len(docs) > 1:
            sequence = self.env['ir.sequence'].browse(self.env.ref('maintenance_base.jobwork_challan_number_sequence').id).next_by_id()
            for each in docs:
                if each.stage_id.job_work:
                    if each.jobwork_challan_no == '/':
                        each.jobwork_challan_no = sequence
        else:
            for each in docs:
                if each.stage_id.job_work:
                    if each.jobwork_challan_no == '/':
                        sequence = self.env['ir.sequence'].browse(self.env.ref('maintenance_base.jobwork_challan_number_sequence').id)
                        each.jobwork_challan_no = sequence.next_by_id()

        grouped_docs  = [g for k, g in groupbyelem(docs, itemgetter('jobwork_challan_no'))]
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'maintenance.request',
            'docs': grouped_docs,
        }