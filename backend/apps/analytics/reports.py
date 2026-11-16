import csv
import io
import json
from xml.sax.saxutils import escape
from django.conf import settings
from django.http import StreamingHttpResponse,HttpResponse
from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import StaffAccess,role_code
from apps.audit.models import AuditEvent,record
from apps.content.models import Content,Response as SurveyResponse
from apps.content.surveys import survey_results,survey_submissions
from .filters import access_rows,AuditFilter
from .models import SecurityAlert
from .periods import PeriodSerializer,period_from,during,data_scope
from .metrics import portal_metrics


class ReportQuery(PeriodSerializer):
    file_format=serializers.ChoiceField(choices=['csv','pdf'],default='csv')
    content=serializers.IntegerField(required=False)
    category=serializers.IntegerField(required=False)
    state=serializers.CharField(required=False)
    actor=serializers.IntegerField(required=False)
    action=serializers.CharField(required=False)
    entity=serializers.CharField(required=False)
    search=serializers.CharField(required=False)
    device=serializers.CharField(required=False)
    user_type=serializers.CharField(required=False)
    event_type=serializers.ChoiceField(choices=['access','view'],required=False)
    section=serializers.CharField(required=False)
    uid=serializers.CharField(required=False)
    priority=serializers.ChoiceField(choices=['low','medium','high'],required=False)
    reviewed=serializers.BooleanField(required=False)


def safe_csv(value):
    if value is None:return ''
    if isinstance(value,(int,float)):return value
    text=str(value)
    if text.lstrip(' \t\r\n\ufeff').startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')):
        return "'"+text
    return text


class Echo:
    def write(self,value):return value


def csv_response(headers,rows,name):
    def stream():
        writer=csv.writer(Echo())
        yield '\ufeff'
        yield writer.writerow(headers)
        for row in rows:yield writer.writerow([safe_csv(value) for value in row])
    response=StreamingHttpResponse(stream(),content_type='text/csv; charset=utf-8')
    response['Content-Disposition']=f'attachment; filename="portalinfo-{name}.csv"'
    return response


def pdf_response(headers,rows,name,period):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
    limit=getattr(settings,'REPORT_PDF_MAX_ROWS',2000)
    body=[]
    for index,row in enumerate(rows):
        if index>=limit:raise ValidationError(f'PDF limitado a {limit} filas. Reduzca los filtros o utilice CSV.')
        body.append(row)
    output=io.BytesIO();styles=getSampleStyleSheet()
    small=ParagraphStyle('report-cell',fontName='Helvetica',fontSize=7,leading=9,wordWrap='CJK')
    def cell(value):return Paragraph(escape(str(value if value is not None else '')[:600]),small)
    table=[[cell(h) for h in headers]]+[[cell(v) for v in row] for row in body]
    width,height=landscape(A4)
    document=SimpleDocTemplate(output,pagesize=(width,height),leftMargin=30,rightMargin=30,topMargin=35,bottomMargin=35,title='PortalInfo UHO - '+name)
    contents=[Paragraph('PortalInfo UHO',styles['Title']),Paragraph(escape(name),styles['Heading2']),
        Paragraph(f'Período: {period["start"].date()} a {period["end"].date()} (fin exclusivo), {period["timezone"]}. Fuente: {period["data_scope"]}.',styles['Normal']),
        Paragraph('Generado: '+timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),styles['Normal']),
        Paragraph(f'Resumen: {len(body)} filas. Las celdas extensas se resumen; CSV conserva el texto completo.',styles['Normal']),Spacer(1,14)]
    grid=LongTable(table,colWidths=[(width-60)/len(headers)]*len(headers),repeatRows=1)
    grid.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edfa')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#ccd9e8')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    contents.append(grid)
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.drawString(30,18,f'PortalInfo UHO · Página {doc.page}');canvas.restoreState()
    document.build(contents,onFirstPage=footer,onLaterPages=footer)
    response=HttpResponse(output.getvalue(),content_type='application/pdf')
    response['Content-Disposition']=f'attachment; filename="portalinfo-{name}.pdf"'
    return response


def report_rows(kind,params,period,user):
    if kind=='general':
        stats=portal_metrics(period)
        rows=[('Accesos','total',stats['accesses']),('Visualizaciones','total',stats['views']),('Cuentas identificadas','total',stats['identified_accounts'])]
        for metric,field in [('by_day','date'),('by_week','date'),('by_month','date'),('by_device','device'),('by_user_type','user_type'),('by_hour','hour'),('by_section','section')]:
            rows.extend((metric,row[field],row['count']) for row in stats[metric])
        return ['Métrica','Grupo','Valor'],iter(rows)
    if kind=='accesses':
        qs=access_rows(params,period)
        return ['ID','Fecha','Identidad seudónima','Tipo','IP','Dispositivo','User-Agent','Sección','Evento','DEMO'],qs.values_list('id','created_at','uid','user_type','ip','device','user_agent','section','event_type','demo').iterator(chunk_size=500)
    if kind=='contents':
        qs=during(Content.objects.filter(deleted_at__isnull=True),period)
        if period['data_scope']=='real':qs=qs.filter(seed_key__isnull=True)
        elif period['data_scope']=='demo':qs=qs.filter(seed_key__isnull=False)
        if params.get('category'):
            if not params['category'].isdigit():raise ValidationError('Categoría inválida.')
            qs=qs.filter(category_id=int(params['category']))
        if params.get('state'):qs=qs.filter(state=params['state'])
        if params.get('search'):qs=qs.filter(title__icontains=params['search'])
        return ['ID','Categoría','Título','Estado','Revisión','Fecha creación','DEMO'],((row.id,row.category.name,row.title,row.state,row.revision,row.created_at,bool(row.seed_key)) for row in qs.select_related('category').order_by('category__name','pk').iterator(chunk_size=500))
    if kind=='audit':
        if role_code(user)!='superadmin':raise PermissionDenied('Reporte de auditoría reservado al Superadmin.')
        filtered=AuditFilter(params,queryset=during(AuditEvent.objects.all(),period))
        if not filtered.is_valid():raise ValidationError(filtered.errors)
        qs=filtered.qs
        if params.get('search'):qs=qs.filter(Q(action__icontains=params['search'])|Q(resource__icontains=params['search']))
        headers=['ID','Fecha','Actor ID','Acción','Entidad','Recurso','IP','Resumen']
        return headers,((r.id,r.created_at,r.actor_id,r.action,r.entity,r.resource,r.ip,json.dumps(r.metadata,ensure_ascii=False)) for r in qs.order_by('-created_at','-pk').iterator(chunk_size=500))
    if kind=='security':
        qs=data_scope(SecurityAlert.objects.filter(window_end__gt=period['start'],window_start__lt=period['end']),period)
        for name in ['priority','kind','uid']:
            if params.get(name):qs=qs.filter(**{name:params[name]})
        if params.get('search'):qs=qs.filter(Q(uid__icontains=params['search'])|Q(kind__icontains=params['search']))
        if params.get('reviewed') in ['true','false']:qs=qs.filter(reviewed_at__isnull=params['reviewed']=='false')
        return ['ID','Identidad','Tipo','Prioridad','Inicio','Fin','Revisada','Evidencia','DEMO'],((r.id,r.uid,r.kind,r.priority,r.window_start,r.window_end,bool(r.reviewed_at),json.dumps(r.evidence,ensure_ascii=False),r.demo) for r in qs.order_by('-window_start','-pk').iterator(chunk_size=500))
    if kind=='surveys':
        pk=params.get('content','')
        if not pk.isdigit():raise ValidationError('Seleccione una encuesta mediante content.')
        item=Content.objects.filter(pk=int(pk),category__content_type='survey',deleted_at__isnull=True).first()
        if not item:raise ValidationError('Encuesta no disponible.')
        stats=survey_results(item,period)
        def rows():
            yield ['Todas','Envíos','resumen','',stats['total'],'']
            yield ['Todas','Participantes seudónimos','resumen','',stats['participants'],'']
            for version in stats['versions']:
                for q in version['questions']:
                    for option in q['options']:yield [version['version'],q['text'],q['kind'],option['text'],option['count'],option['percentage']]
            opened=SurveyResponse.objects.filter(submission__in=survey_submissions(item,period),question__kind='open').select_related('question','submission__publication').order_by('pk')
            for answer in opened.iterator(chunk_size=500):yield [answer.submission.publication.version,answer.question.text,'open',answer.value,1,'']
        return ['Versión','Pregunta','Tipo','Opción / texto','Respuestas','Porcentaje'],rows()
    raise ValidationError('Tipo de reporte desconocido.')


class ReportView(APIView):
    permission_classes=[StaffAccess]
    @extend_schema(parameters=[ReportQuery],responses={(200,'text/csv'):bytes,(200,'application/pdf'):bytes})
    def get(self,request,kind):
        period=period_from(request.query_params)
        fmt=request.query_params.get('file_format','csv')
        if fmt not in ['csv','pdf']:raise ValidationError('file_format debe ser csv o pdf.')
        headers,rows=report_rows(kind,request.query_params,period,request.user)
        response=csv_response(headers,rows,kind) if fmt=='csv' else pdf_response(headers,rows,kind,period)
        record(request,'report.export',kind,{'file_format':fmt,'period':period['name'],'data_scope':period['data_scope']})
        return response
