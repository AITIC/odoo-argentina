# Copyright 2026 AITIC S.A.S <https://aitic.com.ar>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.zeep import Client, Transport


_logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 10
SERVICE_STATES = [
    ("unknown", "Not checked"),
    ("available", "Available"),
    ("unavailable", "Unavailable"),
]
WSAA_URLS = {
    "production": "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL",
    "testing": "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL",
}
WSFE_URLS = {
    "production": "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    "testing": "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
}


class ArcaHTTPAdapter(HTTPAdapter):
    """Avoid incompatible DH ciphers while preserving certificate verification."""

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = create_urllib3_context(ciphers="DEFAULT:!DH")
        return super().init_poolmanager(*args, **kwargs)


class L10nArAfipServiceStatus(models.Model):
    _name = "l10n_ar.afip.service.status"
    _description = "ARCA Service Availability"
    _rec_name = "environment"

    environment = fields.Selection(
        [("production", "Production"), ("testing", "Testing")], required=True,
    )
    wsfe_status = fields.Selection(SERVICE_STATES, default="unknown", required=True)
    wsaa_status = fields.Selection(SERVICE_STATES, default="unknown", required=True)
    wsfe_error = fields.Text()
    wsaa_error = fields.Text()
    check_date = fields.Datetime(string="Last Check")

    _sql_constraints = [
        ("environment_unique", "unique(environment)",
         "Only one ARCA status record is allowed per environment."),
    ]

    @api.model
    def _get_environment(self, company):
        # Enterprise supplies a per-company setting. Keep the base addon usable
        # in Community, where only the system-wide infrastructure monitor exists.
        if "l10n_ar_afip_ws_environment" in company._fields:
            environment = company.l10n_ar_afip_ws_environment
        else:
            environment = self.env["ir.config_parameter"].sudo().get_param(
                "l10n_ar_ux.arca_environment", default="production",
            )
        return environment if environment in WSFE_URLS else False

    @api.model
    def get_status_info(self):
        """Read cached public-service status for the user's current company."""
        self.check_access_rights("read")
        company = self.env.company
        environment = self._get_environment(company)
        status = self.search([("environment", "=", environment)], limit=1) if environment else self
        return {
            "enabled": company.country_id.code == "AR",
            "environment": environment or False,
            "last_check": fields.Datetime.to_string(status.check_date) if status else False,
            "wsfe": {
                "status": status.wsfe_status if status else "unknown",
                "error": status.wsfe_error if status else False,
            },
            "wsaa": {
                "status": status.wsaa_status if status else "unknown",
                "error": status.wsaa_error if status else False,
            },
        }

    @api.model
    def refresh_status(self):
        """Allow internal users to check fixed ARCA endpoints, without write ACLs."""
        self.check_access_rights("read")
        # Resolve the company before sudo, so allowed_company_ids are validated.
        environment = self._get_environment(self.env.company)
        if not environment:
            raise UserError(_("Configure a valid ARCA environment (production or testing)."))
        status = self.sudo().search([("environment", "=", environment)], limit=1)
        if not status:
            raise UserError(_("ARCA status is not initialized. Please update the Accounting UX module."))
        # Only this fixed status record is writable through this RPC method.
        status._check_services()
        return self.get_status_info()

    def _probe_service(self, service):
        """Check infrastructure only: never request tokens or send invoices."""
        self.ensure_one()
        transport = Transport(timeout=TIMEOUT_SECONDS, operation_timeout=TIMEOUT_SECONDS)
        transport.session.mount("https://", ArcaHTTPAdapter())
        try:
            if service == "wsfe":
                url = WSFE_URLS[self.environment]
            else:
                url = WSAA_URLS[self.environment]
            client = Client(url, transport=transport)
            if service == "wsfe":
                response = client.service.FEDummy()
                servers = {
                    name: str(getattr(response, name, "") or "").upper()
                    for name in ("AppServer", "DbServer", "AuthServer")
                }
                if any(value != "OK" for value in servers.values()):
                    return "unavailable", _(
                        "ARCA reported: application %(app)s, database %(db)s, authentication %(auth)s.",
                        app=servers["AppServer"] or _("No response"),
                        db=servers["DbServer"] or _("No response"),
                        auth=servers["AuthServer"] or _("No response"),
                    )
            # WSAA has no unauthenticated login check: loading its WSDL only
            # confirms reachability, not the validity of a company's certificate.
            return "available", False
        except Exception as error:
            _logger.warning("ARCA %s availability check failed (%s): %s", service, self.environment, error)
            return "unavailable", _("Could not contact ARCA (%s).", type(error).__name__)
        finally:
            transport.session.close()

    def _check_services(self):
        for status in self:
            values = {}
            for service in ("wsfe", "wsaa"):
                state, error = status._probe_service(service)
                values.update({f"{service}_status": state, f"{service}_error": error})
            values["check_date"] = fields.Datetime.now()
            status.write(values)

    @api.model
    def _cron_refresh_status(self):
        companies = self.env["res.company"].search([
            ("country_id.code", "=", "AR"),
        ])
        if "l10n_ar_afip_ws_environment" in companies._fields:
            environments = companies.mapped("l10n_ar_afip_ws_environment")
        else:
            environments = [self._get_environment(self.env.company)] if companies else []
        self.search([("environment", "in", environments)])._check_services()
