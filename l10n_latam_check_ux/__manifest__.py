{
    'name': 'Latam Check UX',
    'version': "15.0.1.0.0",
    'category': 'Localization/Argentina',
    'sequence': 15,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'l10n_latam_check',
        'l10n_ar_ux',
    ],
    'data': [
        'reports/report_account_transfer.xml',
        'views/account_payment_view.xml',
        'views/l10n_latam_checkbook_view.xml',
        'wizards/account_payment_add_checks_views.xml',
        'wizards/account_payment_register_views.xml',
        'views/account_payment_group_view.xml',
        'reports/report_payment_group.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
