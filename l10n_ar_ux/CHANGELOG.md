## [17.0.1.9.0] - 2026-11-05

### Added

- Indicador «Conexión ARCA» en la barra superior, con disponibilidad de WSFE y
  WSAA por ambiente de la compañía activa y actualización programada cada cinco
  minutos, con validación TLS y sin generar tokens ni agregar dependencias
  Enterprise. Con `l10n_ar_edi` utiliza el ambiente contable de la compañía;
  sin ese módulo utiliza el parámetro `l10n_ar_ux.arca_environment`.

### Fixed

- Declara las dependencias de `account_ux` y `l10n_latam_check`, ya utilizadas por asistentes y vistas,
  y conserva la carga de la acción de cambio de cotización antes del formulario
  que la referencia, permitiendo la instalación desde cero.
- `ArcaStatusSystray.onRefreshClick` consulta y guarda un estado nuevo mediante
  `refresh_status`, en lugar de releer el resultado anterior. Informa fallas de
  consulta sin mostrar una confirmación exitosa.
- `ArcaStatusSystray.lastCheckLabel` convierte la fecha UTC al huso horario y
  formato del usuario, incluyendo cambios de día.
- Adaptación de la interfaz de v19 para Odoo 17.
  Ticket [#6680](https://www.aitic.com.ar/odoo/helpdesk.ticket/7182).
