# Contabilidad argentina UX

## Descripción General

Extiende la localización contable argentina de Odoo. Agrega un indicador de
disponibilidad de ARCA a la barra superior sin agregar dependencias Enterprise
al monitor.
La documentación previa del módulo se conserva en `README.rst`.

## Funcionalidades

- Indicador «Conexión ARCA» para compañías argentinas, con el ambiente de la
  compañía activa (producción u homologación).
- Consulta WSFE mediante `FEDummy` y disponibilidad del WSDL de WSAA. El control
  de WSAA no valida certificados, delegaciones ni credenciales de la compañía.
- «Verificar ahora» realiza consultas nuevas y actualiza el resultado visible.
- Consulta programada cada cinco minutos para los ambientes configurados.
- Última verificación en la zona horaria y formato del usuario. Antes de la
  primera consulta se informa que el servicio todavía no fue verificado.
- Fallas de red, respuestas incompletas y servicios no operativos se muestran
  como no disponibles, sin reutilizar estados exitosos como resultado nuevo.
- No se envían comprobantes ni se solicitan tokens desde el indicador.

## Instalación

- Para instalar este módulo seleccione `l10n_ar_ux` en Ajustes → Aplicaciones
  e instálelo como cualquier otro módulo de Odoo. En bases existentes, actualice
  el módulo y recargue el navegador para cargar los nuevos recursos.
- Depende de `l10n_ar`, `account_ux` y `l10n_latam_check`, proveedores del asistente
  heredado `account.change.currency` y de las vistas contables y de pagos que
  ya utiliza el módulo.
  El monitor no requiere `l10n_ar_edi`.
- Si está instalado `l10n_ar_edi`, utiliza el ambiente ARCA de la compañía en
  los ajustes contables. Sin ese módulo, utiliza el parámetro de sistema
  `l10n_ar_ux.arca_environment`: `production` por defecto o `testing` para
  homologación. La zona horaria se configura en las preferencias del usuario.
- Usuarios internos pueden consultar y refrescar el indicador; los registros
  almacenados de estado no admiten edición directa por esos usuarios.
- Este indicador es informativo y no reemplaza el control preventivo de emisión
  de `aitic_l10n_ar_afip_status`. No automatiza la actualización de contactos.

## Colaboradores

- Desarrollo original: ADHOC SA; ver `README.rst` y el historial del repositorio.
- Adaptación del indicador de disponibilidad: AITIC S.A.S.

---

## AITIC

Adaptación desarrollada por **AITIC** — [aitic.com.ar](https://www.aitic.com.ar).

[![AITIC](https://www.aitic.com.ar/web/image/website/1/logo/AITIC?unique=0d6d95a)](https://www.aitic.com.ar)
