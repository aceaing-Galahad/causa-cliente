#!/usr/bin/env python3
"""Genera informes de seguimiento judicial desde datos revisados por una persona."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse


class InputError(ValueError):
    pass


def required(obj, key, where):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InputError(f'{where}.{key}: se requiere texto no vacío')
    if len(value) > 12000:
        raise InputError(f'{where}.{key}: máximo 12000 caracteres')
    return value


def day(value, where):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise InputError(f'{where}: use AAAA-MM-DD')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f'{where}: fecha inválida') from exc


def records(data, key, minimum=0):
    value = data.get(key)
    if not isinstance(value, list) or len(value) < minimum or not all(isinstance(x, dict) for x in value):
        raise InputError(f'{key}: se requiere una lista de objetos (mínimo {minimum})')
    if len(value) > 500:
        raise InputError(f'{key}: máximo 500 registros')
    return value


def validate(data):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise InputError('schema_version debe ser 1')
    case = data.get('case')
    if not isinstance(case, dict):
        raise InputError('case: se requiere un objeto')
    for key in ('rol', 'court', 'caption', 'procedure', 'stage', 'status', 'summary', 'scope'):
        required(case, key, 'case')
    cutoff = day(case.get('cutoff_date'), 'case.cutoff_date')
    filed = day(case.get('filed_at'), 'case.filed_at')
    if filed > cutoff:
        raise InputError('La fecha de ingreso no puede ser posterior al corte')
    if case.get('review_status') not in ('draft', 'validated'):
        raise InputError('case.review_status: use draft o validated')
    if case['review_status'] == 'validated':
        required(case, 'reviewed_by', 'case')
        reviewed = day(case.get('reviewed_at'), 'case.reviewed_at')
        if reviewed < cutoff:
            raise InputError('La revisión no puede ser anterior al corte de información')
    sources = records(data, 'sources', 1)
    ids = set()
    for source in sources:
        sid = required(source, 'id', 'sources')
        if sid in ids:
            raise InputError(f'Fuente duplicada: {sid}')
        ids.add(sid)
        required(source, 'title', f'sources.{sid}')
        url = required(source, 'url', f'sources.{sid}')
        parsed = urlparse(url)
        if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or parsed.password:
            raise InputError(f'URL de fuente inválida: {sid}')
        if day(source.get('consulted_at'), f'sources.{sid}.consulted_at') > cutoff:
            raise InputError('Una fuente no puede haber sido consultada después del corte')
    for event in records(data, 'events', 1):
        for key in ('stage', 'title', 'description', 'folio', 'source_id'):
            required(event, key, 'events')
        when = day(event.get('date'), 'events.date')
        if not filed <= when <= cutoff:
            raise InputError('Los hitos deben estar entre el ingreso y el corte; use next_steps para el futuro')
        if event['source_id'] not in ids:
            raise InputError(f"Fuente de hito inexistente: {event['source_id']}")
    for step in records(data, 'next_steps', 1):
        for key in ('action', 'owner', 'when', 'reason'):
            required(step, key, 'next_steps')
    timing = data.get('timing')
    if not isinstance(timing, dict):
        raise InputError('timing: se requiere un objeto')
    for key in ('legal_reference', 'remaining_time', 'follow_up'):
        required(timing, key, 'timing')
    if timing.get('source_id') and timing['source_id'] not in ids:
        raise InputError('Fuente de referencia legal inexistente')
    if timing.get('waiting_since'):
        waiting = day(timing['waiting_since'], 'timing.waiting_since')
        if not filed <= waiting <= cutoff:
            raise InputError('waiting_since debe estar entre el ingreso y el corte')
    return data


def load(path):
    path = Path(path)
    if path.stat().st_size > 2_000_000:
        raise InputError('El archivo supera 2 MB')
    try:
        return validate(json.loads(path.read_text(encoding='utf-8-sig')))
    except json.JSONDecodeError as exc:
        raise InputError(f'JSON inválido: línea {exc.lineno}, columna {exc.colno}') from exc


def fmt(value):
    return day(value, 'fecha').strftime('%d/%m/%Y')


def waiting_text(data):
    timing, case = data['timing'], data['case']
    if not timing.get('waiting_since'):
        return 'Sin fecha de inicio de espera informada.'
    elapsed = (day(case['cutoff_date'], 'corte') - day(timing['waiting_since'], 'espera')).days
    return f"{elapsed} días corridos desde {fmt(timing['waiting_since'])}. Este dato no calcula un vencimiento procesal."


def review_text(case):
    if case['review_status'] == 'validated':
        return f"REVISADO por {case['reviewed_by']} el {fmt(case['reviewed_at'])} (declaración registrada en los datos; no es firma digital)."
    return 'BORRADOR - PENDIENTE DE REVISIÓN DEL ABOGADO'


def html_report(data):
    case, timing = data['case'], data['timing']
    def e(value):
        return escape(str(value), quote=True)
    events = ''.join(
        f'<li><div class="date">{fmt(x["date"])} · {e(x["stage"])}</div>'
        f'<h3>{e(x["title"])}</h3><p>{e(x["description"])}</p>'
        f'<small>Folio: {e(x["folio"])} · Fuente: {e(x["source_id"])}</small></li>'
        for x in sorted(data['events'], key=lambda x: x['date']))
    actions = ''.join(f'<li><h3>{e(x["action"])}</h3><p>{e(x["reason"])}</p>'
                      f'<small>Responsable: {e(x["owner"])} · Cuándo: {e(x["when"])}</small></li>'
                      for x in data['next_steps'])
    sources = ''.join(f'<li id="{e(x["id"])}">[{e(x["id"])}] <a href="{e(x["url"])}" rel="noreferrer">'
                      f'{e(x["title"])}</a> · Consulta: {fmt(x["consulted_at"])}</li>' for x in data['sources'])
    legal_source = f' [Fuente: {e(timing["source_id"])}]' if timing.get('source_id') else ''
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><title>Informe {e(case['rol'])}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf2f6;color:#23384d;font:16px/1.6 system-ui,Arial,sans-serif}}
main{{max-width:900px;margin:36px auto;background:white;padding:48px;border-top:8px solid #087d83}}
h1,h2,h3{{line-height:1.25;color:#172b43}}h1{{font-size:34px;margin:10px 0}}h2{{margin-top:36px;font-size:24px}}h3{{font-size:18px;margin:6px 0}}
p{{margin:8px 0}}.eyebrow,.date{{color:#087d83;font-weight:700}}.badge{{background:#fff1d6;color:#754b0e;padding:12px;font-size:13px}}
.summary{{background:#edf6f6;border-left:4px solid #087d83;padding:20px;margin:24px 0}}dl{{display:grid;grid-template-columns:150px 1fr;gap:8px 16px}}dt{{font-weight:700}}dd{{margin:0}}
ol.timeline{{list-style:none;padding-left:22px;border-left:3px solid #d6e0e8}}li{{margin-bottom:24px}}small,.scope{{color:#586c80;font-size:13px}}a{{color:#087d83;overflow-wrap:anywhere}}
footer{{border-top:1px solid #d6e0e8;padding-top:16px;margin-top:32px;font-size:13px}}@page{{size:A4;margin:18mm}}
@media print{{body{{background:white;font-size:11pt}}main{{padding:0;margin:0;max-width:none;border-top:4px solid #087d83}}h1{{font-size:25pt}}h2{{font-size:17pt}}li,.summary,dl{{break-inside:avoid}}h2,h3{{break-after:avoid}}a{{text-decoration:none}}}}
</style></head><body><main>
<div class="eyebrow">INFORME DE SEGUIMIENTO JUDICIAL</div><h1>{e(case['rol'])}</h1><p>{e(case['caption'])}</p>
<p class="badge">{e(review_text(case))}</p><dl><dt>Tribunal</dt><dd>{e(case['court'])}</dd><dt>Procedimiento</dt><dd>{e(case['procedure'])}</dd>
<dt>Ingreso</dt><dd>{fmt(case['filed_at'])}</dd><dt>Corte</dt><dd>{fmt(case['cutoff_date'])}</dd></dl>
<section class="summary"><strong>{e(case['stage'])} · {e(case['status'])}</strong><p>{e(case['summary'])}</p></section>
<h2>Línea de tiempo por etapas</h2><ol class="timeline">{events}</ol>
<h2>Qué sigue</h2><ol>{actions}</ol><h2>Tiempo y seguimiento</h2>
<h3>Tiempo observado</h3><p>{e(waiting_text(data))}</p><h3>Referencia legal</h3><p>{e(timing['legal_reference'])}{legal_source}</p>
<h3>Tiempo restante</h3><p>{e(timing['remaining_time'])}</p><h3>Próximo control</h3><p>{e(timing['follow_up'])}</p>
<h2>Fuentes y alcance</h2><ul>{sources}</ul><p class="scope">{e(case['scope'])}</p>
<footer>Datos ingresados por una persona. El generador no consulta la OJV, no verifica el mérito de la causa y no calcula plazos legales. Revise el informe antes de entregarlo.</footer>
</main></body></html>'''


def pdf_report(data, path):
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    except ImportError as exc:
        raise InputError('Para PDF instale: python -m pip install -r requirements.txt; o use --format html') from exc
    styles = getSampleStyleSheet()
    for key in ('BodyText','Normal'):
        styles[key].fontName='Helvetica'; styles[key].fontSize=10; styles[key].leading=14
        styles[key].textColor=colors.HexColor('#23384d')
    styles.add(ParagraphStyle('Meta',fontName='Helvetica',fontSize=8,leading=11,textColor=colors.HexColor('#586c80')))
    styles.add(ParagraphStyle('Review',fontName='Helvetica-Bold',fontSize=9,leading=13,textColor=colors.HexColor('#875b17'),spaceAfter=14))
    for key in ('Title','Heading2','Heading3'):
        styles[key].textColor=colors.HexColor('#172b43')
        styles[key].alignment=TA_LEFT
    story=[]
    def para(text, kind='BodyText'):
        return Paragraph(escape(str(text)),styles[kind])
    def add(text, kind='BodyText'):
        story.append(para(text,kind))
    case, timing = data['case'], data['timing']
    add('INFORME DE SEGUIMIENTO JUDICIAL','Meta')
    add(case['rol'],'Title'); add(case['caption'],'Heading3'); add(review_text(case),'Review')
    for title,key in [('Tribunal','court'),('Procedimiento','procedure')]:
        add(f'{title}: {case[key]}')
    add(f"Ingreso: {fmt(case['filed_at'])} | Corte: {fmt(case['cutoff_date'])}")
    add(f"{case['stage']} | {case['status']}",'Heading2'); add(case['summary'])
    add('Línea de tiempo por etapas','Heading2')
    for event in sorted(data['events'],key=lambda x:x['date']):
        story.append(KeepTogether([
            para(f"{fmt(event['date'])} | {event['stage']}",'Meta'),
            para(event['title'],'Heading3'),para(event['description']),
            para(f"Folio: {event['folio']} | Fuente: {event['source_id']}",'Meta'),Spacer(1,12)]))
    add('Qué sigue','Heading2')
    for n,step in enumerate(data['next_steps'],1):
        story.append(KeepTogether([para(f"{n}. {step['action']}",'Heading3'),para(step['reason']),
            para(f"Responsable: {step['owner']} | Cuándo: {step['when']}",'Meta'),Spacer(1,10)]))
    add('Tiempo y seguimiento','Heading2'); add('Tiempo observado','Heading3'); add(waiting_text(data))
    for title,key in [('Referencia legal','legal_reference'),('Tiempo restante','remaining_time'),('Próximo control','follow_up')]:
        add(title,'Heading3')
        suffix=f" [Fuente: {timing['source_id']}]" if key=='legal_reference' and timing.get('source_id') else ''
        add(timing[key]+suffix)
    add('Fuentes y alcance','Heading2')
    for source in data['sources']:
        story.append(KeepTogether([para(f"[{source['id']}] {source['title']} | Consulta: {fmt(source['consulted_at'])}",'Meta'),
            para(source['url'],'Meta'),Spacer(1,9)]))
    add(case['scope'],'Meta')
    story.append(Spacer(1,10))
    add('Datos ingresados por una persona. El generador no consulta la OJV ni calcula plazos legales. Revise el informe antes de entregarlo.','Meta')
    def footer(c,doc):
        c.saveState(); c.setStrokeColor(colors.HexColor('#087d83'))
        c.line(42,35,A4[0]-42,35); c.setFont('Helvetica',8)
        c.setFillColor(colors.HexColor('#586c80'))
        # Short fixed footer avoids clipping user-provided identifiers.
        c.drawString(42,23,f"Seguimiento judicial | Corte: {fmt(case['cutoff_date'])}")
        c.drawRightString(A4[0]-42,23,f'Página {doc.page}'); c.restoreState()
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=52,
                      title=f"Informe {case['rol']}",author='Causa Cliente').build(story,onFirstPage=footer,onLaterPages=footer)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Archivo JSON de la causa')
    parser.add_argument('--output',type=Path,default=Path('salida'),help='Carpeta de destino')
    parser.add_argument('--format',choices=('html','pdf','both'),default='both')
    parser.add_argument('--overwrite',action='store_true',help='Permitir reemplazar informes existentes')
    args=parser.parse_args(argv)
    try:
        data=load(args.input)
        slug=re.sub(r'[^A-Za-z0-9_-]+','_',data['case']['rol']).strip('_')[:80] or 'causa'
        stem=f"informe_{slug}_{data['case']['cutoff_date']}"
        extensions=['html','pdf'] if args.format=='both' else [args.format]
        targets={ext:args.output/f'{stem}.{ext}' for ext in extensions}
        if not args.overwrite and any(p.exists() for p in targets.values()):
            raise InputError('Ya existe un informe de ese rol y fecha. Use otra carpeta o --overwrite')
        args.output.mkdir(parents=True,exist_ok=True)
        if 'pdf' in targets:
            pdf_report(data,targets['pdf'])
        if 'html' in targets:
            targets['html'].write_text(html_report(data),encoding='utf-8')
        for target in targets.values():
            print(target.resolve())
        return 0
    except (InputError,OSError) as exc:
        print(f'Error: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
