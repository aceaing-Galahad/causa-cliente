# Causa Cliente

Convierte una revisión de expediente judicial en un informe para el cliente: línea de tiempo por etapas, situación actual, siguientes gestiones, tiempo observado y fuentes.

Proyecto abierto y reutilizable para estudios jurídicos de Chile. Trabaja localmente con un archivo JSON y genera **PDF y HTML**. El HTML también se puede imprimir como PDF desde el navegador.

## Ver el resultado

- [Informe de ejemplo en PDF](docs/demo/informe_DEMO-001-2026_2026-05-15.pdf).
- [Informe de ejemplo en HTML](docs/demo/informe_DEMO-001-2026_2026-05-15.html) (descargar y abrir en el navegador).
- [Datos ficticios del ejemplo](examples/causa_demo.json).
- [Proceso de trabajo](docs/PROCESO.md).

El repositorio solo incluye información ficticia. No incluye expedientes ni datos de clientes reales.

## Inicio rápido

Necesitas Python 3.10 o superior. En GitHub, selecciona **Code > Download ZIP**, descomprime la carpeta y abre una terminal en ella.

```bash
python -m pip install -r requirements.txt
python informe.py examples/causa_demo.json
```

En Windows, si el comando `python` no está disponible, prueba `py -3` en su lugar. En macOS/Linux puede ser `python3`.

Los informes se guardan en `salida/`. Abre el PDF o el HTML generado. Para generar solamente HTML, sin instalar librerías:

```bash
python informe.py examples/causa_demo.json --format html
```

## Usarlo con una causa real

1. Crea una carpeta local `casos/` y copia allí el JSON de ejemplo con otro nombre.
2. Sustituye todos los datos ficticios y revisa las fuentes. Las fechas usan `AAAA-MM-DD`.
3. Registra cada hito con etapa, descripción, folio y `source_id` asociado a una fuente.
4. Completa las gestiones propuestas y las expectativas de tiempo con el abogado responsable.
5. Mantén `review_status: "draft"` mientras falte revisión. El informe se marca como borrador.
6. Después de la revisión profesional, cambia a `"validated"` y completa `reviewed_by` y `reviewed_at`. Es una declaración manual, no una firma ni verificación de identidad.
7. Genera el informe y revisa su contenido y diseño antes de entregarlo al cliente.

```bash
python informe.py casos/mi_causa.json --output salida/cliente
```

El programa no sobrescribe un informe existente salvo que agregues `--overwrite`.

## Datos de entrada

| Campo | Uso |
|---|---|
| `schema_version` | Versión del formato; actualmente `1`. |
| `case` | Rol, tribunal, carátula, procedimiento, etapa, estado, fechas, resumen, alcance y revisión. |
| `events` | Hitos efectivamente observados, con fecha, etapa, título, descripción, folio y fuente. Se ordenan por fecha. |
| `next_steps` | Gestiones propuestas: acción, responsable, cuándo y fundamento. No se presentan automáticamente. |
| `timing` | Inicio opcional de la espera, referencia legal, tiempo restante y pauta de seguimiento. |
| `sources` | Identificador, título, URL y fecha de consulta de cada fuente. |

La estructura completa está en el ejemplo. No se acepta una fecha futura de hito respecto del corte: registra las acciones pendientes en `next_steps`. El número de días que se muestra es una diferencia de fechas en **días corridos**, no un cálculo de plazos judiciales.

## Límites del producto

- No consulta ni descarga expedientes de la OJV. La obtención y verificación de antecedentes es manual.
- No elude autenticación, reservas ni CAPTCHA.
- No concluye quién ganó por la etiqueta de etapa. Citar para oír sentencia no equivale a dictar sentencia.
- No calcula vencimientos legales ni predice fechas de fallo. Una referencia normativa requiere confirmar la materia, las resoluciones y las reglas de cómputo.
- No presenta escritos, envía correos ni modifica expedientes.
- El PDF usa Helvetica para textos en español/alfabeto latino. Para escrituras con otras familias de caracteres, usa el HTML o adapta las fuentes del PDF.

## Privacidad

El generador no envía datos a servidores. Los enlaces de fuentes solo se abren si el lector los visita. El HTML no carga recursos remotos.

`casos/` y `salida/` están excluidos por `.gitignore`; esto es una ayuda, no un control de acceso. Revisa los archivos antes de cualquier commit. Conserva los expedientes reales fuera del repositorio público. Si necesitas ejemplos públicos, anonimízalos y verifica las autorizaciones aplicables.

## Verificación

```bash
python -m unittest discover -s tests -v
python informe.py examples/causa_demo.json --output salida/verificacion
```

Las pruebas cubren validación de fechas y fuentes, protección contra HTML inyectado, marca de borrador, revisión declarada y generación de archivos. Para liberar cambios, abre también el PDF y el HTML y revisa visualmente el resultado.

## Publicar tu copia en GitHub

Crea un repositorio vacío llamado `causa-cliente` en tu cuenta y carga **el contenido de esta carpeta**, no el espacio de trabajo completo. Puedes usar la interfaz web **Add file > Upload files** o Git:

```bash
git init
git add .
git commit -m "Publicar generador de informes judiciales"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/causa-cliente.git
git push -u origin main
```

Reemplaza `TU_USUARIO` por tu usuario de GitHub, que puede ser distinto de tu correo. Revisa que el commit solo contenga la plantilla, los ejemplos ficticios y la documentación.

## Contribuir

Describe el problema, utiliza datos ficticios y agrega una prueba si afecta la validación o el informe. No adjuntes expedientes reales a issues o pull requests. Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

Licencia [MIT](LICENSE).
