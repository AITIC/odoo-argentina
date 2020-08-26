# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools.translate import _
from odoo.tools.misc import formatLang, format_date


class ReportWithholdingPerception(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'report.withholding.perception'
    _description = 'Withholding and Perceptions Report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_unfold_all = False
    filter_partner = False
    filter_aliquot_type = [{'id': 'withholding', 'name': _('Withholding'), 'selected': False},
                           {'id': 'perception', 'name': _('Perception'), 'selected': False}]

    def _build_options(self, previous_options=None):
        self.filter_aliquot_type = [{'id': 'withholding', 'name': _('Withholding'), 'selected': False},
                           {'id': 'perception', 'name': _('Perception'), 'selected': False}]
        return super(ReportWithholdingPerception, self)._build_options(previous_options=previous_options)

    def _get_withh_percep_by_type(self, date_from, date_to, type_tax_use, account_ids=False):
        withh_percep_vals = []
        self.env.user.company_id
        domain = [('date', '>=', date_from), ('date', '<=', date_to), ('company_id', '=', self.env.user.company_id.id),
                  ('tax_repartition_line_id.tag_ids', '!=', False),
                  ('tax_line_id.type_tax_use', 'in', type_tax_use)]
        if account_ids:
            domain.append(('account_id', 'in', account_ids))
        move_line_ids = self.env['account.move.line'].search(domain, order='date asc')
        for line in move_line_ids:
            vals = {
                'id': line.id,
                'concept': line.tax_line_id.name,
                'date': line.date,
                'account': line.account_id.display_name if line.account_id else '',
                'voucher': line.move_id.name,
                'retention': line.name if line.tax_line_id.type_tax_use in ['customer', 'supplier'] else '',
                'organization': line.partner_id.name if line.partner_id.name else '',
                'cuit': line.partner_id.vat,
                # 'state': state,
                'amount': line.balance,
                # 'type': 'withholding',
            }
            withh_percep_vals.append(vals)
        sorted(withh_percep_vals, key=lambda k: k['date'])
        return withh_percep_vals

    def _get_columns_name(self, options):
        columns = [
            {'name': ''},
            {'name': _('Account')},
            {'name': _('Date')},
            {'name': _('Voucher')},
            {'name': _('Retention Voucher')},
            {'name': _('Organization')},
            {'name': _('CUIT')},
            # {'name': _('State')},
            {'name': _('Amount'), 'class': 'number'}]
        return columns

    def _get_data_columns(self, withh_percep_vals, data=True):
        amount = sum([x['amount'] for x in withh_percep_vals])
        if not data:
            columns = [
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                {'name': ''},
                # {'name': ''},
                {'name': round(amount, 2), 'class': 'number'}]
        else:
            columns = [
                {'name': withh_percep_vals[0]['account']},
                {'name': withh_percep_vals[0]['date']},
                {'name': withh_percep_vals[0]['voucher']},
                {'name': withh_percep_vals[0]['retention']},
                {'name': withh_percep_vals[0]['organization']},
                {'name': withh_percep_vals[0]['cuit']},
                # {'name': withh_percep_vals[0]['state']},
                {'name': round(amount, 2), 'class': 'number'}]
        return columns

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []

        lang_code = self.env.user.lang or 'es_AR'
        date_from = options.get('date') and options.get('date').get('date_from')
        date_to = options.get('date') and options.get('date').get('date_to')
        withholding = options.get('aliquot_type') and options.get('aliquot_type')[0].get('selected')
        perception = options.get('aliquot_type') and options.get('aliquot_type')[1].get('selected')
        account_ids = self._context.get('account_ids', False)
        if not (date_from and date_to):
            return []

        supplier_withh_ids = self._get_withh_percep_by_type(date_from, date_to, ['supplier'], account_ids)
        supplier_percep_ids = self._get_withh_percep_by_type(date_from, date_to, ['purchase'], account_ids)
        customer_withh_ids = self._get_withh_percep_by_type(date_from, date_to, ['customer'], account_ids)
        customer_percep_ids = self._get_withh_percep_by_type(date_from, date_to, ['sale'], account_ids)
        if withholding and not perception:
            columns_all = supplier_withh_ids + customer_withh_ids
            columns_effected = supplier_withh_ids
            columns_suffering = customer_withh_ids
            type_effected = [
                {'id': 'te1', 'name': _('Withholding'), 'withh_percep_ids': supplier_withh_ids},
            ]
            type_suffering = [
                {'id': 'ts1', 'name': _('Withholding'), 'withh_percep_ids': customer_withh_ids},
            ]
        elif perception and not withholding:
            columns_all = supplier_percep_ids + customer_percep_ids
            columns_effected = supplier_percep_ids
            columns_suffering = customer_percep_ids
            type_effected = [
                {'id': 'te2', 'name': _('Perception'), 'withh_percep_ids': supplier_percep_ids},
            ]
            type_suffering = [
                {'id': 'ts2', 'name': _('Perception'), 'withh_percep_ids': customer_percep_ids},
            ]
        else:
            columns_all = supplier_withh_ids + customer_withh_ids + supplier_percep_ids + customer_percep_ids
            columns_effected = supplier_withh_ids + supplier_percep_ids
            columns_suffering = customer_withh_ids + customer_percep_ids
            type_effected = [
                {'id': 'te1', 'name': _('Withholding'), 'withh_percep_ids': supplier_withh_ids},
                {'id': 'te2', 'name': _('Perception'), 'withh_percep_ids': supplier_percep_ids},
            ]
            type_suffering = [
                {'id': 'ts1', 'name': _('Withholding'), 'withh_percep_ids': customer_withh_ids},
                {'id': 'ts2', 'name': _('Perception'), 'withh_percep_ids': customer_percep_ids},
            ]
        categories = [
            {'id': 'cs1', 'name': _('Effected'), 'type_aliquot': type_effected},
            {'id': 'cs2', 'name': _('Suffering'), 'type_aliquot': type_suffering},
        ]
        debit_credit = [
            {'id': 1, 'name':  _('Withholdings and Perceptions'), 'categories': categories},
        ]

        for dc in debit_credit:
            if not line_id or 'dc_%s' % dc['id'] == line_id:
                lines.append({
                    'id': 'dc_%s' % dc['id'],
                    'name': dc['name'],
                    'columns': self._get_data_columns(columns_all, data=False),
                    'unfoldable': True,
                    'unfolded': 'dc_%s' % dc['id'] in options.get('unfolded_lines', []),
                    'level': 2,
                })
            if 'dc_%s' % dc['id'] in options.get('unfolded_lines', []) or options.get('unfold_all'):
                for cat in dc['categories']:
                    if not line_id or line_id in ('cat_%s' % cat['id'], 'dc_%s' % dc['id']):
                        type_aliquot = cat['type_aliquot']
                        if cat['id'] == 'cs1':
                            colums = columns_effected
                        if cat['id'] == 'cs2':
                            colums = columns_suffering
                        lines.append({
                            'id': 'cat_%s' % cat['id'],
                            'name': cat['name'],
                            'columns': self._get_data_columns(colums, data=False),
                            'unfoldable': True,
                            'unfolded': 'cat_%s' % cat['id'] in options.get('unfolded_lines', []) or options.get('unfold_all'),
                            'parent_id': 'dc_%s' % dc['id'],
                            'level': 3,
                        })

                    if 'cat_%s' % cat['id'] in options.get('unfolded_lines', []) or options.get('unfold_all'):
                        for tp in cat['type_aliquot']:
                            if not line_id or line_id in ('tp_%s' % tp['id'], 'cat_%s' % cat['id']):
                                withh_percep_ids = tp['withh_percep_ids']
                                lines.append({
                                    'id': 'tp_%s' % tp['id'],
                                    'name': tp['name'],
                                    'columns': self._get_data_columns(withh_percep_ids, data=False),
                                    'unfoldable': True,
                                    'unfolded': 'tp_%s' % tp['id'] in options.get('unfolded_lines',
                                                                                    []) or options.get('unfold_all'),
                                    'parent_id': 'cat_%s' % cat['id'],
                                    'level': 4,
                                })
                            if 'tp_%s' % tp['id'] in options.get('unfolded_lines', []) or options.get('unfold_all'):
                                for withh_percep in tp['withh_percep_ids']:
                                    if line_id and line_id != 'tp_%s' % tp['id']:
                                        continue
                                    lines.append({
                                        'id': 'resp_%s' % withh_percep['id'],
                                        'name': withh_percep['concept'],
                                        'columns': self._get_data_columns([withh_percep]),
                                        'parent_id': 'tp_%s' % tp['id'],
                                        'level': 5,
                                        # 'style': 'color: blue'
                                    })
        return lines

    @api.model
    def _get_report_name(self):
        return _('Withholdings and Perception Report')
