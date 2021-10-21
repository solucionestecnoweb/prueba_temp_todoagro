from datetime import datetime, timedelta
from itertools import product
from operator import mod
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import logging

import io
from io import BytesIO

import xlsxwriter
import shutil
import base64
import csv
import xlwt

_logger = logging.getLogger(__name__)

class CostEffectivenessData(models.Model):
    _name = 'cost.effectiveness.data'

    product = fields.Char(string='Product Name')
    quantity = fields.Float(string='Quantity')
    costo = fields.Float(string='Total Cost Price')
    ingreso = fields.Float(string='Amount')
    margen_ganacia = fields.Float(string='Profitability Margin')
    dif_bs = fields.Float(string='Dif Bs')
    dif_usd = fields.Float(string='Dif USD')

class CostEffectiveness(models.TransientModel):
    _name = "cost.effectiveness"

    date_from = fields.Date(string='Desde', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_to = fields.Date('Hasta', default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_now = fields.Datetime(string='Fecha Actual', default=lambda *a:datetime.now())
    date_today = fields.Date(string='Fecha de Hoy', default=datetime.today())
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.user.company_id.currency_id.id)
    categ_id = fields.Many2many('product.category', string='Categoría')
    product_id = fields.Many2many('product.product', string='Producto')

    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose')
    report = fields.Binary('Archivo Preparado', filters='.xls', readonly=True)
    name = fields.Char('Nombre del Archivo', size=50)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    lines_ids = fields.Many2many(comodel_name='cost.effectiveness.data', string='Lines')
    

    def print_report(self):
        self.get_data()
        return {
            'type': 'ir.actions.report',
            'report_name': 'cost_effectiveness_report.cost_effectiveness',
            'report_type':"qweb-pdf"
            }

    def get_data(self):
        xfind = self.get_lines()

        t = self.env['cost.effectiveness.data']
        t.search([]).unlink()
        prod = ''
        for item in xfind.sorted(key=lambda x: x.product_id.id):
            
            quantity = 0
            costo = 0
            ingreso = 0
            margen_ganacia = 0
            dif_bs = 0
            dif_usd = 0

            cost_bs = 0
            sale_price_bs = 0                  
            costo_venta_bs = 0
            cost_usd = 0
            sale_price_usd = 0   
            costo_venta_usd = 0


            if prod != item.product_id.id:
                prod = item.product_id.id

                prods = self.env['sale.order.line'].search([
                    ('order_id.date_order', '>=', self.date_from),
                    ('order_id.date_order', '<=', self.date_to),
                    ('order_id.state', '=', 'sale'),
                    ('product_id', '=', item.product_id.id)
                ])

                for line in prods:
                    rate = self.env['res.currency.rate'].search([('name', '=', self.date_today)], limit=1).sell_rate
                    if not rate:
                        rate = 1
                    if self.currency_id.id == 3:
                        quantity += line.product_uom_qty
                        cost_bs += line.product_id.standard_price    
                        sale_price_bs +=  line.price_unit                  
                        costo_venta_bs = cost_bs + sale_price_bs
                        costo = cost_bs * quantity
                        ingreso = costo_venta_bs * quantity
                        margen_ganacia = (((ingreso - costo)/costo)*100)
                        dif_bs = ingreso - costo
                        dif_usd = 0
                    else:
                        quantity += line.product_uom_qty
                        cost_usd += line.product_id.standard_price / rate
                        sale_price_usd +=  line.price_unit / rate         
                        costo_venta_usd = cost_usd + sale_price_usd
                        costo = cost_usd * quantity
                        ingreso = costo_venta_usd * quantity
                        margen_ganacia = (((ingreso - costo)/costo)*100)
                        dif_usd = (ingreso - costo)
                        dif_bs = 0

                values = {
                    'product': item.product_id.name,
                    'quantity': quantity,
                    'costo': costo,
                    'ingreso': ingreso,
                    'margen_ganacia': margen_ganacia,
                    'dif_bs': dif_bs,
                    'dif_usd': dif_usd,
                }
                t.create(values)
        self.lines_ids = t.search([])

    def get_lines(self):
        if self.product_id:
            prod = []
            for item in self.product_id:
                prod.append(item.id)
            pfind = self.env['product.product'].search([
                        ('type', '=', 'product'),
                        ('id', 'in', prod)
                    ])
        else:
            categ = []
            for item in self.categ_id:
                categ.append(item.id)
            pfind = self.env['product.product'].search([
                        ('type', '=', 'product'),
                        ('categ_id', 'in', categ)
                    ])
        
        products = []
        for item in pfind:
            products.append(item.id)
        
        xfind = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('order_id.state', '=', 'sale'),
            ('product_id', 'in', products)

        ])
        
        return xfind

# *******************  REPORTE EN EXCEL ****************************

    def generate_xls_report(self):
        self.env['cost.effectiveness.data'].search([]).unlink()
        self.get_data()

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet(_('Margen de Rentabilidad en Ventas'))
        fp = BytesIO()

        header_tittle_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170; align: horiz center, vert centre;")
        header_content_style = xlwt.easyxf("font: name Helvetica size 16 px, bold 1, height 170; align: horiz center, vert centre; pattern:pattern solid, fore_colour silver_ega;")
        lines_style_center = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: bottom thin; align: horiz center, vert centre;")
        lines_style_right = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: bottom thin; align: horiz right, vert centre;")
        
        table_style_center = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center, vert centre;")
        table_style_right = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz right, vert centre;")

        row = 0
        col = 0
        ws1.row(row).height = 500

        #CABECERA DEL REPORTE
        ws1.write_merge(row,row, 2, 3, self.company_id.name, header_tittle_style)
        xdate = self.date_now.strftime('%d/%m/%Y %I:%M:%S %p')
        xdate = datetime.strptime(xdate,'%d/%m/%Y %I:%M:%S %p') - timedelta(hours=4)
        ws1.write_merge(row,row, 5, 6, xdate.strftime('%d/%m/%Y %I:%M:%S %p'), header_tittle_style)
        row += 1
        ws1.write_merge(row,row, 2, 3, 'R.I.F. ' + self.company_id.vat, header_tittle_style)
        row += 1
        ws1.write_merge(row,row, 2, 3, _("Margen de Rentabilidad en Ventas"), header_tittle_style)
        row += 1
        ws1.write_merge(row,row, 2, 3, _('Desde: ') + self.date_from.strftime('%d/%m/%Y') + _(' Hasta: ') + self.date_to.strftime('%d/%m/%Y'), header_tittle_style)
        row += 2

        #CABECERA DE LA TABLA 
        ws1.write(row,col+0, _("Producto"),header_content_style)
        ws1.col(col+0).width = int((len('Producto')+10)*256)
        ws1.write(row,col+1, _("Cantidad Vendida"),header_content_style)
        ws1.col(col+1).width = int((len('Cantidad Vendida')+0)*256)
        ws1.write(row,col+2, _("Costo"),header_content_style)
        ws1.col(col+2).width = int((len('Costo')+10)*256)
        ws1.write(row,col+3, _("Ingreso Total"),header_content_style)
        ws1.col(col+3).width = int((len('Ingreso Total')+2)*256)
        ws1.write(row,col+4, _("Margen de Rentabilidad"),header_content_style)
        ws1.col(col+4).width = int((len('Margen de Rentabilidad')+2)*256)
        ws1.write(row,col+5, _("Dif en $"),header_content_style)
        ws1.col(col+5).width = int((len('Dif en $')+2)*256)
        ws1.write(row,col+6, _("Dif en Bs"),header_content_style)
        ws1.col(col+6).width = int((len('Dif en Bs')+2)*256)


        #LINEAS
        for item in self.lines_ids:
            row += 1
            # Producto
            if item.product:
                ws1.write(row,col+0, item.product,lines_style_center)
            else:
                ws1.write(row,col+0, '',lines_style_center)
            # Cantidad Vendida
            if item.quantity:
                ws1.write(row,col+1, item.quantity,lines_style_center)
            else:
                ws1.write(row,col+1, '',lines_style_center)
            # Costo
            if item.costo:
                ws1.write(row,col+2, item.costo,lines_style_right)
            else:
                ws1.write(row,col+2, '',lines_style_center)
            # Ingreso Total
            if item.ingreso:
                ws1.write(row,col+3, item.ingreso,lines_style_right)
            else:
                ws1.write(row,col+3, '',lines_style_center)
            # Margen de Rentabilidad
            if item.margen_ganacia:
                ws1.write(row,col+4, item.margen_ganacia,lines_style_center)
            else:
                ws1.write(row,col+4, '',lines_style_center)
            # Dif USD
            if self.currency_id.name == 'USD':
                ws1.write(row,col+5, item.dif_usd,lines_style_right)
            else:
                ws1.write(row,col+5, '',lines_style_center)
            # Dif Bs
            if self.currency_id.id == 3:
                ws1.write(row,col+6, item.dif_bs,lines_style_right)
            else:
                ws1.write(row,col+6, '',lines_style_center)

        #IMPRESIÓN
        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        fecha  = datetime.now().strftime('%d/%m/%Y') 
        self.write({'state': 'get', 'report': out, 'name': _('Margen de Rentabilidad en Ventas ')+ fecha +'.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cost.effectiveness',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }