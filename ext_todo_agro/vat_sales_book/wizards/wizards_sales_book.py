from datetime import datetime, timedelta
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

class SalesBook(models.TransientModel):
    _name = "sales.book"

    date_from = fields.Date(string='Desde:', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_to = fields.Date('Hasta:', default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_now = fields.Datetime(string='Date Now', default=lambda *a:datetime.now())

    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose')
    report = fields.Binary('Archivo Preparado:', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=50)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    currency_bs_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    currency_usd_id = fields.Many2one('res.currency', default= lambda self: self.env['res.currency'].search([('id', '=', 2)]))

    def print_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'vat_sales_book.sales_book',
            'report_type':"qweb-pdf"
            }

    def get_lines(self):
        xfind = self.env['account.move'].search([('type', 'in', ('out_invoice', 'out_refund', 'out_receipt')), ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'posted'), ('invoice_payment_state', '=', 'paid')])
        return xfind
    
        # *******************  REPORTE EN EXCEL ****************************

    def generate_xls_report(self):

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet(_('Sales Book'))
        fp = BytesIO()

        header_content_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170; align: horiz center;")
        sub_header_style = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170")
        sub_header_style_c = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center")
        sub_header_style_r = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz right")
        sub_header_content_style = xlwt.easyxf("font: name Helvetica size 10 px, height 170;")
        line_content_style = xlwt.easyxf("font: name Helvetica, height 170;")

        row = 0
        col = 0
        ws1.row(row).height = 500
        ws1.write_merge(row,row, 6, 7, _("Libro de Ventas"), header_content_style)
        xdate = self.date_now.strftime('%d/%m/%Y %I:%M:%S %p')
        xdate = datetime.strptime(xdate,'%d/%m/%Y %I:%M:%S %p') - timedelta(hours=4)
        xname = self.company_id.name
        xvat = self.company_id.vat
        ws1.write_merge(row,row, 0, 1, xname, header_content_style)
        ws1.write_merge(row,row, 2, 3, xvat, header_content_style)
        ws1.write_merge(row,row, 10, 11, xdate.strftime('%d/%m/%Y %I:%M:%S %p'), header_content_style)
        row += 2

        #CABECERA DE LA TABLA 
        ws1.col(col).width = 250
        ws1.write_merge(row,row, 0, 8, ("Identificación de la Factura"), sub_header_style_c)
        ws1.write(row,col+9, _(" "),sub_header_style_c)
        ws1.col(col+9).width = int((len(' ')+10)*256)
        ws1.write(row,col+10, _(" "),sub_header_style_c)
        ws1.col(col+10).width = int((len(' ')+10)*256)
        ws1.write_merge(row,row, 11, 13, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 14, 16, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 17, 19, (" "), sub_header_style)
        row += 1
        ws1.write(row,col+0, _("Fecha"),sub_header_style_c)
        ws1.col(col+0).width = int((len('xx/xx/xxxx')+10)*256)
        ws1.write(row,col+1, _("Control"),sub_header_style_c)
        ws1.col(col+1).width = int((len('Control')+10)*256)
        ws1.write_merge(row,row, 2, 5, ("Documento"), sub_header_style_c)
        ws1.write(row,col+6, _(" "),sub_header_style_c)
        ws1.col(col+6).width = int((len(' ')+10)*256)
        ws1.write(row,col+7, _(" "),sub_header_style_c)
        ws1.col(col+7).width = int((len(' ')+10)*256)
        ws1.write(row,col+8, _(" "),sub_header_style_c)
        ws1.col(col+8).width = int((len(' ')+10)*256)
        ws1.write(row,col+9, _(" "),sub_header_style_c)
        ws1.col(col+9).width = int((len(' ')+10)*256)
        ws1.write(row,col+10, _(" "),sub_header_style_c)
        ws1.col(col+10).width = int((len(' ')+10)*256)
        ws1.write_merge(row,row, 11, 13, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 14, 16, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 17, 19, (" "), sub_header_style)
        row += 1
        ws1.write_merge(row,row, 0, 2, _("Factura"),sub_header_style_c)
        ws1.write(row,col+3, _("N/ Crédito"),sub_header_style_c)
        ws1.col(col+3).width = int((len('N/ Crédito')+10)*256)
        ws1.write(row,col+4, _("N/ Débito"),sub_header_style_c)
        ws1.col(col+4).width = int((len('N/ Débito')+10)*256)
        ws1.write(row,col+5, _("Factura Afectada"),sub_header_style_c)
        ws1.col(col+5).width = int((len('Factura Afectada')+20)*256)
        ws1.write(row,col+6, _("Tipo Reg."),sub_header_style_c)
        ws1.col(col+6).width = int((len('Tipo Reg.')+20)*256)
        ws1.write(row,col+7, _("Nombre - Razón Social del Cliente"),sub_header_style_c)
        ws1.col(col+7).width = int((len('Nombre - Razón Social del Cliente')+20)*256)
        ws1.write(row,col+8, _("R.I.F. Nro"),sub_header_style_c)
        ws1.col(col+8).width = int((len('R.I.F. Nro')+26)*256)
        ws1.write(row,col+9, _("Tipo Per."),sub_header_style_c)
        ws1.col(col+9).width = int((len('Tipo Per.')+26)*256)
        ws1.write(row,col+10, _("Total Ventas (Incluye I.V.A.)"),sub_header_style_c)
        ws1.col(col+10).width = int((len('Total Ventas (Incluye I.V.A.)')+26)*256)
        ws1.write(row,col+11, _("Exento"),sub_header_style_c)
        ws1.col(col+11).width = int((len('Extento')+10)*356)
        ws1.write(row,col+12, _("%"),sub_header_style_c)
        ws1.col(col+12).width = int((len('%')+10)*256)
        ws1.write(row,col+13, _("Impuesto"),sub_header_style_c)
        ws1.col(col+13).width = int((len('Impuesto')+10)*256)
        ws1.write(row,col+14, _("Base"),sub_header_style_c)
        ws1.col(col+14).width = int((len('Base')+10)*256)
        ws1.write(row,col+15, _("%"),sub_header_style_c)
        ws1.col(col+15).width = int((len('%')+10)*256)
        ws1.write(row,col+16, _("Impuesto"),sub_header_style_c)
        ws1.col(col+16).width = int((len('Tax')+10)*256)
        ws1.write(row,col+17, _("Retención de I.V.A."),sub_header_style_c)
        ws1.col(col+17).width = int((len('Retención de I.V.A.')+10)*256)
        ws1.write(row,col+18, _("Nro. Comprobante"),sub_header_style_c)
        ws1.col(col+18).width = int((len('Nro. Comprobante')+10)*256)
        ws1.write(row,col+19, _("Fecha del Comprobante"),sub_header_style_c)
        ws1.col(col+19).width = int((len('xx/xx/xxxx')+10)*256)
        center = xlwt.easyxf("align: horiz center")
        right = xlwt.easyxf("align: horiz right")

        #Totales
        total_sales = 0.00
        total_exempt_sales = 0.00
        total_general_tax_base_tax_amount = 0.00
        total_vat_general_tax = 0.00
        total_withheld = 0.00
        general_total_base = 0.00
        general_total_credit = 0.00
        general_total_withheld = 0.00

        for item in self.get_lines():
            row += 2
            # Fecha
            if item.date:
                ws1.write(row,col+0, item.date.strftime('%d/%m/%Y'),sub_header_style_c)
            else:
                ws1.write(row,col+0, '',sub_header_style_c)
            # Control
            if item.type == 'out_invoice':
                if item.invoice_ctrl_number_pro:
                    ws1.write(row,col+1, item.invoice_ctrl_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+1, '',sub_header_style_c)
            elif item.type == 'out_refund':
                if item.refund_ctrl_number_pro:
                    ws1.write(row,col+1, item.refund_ctrl_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+1, '',sub_header_style_c)
            elif item.type == 'out_receipt':
                if item.refund_ctrl_number_pro:
                    ws1.write(row,col+1, item.refund_ctrl_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+1, '',sub_header_style_c)
            else:
                ws1.write(row,col+1, '',sub_header_style_c)
            # Factura
            if item.type == 'out_invoice':
                if item.invoice_number_pro:
                    ws1.write(row,col+2, item.invoice_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+2, '',sub_header_style_c)
            elif item.type == 'out_refund':
                if item.refuld_number_pro:
                    ws1.write(row,col+2, item.refuld_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+2, '',sub_header_style_c)
            elif item.type == 'out_receipt':
                if item.refuld_number_pro:
                    ws1.write(row,col+2, item.refuld_number_pro,sub_header_style_c)
                else:
                    ws1.write(row,col+2, '',sub_header_style_c)
            else:
                ws1.write(row,col+2, '',sub_header_style_c)
            # N/ Crédito
            if item.type == 'out_refund':
                if item.name:
                    ws1.write(row,col+3, item.name,sub_header_style_c)
                else:
                    ws1.write(row,col+3, '',sub_header_style_c)
            else:
                ws1.write(row,col+3, '',sub_header_style_c)
            # N/ Débito
            if item.type == 'out_receipt':
                if item.name:
                    ws1.write(row,col+4, item.name,sub_header_style_c)
                else:
                    ws1.write(row,col+4, '',sub_header_style_c)
            else:
                ws1.write(row,col+4, '',sub_header_style_c)
            # Factura Afectada
            if item.type in ('out_refund', 'out_receipt'):
                if item.ref:
                    ws1.write(row,col+5, item.ref,sub_header_style_c)
                else:
                    ws1.write(row,col+5, '',sub_header_style_c)
            else:
                ws1.write(row,col+5, '',sub_header_style_c)
            # Tipo Reg.
                if item.type == 'out_invoice':
                    ws1.write(row,col+6, '01-Reg',sub_header_style_c)
                elif item.type == 'out_refund':
                    ws1.write(row,col+6, '02-Reg',sub_header_style_c)
                elif item.type == 'out_receipt':
                    ws1.write(row,col+6, '03-Reg',sub_header_style_c)
                else:
                    ws1.write(row,col+6, '',sub_header_style_c)
            # "Nombre - Razón Social del Cliente
            if item.partner_id.name:
                ws1.write(row,col+7, item.partner_id.name,sub_header_style_c)
            else:
                ws1.write(row,col+7, '',sub_header_style_c)
            # R.I.F. Nro
            if item.partner_id.vat:
                ws1.write(row,col+8, item.partner_id.vat,sub_header_style_c)
            else:
                ws1.write(row,col+8, '',center)
            # Tipo Per.
            if item.partner_id.people_type == 'resident_nat_people':
                ws1.write(row,col+9, 'PNRE',sub_header_style_c)
            elif item.partner_id.people_type == 'non_resit_nat_people':
                ws1.write(row,col+9, 'PNNR',sub_header_style_c)
            elif item.partner_id.people_type == 'domi_ledal_entity':
                ws1.write(row,col+9, 'PJDO',sub_header_style_c)
            elif item.partner_id.people_type == 'legal_ent_not_domicilied':
                ws1.write(row,col+9, 'PJND',sub_header_style_c)
            else:
                ws1.write(row,col+9, '',sub_header_style_c)
            for obj in item.alicuota_line_ids:
                # Total Ventas (Incluye I.V.A.)
                if obj.total_con_iva:
                    ws1.write(row,col+10, obj.total_con_iva,sub_header_style_r)
                else:
                    ws1.write(row,col+10, '',sub_header_style_r)
                # Exento
                if obj.total_exento: 
                    ws1.write(row,col+11, obj.total_exento,sub_header_style_r)
                else:
                    ws1.write(row,col+11, '0,00',sub_header_style_r)
                # %
                if obj.tax_id:
                    ws1.write(row,col+12, '',sub_header_style_r)
                else:
                    ws1.write(row,col+12, '',sub_header_style_r)
                # Impuesto
                if obj.alicuota_general:
                    ws1.write(row,col+13, '',sub_header_style_r)
                else:
                    ws1.write(row,col+13, '',sub_header_style_r)
                # Base
                if obj.base_general:
                    ws1.write(row,col+14, obj.base_general,sub_header_style_r)
                else:
                    ws1.write(row,col+14, '',sub_header_style_r)
                # %
                if obj.tax_id.amount:
                    ws1.write(row,col+15, obj.tax_id.amount,sub_header_style_r)
                else:
                    ws1.write(row,col+15, '',sub_header_style_r)
                # Impuesto
                if obj.alicuota_general:
                    ws1.write(row,col+16, obj.alicuota_general,sub_header_style_r)
                else:
                    ws1.write(row,col+16, '',sub_header_style_r)
                # Retención de I.V.A.
                if obj.total_ret_iva:
                    ws1.write(row,col+17, obj.total_ret_iva,sub_header_style_r)
                else:
                    ws1.write(row,col+17, '',sub_header_style_r)
                for vat in obj.vat_ret_id:
                    # Nro. Comprobante
                    if vat.name:
                        ws1.write(row,col+18, vat.name,sub_header_style_c)
                    else:
                        ws1.write(row,col+18, '',sub_header_style_c)
                    # Fecha del Comprobante
                    if vat.voucher_delivery_date:
                        ws1.write(row,col+19, vat.voucher_delivery_date.strftime('%d/%m/%Y'),sub_header_style_c)
                    else:
                        ws1.write(row,col+19, '',sub_header_style_c)

                total_sales += obj.total_con_iva
                total_exempt_sales += obj.total_exento
                total_general_tax_base_tax_amount += obj.base_general
                total_vat_general_tax += obj.alicuota_general
                total_withheld += obj.total_ret_iva

        general_total_base += total_exempt_sales + total_general_tax_base_tax_amount
        general_total_credit += total_vat_general_tax
        general_total_withheld += total_withheld

        row += 1
        ws1.write_merge(row,row, 0, 9, ("Total Ventas al: " + self.date_to.strftime('%d/%m%Y')), sub_header_style_c)
        ws1.write(row,col+10, total_sales,sub_header_style_r)
        ws1.write(row,col+11, total_exempt_sales,sub_header_style_r)
        ws1.write(row,col+12, '',sub_header_style_r)
        ws1.write(row,col+13, '',sub_header_style_r)
        ws1.write(row,col+14, total_general_tax_base_tax_amount,sub_header_style_r)
        ws1.write(row,col+15, '',sub_header_style_r)
        ws1.write(row,col+16, total_vat_general_tax,sub_header_style_r)
        ws1.write(row,col+17, total_withheld,sub_header_style_r)

        row += 2
        ws1.write_merge(row,row, 0, 1, (" "), center)
        ws1.write_merge(row,row, 2, 3, ("Débito Fiscal"), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, ("Retención de I.V.A."), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Total: Ventas Exentas y/o sin derecho a crédito fiscal"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Importación Afectas sólo Alícuota General"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Importación Afectas en Alícuota General + Adicional"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Importación Afectas en Alícuota Reducida"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Internas Afectas sólo Alícuota General"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, total_vat_general_tax, sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Internas Afectas en Alícuota General + Adicional"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ de las: Ventas Internas Afectas en Alícuota Reducida"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, (" "), center)
        ws1.write_merge(row,row, 2, 3, general_total_credit, sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, general_total_withheld, sub_header_style_r)

        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        fecha  = datetime.now().strftime('%d/%m/%Y') 
        self.write({'state': 'get', 'report': out, 'name': _('Libro de Ventas ')+ fecha +'.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sales.book',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }