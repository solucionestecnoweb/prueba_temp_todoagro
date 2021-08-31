from odoo import api, fields, models


class ApprovalsCategorySaleExtend(models.Model):
    _inherit = 'approval.category'

    has_account_refund = fields.Selection(string='Credit Note', selection=[('required', 'Required'), ('optional', 'Optional'), ('no', 'None')], default='no')

class ApprovalsRequestSaleExtend(models.Model):
    _inherit = 'approval.request'

    account_refund_id = fields.Many2one(comodel_name='account.move', string='Credit Note')
    has_account_refund = fields.Selection(related="category_id.has_account_refund")
