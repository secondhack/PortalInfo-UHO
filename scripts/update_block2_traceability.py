"""Overlay executed Block 2 coverage without altering original SRS descriptions."""
from pathlib import Path

root=Path(__file__).resolve().parent.parent


def update():
    path=root/'docs/arquitectura/TRAZABILIDAD.md'
    if '| Limitaciones |' in path.read_text(encoding='utf-8-sig'):
        from update_final_traceability import update as final_update
        final_update()
        return
    path=root/'docs/arquitectura/TRAZABILIDAD.md'
    rows=[]
    verified=set(range(19,28))|set(range(29,33))|{39,40,41,49,51,52,53,54,55,56,57,59,60,61}
    partial={28,46,50}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('| RF-'):
            columns=line.split('|')
            number=int(columns[1].strip().split('-')[1])
            if number in verified|partial:
                columns[4]=' content/services.py, queries.py, serializers.py, views.py, surveys.py; frontend Contents/ContentEditor/SurveyEditor; BLOQUE_2.md '
                columns[5]=' ContentTests (CRUD, permisos, vigencia, límites, revisiones, encuestas y API pública); content.test.jsx; smoke_content_http.py; RESULTADOS.md '
                columns[6]=' verificado ' if number in verified else ' parcial '
                line='|'.join(columns)
        if line.startswith('Ningún requisito completo se marca verificado'):
            line='Los estados verificados del Bloque 2 se sustentan en ContentTests, pruebas de componentes y smoke HTTP; no acreditan integración AGA_AUTH, pfSense, carga ni WCAG. Evidencia y límites en docs/pruebas/RESULTADOS.md.'
        rows.append(line)
    marker='## Cobertura del Bloque 2'
    text='\n'.join(rows).split(marker)[0].rstrip()
    text+='\n\n'+marker+'\n\nRF-28/50 conservan estado parcial porque falta la adaptación del portal pfSense. RF-46 tiene resultados iniciales por versión; la analítica integral sigue pendiente. RF-58 (registro de vistas) permanece pendiente. RF-60 verifica descubrimiento/API de categorías dinámicas, no una interfaz pfSense. Los contratos actuales se detallan en BLOQUE_2.md.\n'
    path.write_text(text,encoding='utf-8')
    if (root/'scripts/update_block3_traceability.py').exists():
        from update_block3_traceability import update as update_next
        update_next()


if __name__=='__main__':update()
