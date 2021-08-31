from odoo import models, fields,api

class Extension(models.Model):
    _inherit='product.template'

    profit_percentage=fields.Float(string="Product Profit Percentage")
    foreign_currency_cost=fields.Float(string="Cost in Dollars", compute='_compute_foreign_currency')
    
    def _compute_foreign_currency(self):
        for item in self:
            item.foreign_currency_cost = 0
            if item.habilita_precio_div:
                item.foreign_currency_cost = item.env['res.currency']._convert(item.standard_price, item.moneda_divisa_venta, item.env.company, fields.Date.today())

    @api.onchange('foreign_currency_cost','profit_percentage')
    def _onchange_list_price2(self):
        if self.habilita_precio_div:
            self.list_price2 = self.foreign_currency_cost + ((self.foreign_currency_cost * self.profit_percentage) / 100) 

            