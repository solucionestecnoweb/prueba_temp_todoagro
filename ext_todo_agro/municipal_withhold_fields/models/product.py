from odoo import api, fields, models


class MunicipalWithholdTemplate(models.Model):
    _inherit = 'product.template'

    municipal_wh_id = fields.Many2one(comodel_name='muni.wh.concept', string='Municipal Withhold Concept')

class MunicipalWithholdCategory(models.Model):
    _inherit = 'product.category'

    municipal_wh_id = fields.Many2one(comodel_name='muni.wh.concept', string='Municipal Withhold Concept')
