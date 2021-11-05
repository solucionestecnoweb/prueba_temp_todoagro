# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"
    
    os_currency_rate = fields.Float(string='Tipo de Cambio', default=1 ,digits=(12, 4))
    custom_rate = fields.Boolean(string='¿Usar Tasa de Cambio Personalizada?')
    move_aux_id=fields.Integer(compute='_compute_move_id')

    def _compute_move_id(self):
        self.move_aux_id=self.id

    def action_post(self):
        res = super().action_post()
        self.actualizar_balance()
        return res 
        
    def set_os_currency_rate(self):
        for selff in self:
            if selff.invoice_date:
                if not selff.custom_rate: 
                    rate = selff.env['res.currency.rate'].search([('currency_id', '=', selff.currency_id.id),('name','=',selff.invoice_date)], limit=1).sorted(lambda x: x.name)

                    if selff.currency_id.id != selff.company_currency_id.id:
                        if rate:
                            pass
                        else :
                            raise UserError(_("No existe tasa de cambio para  " + str(selff.invoice_date) + " registre el la siguiente ruta Contabilidad/Configuracion/Contabilidad/Monedas" ))

                    if rate :
                        exchange_rate =  1 / rate.rate
                        selff.os_currency_rate = exchange_rate
    
    @api.constrains('invoice_date','currency_id','')
    def _check_os_currency_rate(self):
        self.set_os_currency_rate()
    
    @api.onchange('invoice_date','currency_id')
    def _onchange_os_currency_rate(self):
        self.set_os_currency_rate()
    
    @api.onchange('os_currency_rate','amount_total')
    def _onchange_custom_rate(self):
        self.actualizar_balance()

    @api.constrains('os_currency_rate','amount_total')
    def _constrains_custom_rate(self):
        self.actualizar_balance()

    def actualizar_balance(self):
        for move in self:
            for item in move.line_ids:
                tasa = move.os_currency_rate
                if item.amount_currency > 0:
                    if move.currency_id.id == move.company_id.currency_id.id:
                        item.debit = item.amount_currency
                        item.debit_aux = item.amount_currency / tasa
                        ##item.amount_currency=item.amount_currency/tasa
                    else:

                        item.debit = item.amount_currency * tasa
                        item.debit_aux = item.amount_currency
                elif item.amount_currency < 0:
                    if move.currency_id.id == move.company_id.currency_id.id:
                        item.credit = (item.amount_currency) * (-1)
                        item.credit_aux = (item.amount_currency / tasa) * (-1)
                        ##item.amount_currency=(item.amount_currency/tasa)*(-1)
                    else:
                        item.credit = (item.amount_currency * tasa) * (-1)
                        item.credit_aux = (item.amount_currency) * (-1)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.constrains('move_id','state')
    def _os_constrains_move_id_rate(self):
        if len(self.move_line_ids) > 0:
            self.move_line_ids[0].move_id.os_currency_rate = self.rate

    """@api.constrains('payment_id')
    def _os_constrains_payment_id(self):
        for item in self.line_ids:
            if item.payment_id:
                if item.payment_id.rate > 0:
                    self.os_currency_rate = item.payment_id.rate

    def actualizar_balance(self):
        for move in self:
            for item in move.line_ids:
                tasa = move.os_currency_rate
                if item.amount_currency > 0:
                    if self.currency_id.id == self.company_id.currency_id.id:
                        item.debit = item.amount_currency
                        item.debit_aux = item.amount_currency / tasa
                        ##item.amount_currency=item.amount_currency/tasa
                    else:
                        if item.payment_id:
                            if item.payment_id.rate > 0:
                                tasa=item.payment_id.rate
                        item.debit = item.amount_currency * tasa
                        item.debit_aux = item.amount_currency
                elif item.amount_currency < 0:
                    if self.currency_id.id == self.company_id.currency_id.id:
                        item.credit = (item.amount_currency) * (-1)
                        item.credit_aux = (item.amount_currency / tasa) * (-1)
                        ##item.amount_currency=(item.amount_currency/tasa)*(-1)
                    else:
                        if item.payment_id:
                            if item.payment_id.rate>0:
                                tasa=item.payment_id.rate
                        item.credit = (item.amount_currency * tasa) * (-1)
                        item.credit_aux = (item.amount_currency) * (-1)"""
