{
    'name': 'Account Refunds Approvals',
    'version': '13.0.1.0.0',
    'author': 'OasisConsultora',
    'maintainer': 'OasisConsultora',
    'website': 'oasisconsultora.com',
    'license': 'AGPL-3',
    'depends': ['approvals', 'account_accountant'],
    'data': [
        'views/approval_account_fields_extend.xml',
        'views/account_move_approvals.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
