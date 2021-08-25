from odoo import models,fields

class Condition(models.Model):
    _inherit='account.move'

    condition=fields.Selection(selection=[("counted", "Counted"), ("credit", "Credit")], string="Payment conditions")