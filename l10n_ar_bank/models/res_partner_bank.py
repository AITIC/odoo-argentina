# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    account_number = fields.Char(
        string='Número de Cuenta',
        help=_('El número de cuenta de la cuenta bancaria.'),
        required=True)
    
    alias = fields.Char(
        string='Alias',
        help=_('Un alias para la cuenta bancaria, utilizado para una identificación más sencilla.'))
    
    @api.depends('allow_out_payment', 'acc_number', 'bank_id', 'account_number')
    @api.depends_context('display_account_trust')
    def _compute_display_name(self):
        super()._compute_display_name()
        for acc in self:
            acc.display_name = f'{acc.account_number} - {acc.bank_id.name}' if acc.bank_id else acc.account_number
        if self.env.context.get('display_account_trust'):
            for acc in self:
                trusted_label = _('trusted') if acc.allow_out_payment else _('untrusted')
                if acc.bank_id:
                    name = f'{acc.account_number} - {acc.bank_id.name} ({trusted_label})'
                else:
                    name = f'{acc.account_number} ({trusted_label})'
                acc.display_name = name

    @api.constrains('acc_number')
    def _check_cbu_len(self):
        for rec in self:
            if rec.acc_number and len(rec.acc_number) != 22:
                raise UserError(_('El CBU debe tener exactamente 22 caracteres.'))