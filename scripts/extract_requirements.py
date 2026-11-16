"""Derive a reviewable SRS transcript and traceability inventory, preserving source PDFs."""
import re
from pathlib import Path
from pypdf import PdfReader

root = Path(__file__).resolve().parent.parent
reader = PdfReader(next((root/'docs/requisitos').glob('*.pdf')))
pages = [p.extract_text() for p in reader.pages]
target = root/'docs/arquitectura'
(target/'SRS_EXTRAIDO.txt').write_text('\n\n'.join(f'=== FOLIO {i+1} ===\n{text}' for i,text in enumerate(pages)), encoding='utf-8')
requirements = []
for i in list(range(5,11))+list(range(11,13)):
    text = pages[i]
    markers = list(re.finditer(r'\b(RNF|RF)-\s*(\d{2})\s+', text))
    for index, match in enumerate(markers):
        chunk = text[match.end():markers[index+1].start() if index+1<len(markers) else len(text)]
        chunk = re.split(r'\b(?:Alta|Media|Baja)\b', chunk)[0]
        requirements.append((f'{match[1]}-{match[2]}', ' '.join(chunk.split()), i+1))
assert len(requirements)==84, len(requirements)
rows = ['# Trazabilidad del SRS', '', 'Fuente: PDF original, versión 1.0 (2025), 24 folios. Transcripción íntegra en SRS_EXTRAIDO.txt. Estado conservador: las pruebas unitarias no equivalen a validación institucional ni a pruebas de carga.', '', '| ID | Descripción original extraída | Folio | Módulo y archivos | Pruebas asociadas | Estado |', '|---|---|---|---|---|---|']
accounts={2,3,4,6,37,38,39,40}
catalogs={26,27,28,48,49,50,51,57}
partial={1,3,19,20,21,22,23,24,28,29,31,32,33,36,37,38,39,41,42,44,49,50,60}
implemented={2,4,6,26,27,37,38,40,48,51,57,61}
for rid,description,page in requirements:
    n=int(rid.split('-')[1]); rf=rid.startswith('RF-')
    module='Futuros bloques; docs/arquitectura/TODO.md'; tests='Pendiente'; state='pendiente'
    if rf:
        if n in accounts: module='accounts; backend/apps/accounts/; frontend/src/pages/Resource.jsx'; tests='SecurityTests (según comportamiento); main.test.jsx'
        elif n in catalogs: module='catalogs/settings_app; backend/apps/catalogs/; frontend/src/pages/Settings.jsx'; tests='SecurityTests.test_catalog_crud_and_integrity / test_settings_persist_and_validate; main.test.jsx'
        elif 19<=n<=32: module='Modelos content/approvals; backend/apps/content/models.py'; tests='test_visibility_is_independent_of_editorial_state (solo base)'
        elif 33<=n<=36: module='Modelo notifications; backend/apps/notifications/models.py'
        elif 42<=n<=47: module='analytics/audit; backend/apps/analytics/models.py; settings_app/views.py'; tests='test_dashboard_real_counts_and_pagination (solo contadores CMS)'
        elif n==61: module='config/urls.py; drf-spectacular'; tests='test_swagger_and_schema'
        if n in partial: state='parcial'
        elif n in implemented: state='implementado'
    else:
        if n in {6,7,8,9,10,11,14,15,17,18,21,22,23}:
            state='parcial'; module='config/settings.py; accounts/; frontend/; docs/'; tests='SecurityTests; main.test.jsx; build (alcance en RESULTADOS.md)'
        if n==22: state='implementado'
    rows.append(f'| {rid} | {description.replace("|", "/")} | {page} | {module} | {tests} | {state} |')
rows += ['', 'Ningún requisito completo se marca verificado por disponer solo de pruebas parciales. La evidencia ejecutada y sus límites se registran en docs/pruebas/RESULTADOS.md.', '', 'Los requisitos generales 2.1–2.8, reglas 10–19 y CU-01–CU-04 no tienen identificadores RF/RNF propios. Se analizan en ARQUITECTURA.md y CONTRATOS.md; la numeración original de reglas se conserva.']
(target/'TRAZABILIDAD.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
print(f'{len(pages)} folios; {len(requirements)} requisitos extraídos.')
if (root/'scripts/update_block2_traceability.py').exists():
    from update_block2_traceability import update
    update()
