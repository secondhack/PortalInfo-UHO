import ipaddress
from django.conf import settings


def client_context(request):
    """Trust a forwarded chain only when every hop traversed is explicitly trusted."""
    try: remote=ipaddress.ip_address(request.META.get('REMOTE_ADDR','127.0.0.1'))
    except ValueError: remote=ipaddress.ip_address('127.0.0.1')
    trusted=[ipaddress.ip_network(cidr,strict=False) for cidr in settings.TRUSTED_PROXY_CIDRS]
    forwarded=request.META.get('HTTP_X_FORWARDED_FOR','')
    ip=remote
    if any(remote in network for network in trusted) and len(forwarded)<=1024:
        try:
            chain=[ipaddress.ip_address(part.strip()) for part in forwarded.split(',') if part.strip()]
            if len(chain)<=20:
                for hop in reversed(chain):
                    if not any(ip in network for network in trusted): break
                    ip=hop
        except ValueError: ip=remote
    agent=request.META.get('HTTP_USER_AGENT','')[:500]
    lower=agent.lower()
    device='bot' if any(x in lower for x in ['bot','crawler','spider']) else 'tablet' if any(x in lower for x in ['ipad','tablet']) else 'mobile' if any(x in lower for x in ['android','iphone','mobile']) else 'desktop' if any(x in lower for x in ['windows','macintosh','linux','x11']) else 'unknown'
    return {'ip':str(ip),'user_agent':agent,'device':device}


def audit_summary(instance,fields):
    allowed={'code','name','role','is_active','authorized','categories','visible','active','max_visible','title_limit',
        'description_limit','category','operation','user','validity','starts_at','ends_at','manual_active','state',
        'revision','retention_days','login_attempts','session_seconds','lockout_seconds','email_notifications',
        'security_window_minutes','security_ip_threshold','security_device_threshold','security_activity_threshold','security_activity_multiplier'}
    result={}
    for field in set(fields)&allowed:
        value=getattr(instance,field,None)
        if hasattr(value,'values_list'): value=list(value.values_list('pk',flat=True))
        elif hasattr(value,'pk'): value=value.pk
        elif hasattr(value,'isoformat'): value=value.isoformat()
        if isinstance(value,(str,int,float,bool,list)) or value is None: result[field]=value
    return result
