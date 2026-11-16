from django.db.models import Count,Q,F
from django.db.models.functions import TruncDay,TruncWeek,TruncMonth,ExtractHour
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.permissions import role_code
from apps.approvals.models import Approval
from apps.content.models import Content,Submission
from apps.content.queries import allowed_categories,visible_publications
from .models import AccessLog,ContentView
from .periods import during,data_scope


def grouped(qs,field):
    return list(qs.order_by().values(field).annotate(count=Count('pk')).order_by('-count',field))


def timeline(qs,function):
    rows=qs.annotate(bucket=function('created_at',tzinfo=timezone.get_current_timezone())).values('bucket').annotate(count=Count('pk')).order_by('bucket')
    return [{'date':row['bucket'].date().isoformat(),'count':row['count']} for row in rows]


def dashboard(user,period):
    categories=allowed_categories(user)
    content=Content.objects.filter(category__in=categories,deleted_at__isnull=True)
    active_ids=visible_publications().filter(category__in=categories).values('content_id')
    counts=content.aggregate(total=Count('pk'),active=Count('pk',filter=Q(pk__in=active_ids)),pending=Count('pk',filter=Q(state='pending')))
    by_category=list(content.values('category_id','category__name').annotate(total=Count('pk'),active=Count('pk',filter=Q(pk__in=active_ids)),pending=Count('pk',filter=Q(state='pending'))).order_by('category__name'))
    submissions=data_scope(during(Submission.objects.filter(publication__category__in=categories),period),period)
    views=data_scope(during(ContentView.objects.filter(category__in=categories,content__category__in=categories),period),period)
    staff=role_code(user) in ['admin','superadmin']
    logs=data_scope(during(AccessLog.objects.filter(event_type='access'),period),period)
    return {'period':period,'users':User.objects.filter(is_active=True,authorized=True).count() if staff else None,
        'categories':categories.count(),'contents':counts['total'],'active':counts['active'],'inactive':counts['total']-counts['active'],
        'pending':counts['pending'],'requests_pending':Approval.objects.filter(state='pending',version=F('content__revision'),content__in=content).count(),
        'created_in_period':during(content,period).count(),'by_category':by_category,'by_state':grouped(content,'state'),
        'accesses':logs.count() if staff else None,'views':data_scope(during(ContentView.objects.all(),period),period).count() if staff else views.count(),
        'survey_submissions':submissions.count(),'survey_participants':submissions.values('respondent_key').distinct().count(),
        'top_contents':list(views.order_by().values('content_id','content__title').annotate(count=Count('pk')).order_by('-count','content_id')[:10]),
        'demo_contents':content.filter(seed_key__isnull=False).count(),'portal_analytics':'Métricas del período obtenidas de PostgreSQL.'}


def portal_metrics(period):
    accesses=data_scope(during(AccessLog.objects.filter(event_type='access'),period),period)
    views=data_scope(during(ContentView.objects.all(),period),period)
    return {'period':period,'accesses':accesses.count(),'views':views.count(),
        'identified_accounts':accesses.exclude(uid='').values('uid').distinct().count(),
        'demo_accesses':accesses.filter(demo=True).count(),'demo_views':views.filter(demo=True).count(),
        'by_day':timeline(accesses,TruncDay),'by_week':timeline(accesses,TruncWeek),'by_month':timeline(accesses,TruncMonth),
        'views_by_day':timeline(views,TruncDay),'by_user_type':grouped(accesses,'user_type'),'by_device':grouped(accesses,'device'),
        'by_hour':list(accesses.annotate(hour=ExtractHour('created_at',tzinfo=timezone.get_current_timezone())).values('hour').annotate(count=Count('pk')).order_by('hour')),
        'by_section':grouped(views,'section'),
        'by_category':list(views.exclude(category=None).order_by().values('category_id','category__name').annotate(count=Count('pk')).order_by('-count','category_id')),
        'top_contents':list(views.exclude(content=None).order_by().values('content_id','content__title').annotate(count=Count('pk')).order_by('-count','content_id')[:20])}
