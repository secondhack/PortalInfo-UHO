from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification,MailDelivery


class NotificationSerializer(serializers.ModelSerializer):
    mail_state=serializers.CharField(source='mail_delivery.state',read_only=True,default='disabled')
    class Meta:
        model=Notification
        fields=['id','kind','title','message','resource_type','resource_id','read','read_at','created_at','demo','mail_state']
        read_only_fields=fields


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=NotificationSerializer
    queryset=Notification.objects.none()
    filterset_fields=['read','kind']
    ordering=['-created_at','-id']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('mail_delivery').order_by('-created_at','-id')

    @extend_schema(responses={200:dict})
    @action(detail=False,methods=['get'])
    def unread(self,request):
        return Response({'count':self.get_queryset().filter(read=False).count()})

    @extend_schema(request=None,responses=NotificationSerializer)
    @action(detail=True,methods=['post'])
    def mark_read(self,request,pk=None):
        notification=self.get_object()
        if not notification.read:
            Notification.objects.filter(pk=notification.pk,read=False).update(read=True,read_at=timezone.now())
            notification.refresh_from_db()
        return Response(self.get_serializer(notification).data)

    @extend_schema(request=None,responses={200:dict})
    @action(detail=False,methods=['post'])
    def mark_all_read(self,request):
        count=Notification.objects.filter(recipient=request.user,read=False).update(read=True,read_at=timezone.now())
        return Response({'marked':count})
