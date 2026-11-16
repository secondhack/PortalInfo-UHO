import secrets
from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils.crypto import salted_hmac
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response as APIResponse
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from apps.settings_app.models import GlobalSettings
from .models import Content, Submission, Response
from .queries import visible_publications


class VoteThrottle(SimpleRateThrottle):
    scope='survey_vote'
    rate='10/min'
    def get_cache_key(self,request,view):
        return self.cache_format % {'scope':self.scope,'ident':request.META.get('REMOTE_ADDR','unknown')}


class AnswerSerializer(serializers.Serializer):
    question=serializers.IntegerField(min_value=1)
    options=serializers.ListField(child=serializers.IntegerField(min_value=1),required=False,default=list,max_length=100)
    value=serializers.CharField(required=False,allow_blank=True,default='',max_length=4000)


class VoteSerializer(serializers.Serializer):
    answers=AnswerSerializer(many=True)


@method_decorator(csrf_protect,name='dispatch')
class SurveyAnswerView(APIView):
    permission_classes=[AllowAny]
    throttle_classes=[VoteThrottle]

    @extend_schema(request=VoteSerializer,responses={201:dict})
    def post(self,request,pk):
        from apps.portal.identity import visitor,pseudonym
        portal=visitor(request)
        cfg=GlobalSettings.current()
        if cfg.vote_requires_auth and not portal and (not request.user.is_authenticated or not request.user.is_active or not request.user.authorized):
            raise PermissionDenied('Esta encuesta requiere iniciar sesión en el portal.')
        serializer=VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cookie=request.COOKIES.get('portalinfo_respondent')
        try: anonymous=signing.loads(cookie,salt='survey-respondent',max_age=86400*90) if cookie else None
        except signing.BadSignature: anonymous=None
        anonymous=anonymous if isinstance(anonymous,str) and len(anonymous)<=100 else secrets.token_urlsafe(32)
        identity=pseudonym(portal) if portal else (f'user:{request.user.pk}' if request.user.is_authenticated else f'browser:{anonymous}')
        key=salted_hmac('survey-response',identity).hexdigest()
        with transaction.atomic():
            # Serialize votes with editorial changes, deletion and new publications.
            if not Content.objects.select_for_update().filter(pk=pk,deleted_at__isnull=True).exists():
                raise NotFound('Encuesta no disponible.')
            publication=visible_publications().filter(content_id=pk,category__content_type='survey').first()
            if not publication: raise NotFound('Encuesta no disponible o fuera del límite visible.')
            definition=publication.data['details']
            if definition.get('external_url'):
                raise ValidationError('Las encuestas externas se responden en su enlace, no en esta API.')
            questions={q['id']:q for q in definition['questions']}
            answers=serializer.validated_data['answers']
            if len(answers)>cfg.max_questions or len(answers)>len(questions):
                raise ValidationError('Demasiadas respuestas.')
            seen=set()
            for answer in answers:
                q=questions.get(answer['question'])
                if not q or q['id'] in seen: raise ValidationError('Pregunta ajena o duplicada.')
                seen.add(q['id'])
                options=answer['options']
                allowed={o['id'] for o in q['options']}
                if len(options)!=len(set(options)) or not set(options)<=allowed or len(options)>cfg.max_options:
                    raise ValidationError('Opciones inválidas para esta pregunta.')
                if q['kind']=='open':
                    if options or (q['required'] and not answer['value'].strip()) or not cfg.allow_open_questions:
                        raise ValidationError('Respuesta abierta inválida o deshabilitada.')
                else:
                    if answer['value'] or (q['required'] and not options) or (q['kind']=='single' and len(options)>1):
                        raise ValidationError('La selección no corresponde al tipo de pregunta.')
            if any(q['required'] and q['id'] not in seen for q in questions.values()):
                raise ValidationError('Complete las preguntas obligatorias.')
            try:
                with transaction.atomic(): submission=Submission.objects.create(publication=publication,respondent_key=key)
            except IntegrityError:
                raise ValidationError('Ya se registró una respuesta de esta identidad/navegador para esta versión.')
            for answer in answers:
                if not answer['options'] and not answer['value'].strip(): continue
                row=Response.objects.create(submission=submission,question_id=answer['question'],respondent_key=key,value=answer['value'])
                row.options.set(answer['options'])
        result=APIResponse({'detail':'Respuesta registrada.','submission':submission.pk},status=201)
        if not request.user.is_authenticated and not portal:
            result.set_cookie('portalinfo_respondent',signing.dumps(anonymous,salt='survey-respondent'),max_age=86400*90,
                httponly=True,secure=settings.PRODUCTION,samesite='Lax')
        return result


def survey_submissions(item,period=None):
    qs=Submission.objects.filter(publication__content=item)
    if period:
        from apps.analytics.periods import during,data_scope
        qs=data_scope(during(qs,period),period)
    return qs


def survey_results(item,period=None):
    from django.db.models import Count
    submissions=survey_submissions(item,period)
    answers=Response.objects.filter(submission__in=submissions)
    totals={r['publication_id']:r for r in submissions.values('publication_id').annotate(total=Count('pk'),participants=Count('respondent_key',distinct=True))}
    counts={(r['submission__publication_id'],r['question_id']):r['count'] for r in answers.values('submission__publication_id','question_id').annotate(count=Count('pk'))}
    distribution={(r['submission__publication_id'],r['question_id'],r['options']):r['count'] for r in answers.exclude(options=None).values('submission__publication_id','question_id','options').annotate(count=Count('pk'))}
    versions=[]
    for publication in item.publications.filter(data__type='survey').order_by('-version').iterator(chunk_size=100):
        rows=[]
        for question in publication.data['details'].get('questions',[]):
            qid=question['id'];denominator=counts.get((publication.pk,qid),0)
            options=[]
            for option in question['options']:
                count=distribution.get((publication.pk,qid,option['id']),0)
                options.append({'id':option['id'],'text':option['text'],'count':count,'percentage':round(100*count/denominator,2) if denominator else 0})
            opened=answers.filter(submission__publication=publication,question_id=qid).order_by('pk') if question['kind']=='open' else None
            rows.append({'id':qid,'text':question['text'],'kind':question['kind'],'answered':denominator,'options':options,
                'open_answers':list(opened.values_list('value',flat=True)[:100]) if opened is not None else [],
                'open_answers_truncated':question['kind']=='open' and denominator>100})
        total=totals.get(publication.pk,{})
        versions.append({'version':publication.version,'publication':publication.pk,'total':total.get('total',0),
            'participants':total.get('participants',0),'questions':rows})
    return {'versions':versions,'total':submissions.count(),'participants':submissions.values('respondent_key').distinct().count(),
        'answers_total':answers.count(),'demo_submissions':submissions.filter(demo=True).count(),
        'period':period,'percentage_basis':'Respuestas por pregunta; selección múltiple puede sumar más del 100 %.'}
