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

class PurchaseBook(models.TransientModel):
    _name = "purchase.book"

    date_from = fields.Date(string='Date From', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_to = fields.Date('Date To', default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_now = fields.Datetime(string='Date Now', default=lambda *a:datetime.now())

    state = fields.Selection([('choose', 'choose'), ('get', 'get')],default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=50)
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    currency_bs_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    currency_usd_id = fields.Many2one('res.currency', default= lambda self: self.env['res.currency'].search([('id', '=', 2)]))

    def print_report(self):
        return {
            'type': 'ir.actions.report',
            'report_name': 'vat_purchase_book.purchase_book',
            'report_type':"qweb-pdf"
            }

    def get_lines(self):
        xfind = self.env['account.move'].search([('type', 'in', ('in_invoice', 'in_receive', 'in_receipt')), ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', 'posted')])
        return xfind
    
        # *******************  REPORTE EN EXCEL ****************************

    def generate_xls_report(self):

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet(_('Purchase Book'))
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
        ws1.write_merge(row,row, 6, 7, _("Purchase Book"), header_content_style)
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
        ws1.write_merge(row,row, 0, 11, (" "), sub_header_style)
        ws1.write(row,col+12, _("Non-Credit Purchases"),sub_header_style_c)
        ws1.col(col+12).width = int((len('Non-Credit Purchases')+60)*356)
        ws1.write_merge(row,row, 13, 19, ("Credit Right Purchases"), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 10, ("Invoice Identification"), sub_header_style_c)
        ws1.write(row,col+11, _(" "),sub_header_style_c)
        ws1.col(col+11).width = int((len(' ')+10)*256)
        ws1.write(row,col+12, _("Non-Taxed Purchases"),sub_header_style_c)
        ws1.col(col+12).width = int((len('Non-Taxed Purchases')+60)*356)
        ws1.write_merge(row,row, 13, 15, ("Export Purchases"), sub_header_style_c)
        ws1.write_merge(row,row, 16, 19, ("Internal Purchases"), sub_header_style_c)
        row += 1
        ws1.write(row,col+0, _("Date"),sub_header_style_c)
        ws1.col(col+0).width = int((len('xx/xx/xxxx')+10)*256)
        ws1.write(row,col+1, _("Control Number"),sub_header_style_c)
        ws1.col(col+1).width = int((len('Control Number')+20)*256)        
        ws1.write(row,col+2, _("Bill"),sub_header_style_c)
        ws1.col(col+2).width = int((len('Bill')+10)*256)
        ws1.write(row,col+3, _("Credit N/"),sub_header_style_c)
        ws1.col(col+3).width = int((len('Credit N/')+10)*256)
        ws1.write(row,col+4, _("Debit N/"),sub_header_style_c)
        ws1.col(col+4).width = int((len('Debit N/')+10)*256)
        ws1.write(row,col+5, _("Doc Number"),sub_header_style_c)
        ws1.col(col+5).width = int((len('Doc Number')+10)*256)
        ws1.write(row,col+6, _("Transaction Type"),sub_header_style_c)
        ws1.col(col+6).width = int((len('Transaction Type')+20)*256)
        ws1.write(row,col+7, _("Affected Invoice Number"),sub_header_style_c)
        ws1.col(col+7).width = int((len('Affected Invoice Number')+20)*256)
        ws1.write(row,col+8, _("Name - Supplier's Social Reason"),sub_header_style_c)
        ws1.col(col+8).width = int((len('Name - Suppliers Social Reason')+20)*256)
        ws1.write(row,col+9, _("R.I.F. Number"),sub_header_style_c)
        ws1.col(col+9).width = int((len('R.I.F. Number')+26)*256)
        ws1.write(row,col+10, _("Supplier Type"),sub_header_style_c)
        ws1.col(col+10).width = int((len('Supplier Type')+26)*256)
        ws1.write(row,col+11, _("Total Purchases (Includes VAT)"),sub_header_style_c)
        ws1.col(col+11).width = int((len('Total Purchases (Includes VAT)')+26)*256)
        ws1.write(row,col+12, _("Exempt"),sub_header_style_c)
        ws1.col(col+12).width = int((len('Exempt')+10)*356)
        ws1.write(row,col+13, _("Base"),sub_header_style_c)
        ws1.col(col+13).width = int((len('Base')+15)*256)
        ws1.write(row,col+14, _("%"),sub_header_style_c)
        ws1.col(col+14).width = int((len('%')+10)*256)
        ws1.write(row,col+15, _("Tax"),sub_header_style_c)
        ws1.col(col+15).width = int((len('Tax')+10)*256)
        ws1.write(row,col+16, _("Base"),sub_header_style_c)
        ws1.col(col+16).width = int((len('Base')+10)*256)
        ws1.write(row,col+17, _("%"),sub_header_style_c)
        ws1.col(col+17).width = int((len('%')+10)*256)
        ws1.write(row,col+18, _("Tax"),sub_header_style_c)
        ws1.col(col+18).width = int((len('Tax')+10)*256)
        ws1.write(row,col+19, _("VAT Withholding Voucher (Date)"),sub_header_style_c)
        ws1.col(col+19).width = int((len('VAT Withholding Voucher (Date)')+10)*256)
        ws1.write(row,col+20, _("VAT Withholding Voucher (Number)"),sub_header_style_c)
        ws1.col(col+20).width = int((len('VAT Withholding Voucher (Number)')+10)*256)
        center = xlwt.easyxf("align: horiz center")
        right = xlwt.easyxf("align: horiz right")

        #Totales
        total_purchases = 0.00
        total_exempt_purchases = 0.00
        total_general_tax_base_tax_amount = 0.00
        total_vat_general_tax = 0.00
        general_total_base = 0.00
        general_total_credit = 0.00
        general_total_withheld = 0.00

        for item in self.get_lines():
            row += 2
            # Date
            if item.date:
                ws1.write(row,col+0, item.date.strftime('%d/%m/%Y'),sub_header_style_c)
            else:
                ws1.write(row,col+0, '',sub_header_style_c)
            # Control Number
            if item.invoice_ctrl_number_pro:
                ws1.write(row,col+1, item.invoice_ctrl_number_pro,sub_header_style_c)
            else:
                ws1.write(row,col+1, '',sub_header_style_c)
            # Bill
            if item.invoice_number_pro:
                ws1.write(row,col+2, item.invoice_number_pro,sub_header_style_c)
            else:
                ws1.write(row,col+2, '',sub_header_style_c)
            # Credit N/
            if item.invoice_number_pro:
                ws1.write(row,col+3, '',sub_header_style_c)
            else:
                ws1.write(row,col+3, '',sub_header_style_c)
            # Debit N/
            if item.invoice_number_pro:
                ws1.write(row,col+4, '',sub_header_style_c)
            else:
                ws1.write(row,col+4, '0',sub_header_style_c)
            # Doc Number
            if item.invoice_number_pro:
                ws1.write(row,col+5, item.invoice_number_pro,sub_header_style_c)
            else:
                ws1.write(row,col+5, '0',sub_header_style_c)
            # Affected Invoice Number
            if item.name:
                ws1.write(row,col+6, item.name,sub_header_style_c)
            else:
                ws1.write(row,col+6, '',sub_header_style_c)
            # Transaction Type
            if item.type_name:
                ws1.write(row,col+7, item.type_name,sub_header_style_c)
            else:
                ws1.write(row,col+7, '',sub_header_style_c)
            # Name - Supplier's Social Reason
            if item.partner_id.name:
                ws1.write(row,col+8, item.partner_id.name,sub_header_style_c)
            else:
                ws1.write(row,col+8, '',sub_header_style_c)
            # R.I.F. Number
            if item.partner_id.vat:
                ws1.write(row,col+9, item.partner_id.vat,sub_header_style_c)
            else:
                ws1.write(row,col+9, '',center)
            # Supplier Type
            if item.partner_id.vendor:
                ws1.write(row,col+10, item.partner_id.vendor,sub_header_style_c)
            else:
                ws1.write(row,col+10, '',sub_header_style_c)
            for obj in item.alicuota_line_ids:
                # Total Purchases (Includes VAT)
                if obj.total_con_iva:
                    ws1.write(row,col+11, obj.total_con_iva,sub_header_style_r)
                else:
                    ws1.write(row,col+11, '',sub_header_style_r)
                # Exempt
                if obj.total_exento: 
                    ws1.write(row,col+12, obj.total_exento,sub_header_style_r)
                else:
                    ws1.write(row,col+12, '0,00',sub_header_style_r)
                # Base
                if obj.base_general:
                    ws1.write(row,col+13, '',sub_header_style_r)
                else:
                    ws1.write(row,col+13, '',sub_header_style_r)
                # %
                if obj.tax_id:
                    ws1.write(row,col+14, '',sub_header_style_r)
                else:
                    ws1.write(row,col+14, '',sub_header_style_r)
                # Tax
                if obj.alicuota_general:
                    ws1.write(row,col+15, '',sub_header_style_r)
                else:
                    ws1.write(row,col+15, '',sub_header_style_r)
                # Base
                if obj.base_general:
                    ws1.write(row,col+16, obj.base_general,sub_header_style_r)
                else:
                    ws1.write(row,col+16, '',sub_header_style_r)
                # %
                if obj.tax_id.amount:
                    ws1.write(row,col+17, obj.tax_id.amount,sub_header_style_r)
                else:
                    ws1.write(row,col+17, '',sub_header_style_r)
                # Tax
                if obj.alicuota_general:
                    ws1.write(row,col+18, obj.alicuota_general,sub_header_style_r)
                else:
                    ws1.write(row,col+18, '',sub_header_style_r)
                # VAT Withholding Voucher (Date)
                if obj.total_con_iva:
                    ws1.write(row,col+19, obj.fecha_comprobante,sub_header_style_c)
                else:
                    ws1.write(row,col+19, '',sub_header_style_c)
                # VAT Withholding Voucher (Number)
                if obj.total_con_iva:
                    ws1.write(row,col+20, obj.nro_comprobante,sub_header_style_c)
                else:
                    ws1.write(row,col+20, '',sub_header_style_c)

                total_purchases += obj.total_con_iva
                total_exempt_purchases += obj.total_exento
                total_general_tax_base_tax_amount += obj.base_general
                total_vat_general_tax += obj.alicuota_general

        general_total_base += total_exempt_purchases + total_general_tax_base_tax_amount
        general_total_credit += total_vat_general_tax
        general_total_withheld = 0.00

        row += 1
        ws1.write_merge(row,row, 0, 10, ("Total Purchases at: " + self.date_to.strftime('%d/%m%Y')), sub_header_style_c)
        ws1.write(row,col+11, total_purchases,sub_header_style_r)
        ws1.write(row,col+12, total_exempt_purchases,sub_header_style_r)
        ws1.write(row,col+13, '',sub_header_style_r)
        ws1.write(row,col+14, '',sub_header_style_r)
        ws1.write(row,col+15, '',sub_header_style_r)
        ws1.write(row,col+16, total_general_tax_base_tax_amount,sub_header_style_r)
        ws1.write(row,col+17, '',sub_header_style_r)
        ws1.write(row,col+18, total_vat_general_tax,sub_header_style_r)

        row += 2
        ws1.write_merge(row,row, 0, 1, (" "), center)
        ws1.write_merge(row,row, 2, 3, ("Tax Base"), sub_header_style_c)
        ws1.write_merge(row,row, 4, 5, ("Fiscal Credit"), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, ("VAT Withheld"), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Total: Exempt purchases and / or without the right to tax credit"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, total_exempt_purchases,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of: Import Purchases Affects only General Aliquot"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" ") ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of: Import Purchases Affected in General Tax Rate + Additional"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" ") ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of: Import Purchases Affected in Reduced Rate"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" ") ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of: Purchases Internal Affects only General Tax Rate"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, total_general_tax_base_tax_amount ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, total_vat_general_tax, sub_header_style_r)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of: Internal Purchases Affected in General Tax Rate + Additional"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" ") ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, ("Σ of the: Internal Purchases Affected in Reduced Rate"), sub_header_style_c)
        ws1.write_merge(row,row, 2, 3, (" ") ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, (" "), sub_header_style_c)
        ws1.write_merge(row,row, 6, 7, (" "), sub_header_style_c)
        row += 1
        ws1.write_merge(row,row, 0, 1, (" "), center)
        ws1.write_merge(row,row, 2, 3, general_total_base ,sub_header_style_r)
        ws1.write_merge(row,row, 4, 5, general_total_credit, sub_header_style_r)
        ws1.write_merge(row,row, 6, 7, general_total_withheld, sub_header_style_r)

        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        fecha  = datetime.now().strftime('%d/%m/%Y') 
        self.write({'state': 'get', 'report': out, 'name': _('Purchase Book ')+ fecha +'.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.book',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }