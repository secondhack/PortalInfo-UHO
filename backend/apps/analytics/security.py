from datetime import datetime,timedelta,timezone as dt_timezone
import hashlib
from django.db.models import Count,Value,BigIntegerField
from django.db.models.functions import Extract,Floor,Cast
from django.utils import timezone
from apps.settings_app.models import GlobalSettings
from .models import AccessLog,SecurityAlert
from .periods import during,data_scope


def detect_alerts(period):
    cfg=GlobalSettings.current();seconds=cfg.security_window_minutes*60
    all_logs=data_scope(AccessLog.objects.filter(event_type='access').exclude(uid=''),period)
    logs=during(all_logs,period)
    bucket=Cast(Floor(Extract('created_at','epoch',tzinfo=dt_timezone.utc)/Value(seconds)),BigIntegerField())
    groups=logs.annotate(bucket=bucket).values('uid','bucket','demo').annotate(
        count=Count('pk'),ips=Count('ip',distinct=True),agents=Count('user_agent',distinct=True)).order_by('uid','bucket')
    created=0
    for group in groups.iterator(chunk_size=200):
        start=datetime.fromtimestamp(group['bucket']*seconds,tz=dt_timezone.utc);end=start+timedelta(seconds=seconds)
        rules=[]
        if group['ips']>=cfg.security_ip_threshold:rules.append(('multiple_ips','high' if group['ips']>=2*cfg.security_ip_threshold else 'medium'))
        if group['agents']>=cfg.security_device_threshold:rules.append(('device_churn','medium'))
        baseline=all_logs.filter(uid=group['uid'],created_at__gte=start-timedelta(seconds=seconds),created_at__lt=start).count()
        if baseline and group['count']>=cfg.security_activity_threshold and group['count']>=baseline*cfg.security_activity_multiplier:
            rules.append(('activity_spike','high'))
        for kind,priority in rules:
            key=hashlib.sha256(f'{group["uid"]}:{start.isoformat()}:{kind}:{group["demo"]}'.encode()).hexdigest()
            evidence={'accesses':group['count'],'distinct_ips':group['ips'],'device_signatures':group['agents'],
                'previous_window_accesses':baseline,'window_minutes':cfg.security_window_minutes,
                'ip_threshold':cfg.security_ip_threshold,'device_threshold':cfg.security_device_threshold,
                'activity_threshold':cfg.security_activity_threshold,'activity_multiplier':cfg.security_activity_multiplier,
                'notice':'Indicador para revisión; no demuestra uso compartido de cuentas.'}
            _,new=SecurityAlert.objects.get_or_create(event_key=key,defaults={'uid':group['uid'],'kind':kind,'priority':priority,
                'window_start':start,'window_end':end,'evidence':evidence,'demo':group['demo']})
            created+=int(new)
    return created
