# Del expediente al informe del cliente

## 1. Identificar

Reúne rol/RIT, año, tribunal y competencia. El número por sí solo puede repetirse en distintos tribunales. Confirma carátula y fecha de ingreso antes de usar el resultado.

## 2. Consultar y conservar evidencia

Consulta la [Oficina Judicial Virtual](https://oficinajudicialvirtual.pjud.cl/). Registra la fecha de consulta, el cuaderno y el folio de cada hito. Descarga o conserva los antecedentes en el archivo privado del estudio, según sus políticas. No subas documentos reales al repositorio público.

Si hay acceso restringido, reserva o autenticación, utiliza los canales autorizados. Una ausencia de resultados no prueba la inexistencia de la causa.

## 3. Revisar por etapas

Usa las etapas que correspondan a la materia. Para un ejemplo civil pueden aparecer inicio, notificaciones, discusión, conciliación, prueba, sentencia, recursos y cumplimiento. No fuerces todas las causas al mismo recorrido.

Lee las resoluciones completas, no solo las etiquetas de la plataforma. Revisa todos los cuadernos relevantes, las notificaciones y los escritos pendientes. Si algo no se revisó, indícalo en `case.scope`.

## 4. Separar observaciones y propuestas

En `events`, registra solo hechos observados y su fuente. En `next_steps`, registra acciones propuestas con responsable y momento de revisión. No describas como realizada una gestión que todavía se está evaluando.

En `case.summary`, explica la situación en lenguaje simple. No atribuyas un resultado favorable/desfavorable sin leer el fallo correspondiente.

## 5. Explicar el tiempo

Separa tres conceptos:

- **Tiempo observado:** días corridos desde un hito hasta el corte. Lo calcula el generador si hay `waiting_since`.
- **Referencia legal:** norma y plazo que el abogado verificó para esa materia y actuación. Se ingresa como texto; el programa no lo calcula.
- **Tiempo restante:** estimación fundamentada o declaración expresa de que no hay información suficiente. No inventes rangos para completar el informe.

Las fechas de control del estudio son pautas internas. No son promesas de respuesta del tribunal.

Como referencia educativa, los arts. 64, 687 y 688 del [Código de Procedimiento Civil](https://www.bcn.cl/leychile/navegar?idNorma=22740) distinguen el tratamiento de plazos del tribunal y la citación/fallo en el procedimiento sumario. Antes de aplicarlos, verifica el texto vigente, la acción ejercida y las resoluciones del expediente. El ejemplo no sirve como calendario automático de vencimientos.

## 6. Validar y entregar

- [ ] Identificación y carátula correctas.
- [ ] Corte de información y fuentes registrados.
- [ ] Hitos respaldados con cuaderno y folio; sin hechos futuros mezclados.
- [ ] Documentos y cuadernos revisados descritos en el alcance.
- [ ] Etapa actual contrastada con las resoluciones.
- [ ] Propuestas diferenciadas de gestiones realizadas.
- [ ] Plazos y expectativas revisados por el abogado.
- [ ] Datos personales y destinatario del informe comprobados.
- [ ] PDF/HTML abierto y revisado visualmente.
- [ ] Revisión declarada y siguiente control agendado por el equipo.

El indicador `validated` registra una declaración del operador. No sustituye una firma electrónica ni una revisión independiente. Entrega el informe por el canal acordado con el cliente y conserva una versión por fecha de corte.

## 7. Actualizar

Ante una novedad, guarda una nueva versión del JSON, actualiza el corte, incorpora los hitos y repite la revisión. Conserva el informe anterior. El nombre de salida incluye rol y fecha para facilitar el archivo.
