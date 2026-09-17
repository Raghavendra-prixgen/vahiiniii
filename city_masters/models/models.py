# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools import email_split
import logging
import threading
from datetime import date, datetime, timedelta
from psycopg2 import sql

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict, defaultdict

import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit="res.partner"

    y_city_id = fields.Many2one(comodel_name='res.city',string='Taluk')
    y_district_id=fields.Many2one(comodel_name='res.district',string='district')
    

    @api.onchange('y_city_id','y_district_id','state_id')
    def set_state_country_details(self):
        if self.y_city_id:
            self.y_district_id=self.y_city_id.y_district_id.id
            self.state_id = self.y_city_id.y_state_id.id
            self.country_id = self.y_city_id.y_country_id.id
            self.city = self.y_city_id.y_name

# concate the ref and customer name ie parent_id.name by sh
    def name_get(self):
        res = []
        for rec in self:
            if rec.ref:
                res.append((rec.id, "[%s] %s" % (rec.ref or " ", rec.name)))
            else:
                res.append((rec.id, "%s" % rec.name))
        return res
 
class District(models.Model):
    _name = 'res.district'
    _description = "RES DISTRICT"
    _rec_name = 'y_name'

    y_name = fields.Char(string='Name', required=True)
    y_country_id = fields.Many2one(comodel_name='res.country', string='Country')
    y_state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    

class City(models.Model):
    _name = 'res.city'
    _description = "RES CITY"
    _rec_name = 'y_name'
    
    
    y_name = fields.Char(string='Name', required=True)
    y_country_id = fields.Many2one(comodel_name='res.country', string='Country')
    y_state_id = fields.Many2one(comodel_name='res.country.state', string='State')
    y_district_id = fields.Many2one(comodel_name='res.district', string='District')

    @api.onchange('y_district_id','state_id')
    def set_city_country_details(self):
        if self.y_district_id:


            # self.y_district_id=self.y_city_id.y_district_id.id
            self.y_state_id = self.y_district_id.y_state_id.id
            self.y_country_id = self.y_district_id.y_country_id.id



class CrmLead(models.Model):
    _inherit =  "crm.lead"

    
    y_city_id = fields.Many2one(comodel_name='res.city',string='Taluk ')
    y_district_id=fields.Many2one(comodel_name='res.district',string='District')
   
    @api.onchange('y_city_id','y_district_id','state_id')
    def set_state_country_details(self):
        if self.y_city_id:
            self.y_district_id=self.y_city_id.y_district_id.id
            self.state_id = self.y_city_id.y_state_id.id
            self.country_id = self.y_city_id.y_country_id.id
            self.city = self.y_city_id.y_name


    def _handle_partner_assignment(self, force_partner_id=False, create_missing=True):
        for lead in self:
            if not lead.partner_id and create_missing:
                partner = lead._create_customer()
                lead.partner_id = partner.parent_id.id
        res = super()._handle_partner_assignment(force_partner_id=force_partner_id, create_missing=create_missing)   
        return res
                
                   
     
     
    
    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super()._prepare_customer_values(partner_name, is_company=is_company, parent_id=parent_id)
        
        if is_company == False:
            res.update({
                'y_city_id':self.y_city_id.id,
                'y_district_id':self.y_district_id.id,
            })
            return res
        else:
            res.update({
                'y_city_id': self.y_city_id.id,
                'y_district_id':self.y_district_id.id,
            })
            return res
        

        
   

   