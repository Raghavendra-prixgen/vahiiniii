# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command


class FollowupManualReminder(models.TransientModel):
    _inherit = 'account_followup.manual_reminder'

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        assert self.env.context['active_model'] == 'res.partner'
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        partner.ensure_one()
        followup_line = partner.followup_line_id
        if followup_line:
            defaults.update(
                email=followup_line.send_email,
                sms=followup_line.send_sms,
                template_id=followup_line.mail_template_id.id,
                sms_template_id=followup_line.sms_template_id.id,
                join_invoices=followup_line.join_invoices,
            )
        defaults.update(
            partner_id=partner.id,
            attachment_ids=[Command.set(partner._get_included_unreconciled_aml_ids().move_id.message_main_attachment_id.ids)],
            render_model='res.partner'
        )
        return defaults
