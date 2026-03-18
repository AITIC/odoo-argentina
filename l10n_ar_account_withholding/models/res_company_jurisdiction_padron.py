from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from io import BytesIO
import zipfile
import os
import re
import logging
import base64
_logger = logging.getLogger(__name__)


class ResCompanyJurisdictionPadron(models.Model):
    _name = "res.company.jurisdiction.padron"
    _description = "res.company.jurisdiction.padron"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    jurisdiction_id = fields.Many2one(
        "account.account.tag",
        domain="[('applicability', '=', 'taxes'),('jurisdiction_code', '!=', False)]",
        required=True,
    )

    file_padron = fields.Binary(
        "File",
        required=True,
    )
    l10n_ar_padron_from_date = fields.Date(
        "From Date",
        required=True,
    )
    l10n_ar_padron_to_date = fields.Date(
        "To Date",
        required=True,
    )

    @api.constrains('jurisdiction_id')
    def check_jurisdiction_id(self):
        arba_tag = self.env.ref('l10n_ar_ux.tag_tax_jurisdiccion_902')
        for rec in self:
            if rec.jurisdiction_id != arba_tag:
                raise ValidationError("El padron para (%s) no está implementado." % rec.jurisdiction_id.name)

    @api.depends('company_id', 'jurisdiction_id')
    def name_get(self):
        res = []
        for padron in self:
            name = "%s: %s" % (padron.company_id.name,
                               padron.jurisdiction_id.name)
            res += [(padron.id, name)]
        return res

    def descompress_file(self, file_padron):
        file = base64.b64decode(file_padron)
        with zipfile.ZipFile(BytesIO(file), 'r') as zip_file:
            names = zip_file.namelist()
            zip_file.extractall(path="/tmp")

    def find_aliquot(self, path, cuit):
        """We try to find aliqut and number for a partner given
        """
        with open(path, "r") as fp:
            aliq = False
            nro = False
            for line in fp.readlines():
                values = line.split(";")
                if values[4] == cuit:
                    aliq = values[8]
                    nro = values[3]
                    break
            return nro, aliq

    def find_file(self, rootdir, type_code):
        date = "%02d%d" % (self.l10n_ar_padron_from_date.month, self.l10n_ar_padron_from_date.year)
        pattern = type_code + r".*" + date
        for subdir, dirs, files in os.walk(rootdir):
            for f in files:
                if re.search(pattern, f, re.IGNORECASE):
                    return f
        return False

    def _get_aliquit(self, partner):
        padron_types = ["Per", "Ret"]
        nro = False
        aliquot_ret = 0.0
        aliquot_per = 0.0
        for padron_type in padron_types:
            path_file = self.find_file("/tmp/", padron_type)
            if not path_file:
                self.descompress_file(self.file_padron)
                path_file = self.find_file("/tmp/", padron_type)
            nro, aliquot = self.find_aliquot("/tmp/" + path_file, partner.vat)
            if padron_type == "Per":
                aliquot_per = aliquot and aliquot.replace(",", ".")
            else:
                aliquot_ret = aliquot and aliquot.replace(",", ".")
        return nro, aliquot_ret, aliquot_per

    def _build_aliquot_dict(self, path, cuit_filter=None):
        """Read a padron file and return a dict {cuit: (nro, aliquot)}.
        If cuit_filter is provided (a set), only entries matching those CUITs are kept.
        """
        result = {}
        try:
            with open(path, "r") as fp:
                for line in fp:
                    values = line.split(";")
                    if len(values) > 8:
                        cuit = values[4].strip()
                        if not cuit:
                            continue
                        if cuit_filter is not None and cuit not in cuit_filter:
                            continue
                        nro = values[3].strip()
                        aliq = values[8].strip().replace(",", ".")
                        result[cuit] = (nro, aliq)
        except Exception as e:
            _logger.warning("Error reading padron file %s: %s", path, e)
        return result

    def action_load_padron(self):
        self.ensure_one()
        self.descompress_file(self.file_padron)

        per_file = self.find_file("/tmp/", "Per")
        ret_file = self.find_file("/tmp/", "Ret")

        if not per_file and not ret_file:
            raise ValidationError(_("No se encontraron archivos de alícuotas en el padrón."))

        AlicuotModel = self.env['res.partner.arba_alicuot']
        cuit_type = self.env.ref('l10n_ar.it_cuit')

        partners = self.env['res.partner'].search([
            ('l10n_latam_identification_type_id', '=', cuit_type.id),
            ('vat', '!=', False),
        ])
        _logger.info("action_load_padron: %d partners found", len(partners))
        cuit_filter = set(partners.mapped('vat'))

        per_dict = self._build_aliquot_dict("/tmp/" + per_file, cuit_filter) if per_file else {}
        ret_dict = self._build_aliquot_dict("/tmp/" + ret_file, cuit_filter) if ret_file else {}

        count = 0

        for partner in partners:
            cuit = partner.vat
            per_data = per_dict.get(cuit)
            ret_data = ret_dict.get(cuit)

            if not per_data and not ret_data:
                continue

            nro = (per_data or ret_data)[0]
            try:
                aliquot_per = float(per_data[1]) if per_data and per_data[1] else 0.0
            except ValueError:
                aliquot_per = 0.0
            try:
                aliquot_ret = float(ret_data[1]) if ret_data and ret_data[1] else 0.0
            except ValueError:
                aliquot_ret = 0.0

            existing = AlicuotModel.search([
                ('partner_id', '=', partner.id),
                ('tag_id', '=', self.jurisdiction_id.id),
                ('company_id', '=', self.company_id.id),
                ('from_date', '=', self.l10n_ar_padron_from_date),
                ('to_date', '=', self.l10n_ar_padron_to_date),
            ], limit=1)

            vals = {
                'alicuota_percepcion': aliquot_per,
                'alicuota_retencion': aliquot_ret,
                'numero_comprobante': nro,
            }
            if existing:
                existing.write(vals)
            else:
                vals.update({
                    'partner_id': partner.id,
                    'tag_id': self.jurisdiction_id.id,
                    'company_id': self.company_id.id,
                    'from_date': self.l10n_ar_padron_from_date,
                    'to_date': self.l10n_ar_padron_to_date,
                })
                AlicuotModel.create(vals)
            count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Padrón cargado'),
                'message': _('%d alícuotas actualizadas.') % count,
                'type': 'success',
            },
        }
        