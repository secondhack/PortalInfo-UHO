import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if os.name == 'nt' and Path('C:/Program Files/PostgreSQL/16/bin').exists():
    os.environ['PATH'] = 'C:/Program Files/PostgreSQL/16/bin;' + os.environ.get('PATH', '')
load_dotenv(BASE_DIR.parent / '.env')
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.getenv('PORTALINFO_DEBUG', os.getenv('DEBUG', 'false')).lower() == 'true'
APP_ENV = os.getenv('APP_ENV', 'production').strip().lower()
if APP_ENV not in {'development','test','production'}:
    raise ImproperlyConfigured('APP_ENV debe ser development, test o production; no se interpreta un valor desconocido como demo.')
PRODUCTION = APP_ENV == 'production'
AUTH_PROVIDER = os.getenv('AUTH_PROVIDER', 'aga')
if PRODUCTION and (DEBUG or AUTH_PROVIDER == 'demo'):
    raise ImproperlyConfigured('Producción no permite DEBUG ni autenticación demo.')
if PRODUCTION and (len(SECRET_KEY)<32 or SECRET_KEY.startswith('replace-')):
    raise ImproperlyConfigured('Producción requiere SECRET_KEY propia y suficientemente larga.')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.staticfiles', 'rest_framework', 'django_filters',
    'corsheaders', 'drf_spectacular', 'drf_spectacular_sidecar',
    'apps.catalogs', 'apps.accounts', 'apps.content', 'apps.approvals',
    'apps.notifications', 'apps.analytics', 'apps.audit', 'apps.settings_app', 'apps.portal',
]
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'apps.audit.middleware.SecurityAuditMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql',
    'CONN_MAX_AGE':int(os.getenv('DATABASE_CONN_MAX_AGE','60')),'CONN_HEALTH_CHECKS':True,
    'NAME': os.environ['DATABASE_NAME'], 'USER': os.environ['DATABASE_USER'],
    'PASSWORD': os.environ['DATABASE_PASSWORD'], 'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
    'PORT': os.getenv('DATABASE_PORT', '5432')}}
AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Havana'
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
SECURE_SSL_REDIRECT = PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if PRODUCTION else 0
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 1800
CORS_ALLOWED_ORIGINS = ['http://localhost:5174', 'http://127.0.0.1:5174'] if DEBUG else []
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = True
REST_FRAMEWORK = {
    'NUM_PROXIES': 0,
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['apps.accounts.permissions.AuthorizedAccess'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter', 'rest_framework.filters.OrderingFilter'],
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '120/min', 'user': '600/min'},
}
SPECTACULAR_SETTINGS = {'TITLE': 'PortalInfo UHO', 'VERSION': '1.0.0',
    'OAS_VERSION': '3.0.3', 'SWAGGER_UI_DIST': 'SIDECAR', 'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'SERVE_PERMISSIONS': ['apps.accounts.permissions.SuperAccess'] if PRODUCTION else ['rest_framework.permissions.AllowAny']}
TRUSTED_PROXY_CIDRS=[x.strip() for x in os.getenv('TRUSTED_PROXY_CIDRS','').split(',') if x.strip()]
EMAIL_MODE=os.getenv('EMAIL_MODE','file')
if EMAIL_MODE=='smtp' and not PRODUCTION:
    raise ImproperlyConfigured('La demostración no permite SMTP real.')
EMAIL_BACKEND={'file':'django.core.mail.backends.filebased.EmailBackend','console':'django.core.mail.backends.console.EmailBackend',
    'memory':'django.core.mail.backends.locmem.EmailBackend','smtp':'django.core.mail.backends.smtp.EmailBackend'}.get(EMAIL_MODE)
if not EMAIL_BACKEND: raise ImproperlyConfigured('Proveedor de correo desconocido.')
EMAIL_FILE_PATH=BASE_DIR.parent/'.local'/'mail'
DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL','portalinfo-demo@example.invalid')
EMAIL_HOST=os.getenv('EMAIL_HOST','')
if EMAIL_MODE=='smtp' and not EMAIL_HOST:
    raise ImproperlyConfigured('SMTP requiere EMAIL_HOST explícito; no se supone un servidor institucional.')
EMAIL_PORT=int(os.getenv('EMAIL_PORT','587'))
EMAIL_HOST_USER=os.getenv('EMAIL_HOST_USER','')
EMAIL_HOST_PASSWORD=os.getenv('EMAIL_HOST_PASSWORD','')
EMAIL_USE_TLS=os.getenv('EMAIL_USE_TLS','true').lower()=='true'
EMAIL_TIMEOUT=10
REPORT_PDF_MAX_ROWS=int(os.getenv('REPORT_PDF_MAX_ROWS','2000'))
PORTAL_AUTH_MODE = os.getenv('PORTAL_AUTH_MODE', 'institutional' if PRODUCTION else 'demo')
if PORTAL_AUTH_MODE not in ('demo', 'institutional') or (PRODUCTION and PORTAL_AUTH_MODE == 'demo'):
    raise ImproperlyConfigured('Modo de autenticación del portal no permitido.')
PORTAL_DEMO_USERS_FILE = BASE_DIR.parent / '.local' / 'portal-demo-users.json'
PORTAL_HTML_FILE = Path(os.getenv('PORTAL_HTML_FILE', str(BASE_DIR.parent / 'captive-portal/dist/index.html')))
PORTAL_WIFI_LABEL = os.getenv('PORTAL_WIFI_LABEL', 'Red WiFi · UHO')
PORTAL_WELCOME_TEXT = os.getenv('PORTAL_WELCOME_TEXT', 'Información, servicios y comunidad en un mismo lugar.')
# For a separately hosted static portal, explicitly list its trusted TLS origin.
if os.getenv('PORTAL_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS += [x.strip() for x in os.environ['PORTAL_ALLOWED_ORIGINS'].split(',') if x.strip()]
    CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS)
