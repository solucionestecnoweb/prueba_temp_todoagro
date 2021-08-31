import json
from datetime import datetime, timedelta
import base64
from io import StringIO
from odoo import api, fields, models, _
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning
import time

class Rate(models.Model):
    _inherit = 'res.partner'

    rate = fields.Float (string="Rate")

class Suppliers(models.Model):
    _inherit ='account.move'

    rate = fields.Float(string='Rate', related='partner_id.rate')
    converted = fields.Monetary(string="Converted Amount", currency_field='final_currency_id', compute="calculate")
    final_currency_id = fields.Many2one ('res.currency', default= lambda self: self.env['res.currency'].search([('id', '=', 2)]))
    
    def calculate(self):
        if (self.rate > 0):
            if(self.currency_id.name == 'USD' or self.currency_id.name == 'EUR'):
                self.converted = self.amount_total * self.rate
            
            elif (self.currency_id.name == 'VEF' or self.currency_id.name == 'VES'):
                self.converted = self.amount_total / self.rate
        else:
            if(self.currency_id.name == 'USD' or self.currency_id.name == 'EUR'):
                self.converted = self.amount_total * 1
            
            elif (self.currency_id.name == 'VEF' or self.currency_id.name == 'VES'):
                self.converted = self.amount_total / 1