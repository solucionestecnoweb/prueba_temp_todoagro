# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from itertools import product
from operator import mod
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ConsignmentProductWizard(models.TransientModel):
    _name = "consignment.product.wizard"

    from_date = fields.Date(string='Desde', required=True ,default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date('Hasta', required=True ,default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))

    def print_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'consignment_product_report.report_consignment_product',
            'report_type':'qweb-pdf',
            'data':None,
            }

    def retorna_fecha(self):
        return {'from':self.from_date,
            'to':self.to_date}

    def retorna_facturas_proveedor(self):
        return self.env['account.move'].search([('type', '=', 'in_invoice'),
            ('date', '>=', self.from_date),('date', '<=', self.to_date),])

class ProductTemplate(models.Model):
    _inherit = "product.template"

    check_consignment = fields.Boolean("Por consignación")
