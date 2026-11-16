from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.accounts.views import CSRFView, LoginView, LogoutView, MeView, UserViewSet, RoleViewSet, GrantViewSet
from apps.catalogs.views import CategoryViewSet, CatalogItemViewSet, CatalogTypeViewSet
from apps.settings_app.views import HealthView, DashboardView, SettingsView, AuditViewSet, PublicConfigView
from apps.content.views import ContentViewSet, ContentMetadataView, PublicContentsView, PublicCategoriesView
from apps.content.surveys import SurveyAnswerView
from apps.notifications.views import NotificationViewSet
from apps.approvals.views import ApprovalViewSet
from apps.analytics.views import RecordView,DemoPortalAccessView,StatisticsView,AccessLogViewSet,SecurityAlertViewSet
from apps.analytics.reports import ReportView
from apps.portal.views import VisitorSessionView, VisitorLogoutView, portal_html

router = DefaultRouter()
for route, view in [('users',UserViewSet),('roles',RoleViewSet),('permissions',GrantViewSet),
    ('categories',CategoryViewSet),('catalog-types',CatalogTypeViewSet),('catalog-items',CatalogItemViewSet),('audit',AuditViewSet),('contents',ContentViewSet),
    ('notifications',NotificationViewSet),('approvals',ApprovalViewSet),('access-logs',AccessLogViewSet),('security-alerts',SecurityAlertViewSet)]:
    router.register(route,view)
urlpatterns = [path('api/health/',HealthView.as_view()), path('api/csrf/',CSRFView.as_view()),
    path('portal/', portal_html),
    path('portal-auth/session', VisitorSessionView.as_view()),
    path('portal-auth/logout', VisitorLogoutView.as_view()),
    path('auth/login',LoginView.as_view()),path('auth/logout',LogoutView.as_view()),
    path('api/me/',MeView.as_view()),path('api/admin/dashboard/',DashboardView.as_view()),
    path('api/admin/settings/',SettingsView.as_view()),path('api/config',PublicConfigView.as_view()),
    path('api/admin/content-metadata/',ContentMetadataView.as_view()),
    path('api/admin/estadisticas',StatisticsView.as_view()),
    path('api/admin/logs',AccessLogViewSet.as_view({'get':'list'})),
    path('api/admin/reports/<slug:kind>/',ReportView.as_view()),
    path('api/demo/portal-access/',DemoPortalAccessView.as_view()),
    path('api/vistas',RecordView.as_view()),
    path('api/categorias',PublicCategoriesView.as_view()),
    path('api/noticias',PublicContentsView.as_view(),{'slug':'noticias'}),
    path('api/eventos',PublicContentsView.as_view(),{'slug':'eventos'}),
    path('api/avisos',PublicContentsView.as_view(),{'slug':'avisos'}),
    path('api/servicios',PublicContentsView.as_view(),{'slug':'servicios'}),
    path('api/encuestas',PublicContentsView.as_view(),{'slug':'encuestas'}),
    path('api/encuestas/<int:pk>/respuestas',SurveyAnswerView.as_view()),
    path('api/admin/',include(router.urls)),path('api/schema/',SpectacularAPIView.as_view(),name='schema'),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/docs',SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/<slug:slug>',PublicContentsView.as_view())]
