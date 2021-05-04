##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    regimen_ganancias_id = fields.Many2one(
        related='payment_group_id.regimen_ganancias_id',
        string='Regimen Ganancias',
        readonly=True,
    )
    withholding_minimum = fields.Float(
        'Withholding Minimum',
        readonly=True,
    )