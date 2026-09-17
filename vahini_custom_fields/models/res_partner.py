from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('street', 'street2', 'zip', 'city', 'state_id', 'country_id')
    def _compute_complete_address(self):
        for record in self:
            address_parts = []
            if record.street:
                address_parts.append(record.street)
            if record.street2:
                address_parts.append(record.street2)
            if record.zip or record.city:
                zip_city = f"{record.zip or ''} {record.city or ''}".strip()
                address_parts.append(zip_city)
            if record.state_id:
                address_parts.append(record.state_id.name)
            if record.country_id:
                address_parts.append(record.country_id.name)

            record.contact_address_complete = ', '.join([part for part in address_parts if part])
            
            

