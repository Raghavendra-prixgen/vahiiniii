from odoo import api, fields, models, _

class Crmleadcreateopportunity(models.Model):
    _inherit = 'crm.lead2opportunity.partner'
    _name='crm.creatsequencenumber'
    _description = 'crm.creatsequencenumber'
    
    def action_merge(self):
        self.ensure_one()
        merge_opportunity = self.opportunity_ids.merge_opportunity(self.user_id.id, self.team_id.id)
        if self.y_sequence_name:
            values['y_sequence_name'] = self.sequence_name
        # The newly created lead might be a lead or an opp: redirect toward the right view
        if merge_opportunity.type == 'opportunity':
            return merge_opportunity.redirect_opportunity_view()
        else:
            return merge_opportunity.redirect_lead_view()

    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        values = {'team_id': self.team_id.id,}
        if self.partner_id:
            values['partner_id'] = self.partner_id.id

        if self.y_sequence_name:
            values['y_sequence_name'] = self.y_sequence_name

        if self.name == 'merge':
            leads = self.with_context(active_test=False).opportunity_ids.merge_opportunity()
            if not leads.active:
                leads.write({'active': True, 'activity_type_id': False, 'lost_reason': False})
            if leads.type == "lead":
                values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
                self.with_context(active_ids=leads.ids)._convert_opportunity(values)
            elif not self._context.get('no_force_assignation') or not leads.user_id:
                values['user_id'] = self.user_id.id
                leads.write(values)
        else:
            leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
            self._convert_opportunity(values)

        sequence_name = self.env['crm.lead'].browse(values.get('y_sequence_name'))

        return leads[0].redirect_opportunity_view()




