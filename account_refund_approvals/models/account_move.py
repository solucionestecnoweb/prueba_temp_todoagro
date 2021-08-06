from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
import base64
from odoo.exceptions import UserError, ValidationError, except_orm, Warning
from odoo.tools.float_utils import float_round


class AccountMoveApproval(models.Model):
    _inherit = 'account.move'

    is_approved = fields.Boolean(default=False)
    approver_ids = fields.Many2many(comodel_name='res.users', string='Approvers')
    
    def action_post(self):
        for item in self:
            xfind = item.env['approval.request'].search([('account_refund_id', '=', item.id)], limit=1)
            is_company =  item.env['res.company'].search([('partner_id', '=', item.partner_id.id)])
            if item.type == 'out_refund':
                status = xfind.request_status
                if len(xfind) > 0:
                    if status == 'approved':
                        item.is_approved = True
                    else:
                        item.is_approved = False
                elif len(is_company) > 0:
                    item.is_approved = True
                elif self.payment_condition_id.name in ('contado', 'Contado', 'CONTADO'):
                    item.is_approved = True
                else:
                    item.is_approved = False
                if item.is_approved:
                    super(AccountMoveApproval, self).action_post()
                elif status == 'refused':
                    raise ValidationError(_("Cannot confirm, there is an approval request refused for this credit note."))
                else:
                    raise ValidationError(_("Cannot confirm until an approval request is approved for this credit note."))
            else:
                super(AccountMoveApproval, self).action_post()

    def approvals_request_refund(self):
        approvers = len(self.approver_ids)
        xfind = self.env['approval.request'].search([('account_refund_id', '=', self.id), ('request_status', 'not in', ['new', 'cancel']), ('approval_minimum', '=', approvers)])
        if len(xfind) == 0:
            approval = self.env['approval.category'].search([
                ('has_account_refund', '=', 'required'), 
                ('approval_minimum', '=', approvers),
            ], limit=1)
            if len(approval) > 0:
                values = {
                    'name': approval.name,
                    'category_id': approval.id,
                    'date': datetime.now(),
                    'request_owner_id': self.env.user.id,
                    'amount': self.amount_total,
                    'account_refund_id': self.id,
                    'request_status': 'pending'
                }
                t = self.env['approval.request'].create(values)
                for item in self.approver_ids:
                    t.approver_ids += self.env['approval.approver'].new({
                        'user_id': item.id,
                        'request_id': t.id,
                        'status': 'new'
                    })
                t.action_confirm()
            else:
                raise ValidationError(_("There is no approval category for this type record. Go to Approvals/Config/Approval type."))
        else:
            if xfind['request_status'] == 'approved':
                raise ValidationError(_("There is an approval request approved for this credit note."))
            elif xfind['request_status'] == 'refused':
                raise ValidationError(_("There is an approval request refused for this credit note."))
            else:
                raise ValidationError(_("There is an approval request ongoing for this credit note."))

