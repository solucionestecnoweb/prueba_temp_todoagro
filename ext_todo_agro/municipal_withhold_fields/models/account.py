from odoo import api, fields, models


class AccountMoveLineOnchange(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _onchange_municipal_wh(self):
        if self.product_id.municipal_wh_id:
            self.concept_id = self.product_id.municipal_wh_id.id
        elif self.product_id.categ_id.municipal_wh_id:
            self.concept_id = self.product_id.categ_id.municipal_wh_id.id
