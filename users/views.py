from django.contrib.auth import get_user_model, login, logout
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwnerOrReadOnly
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserPublicSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response(
            {
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
                'token': token.key
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        token, created = Token.objects.get_or_create(user=user)
        
        login(request, user)
        
        return Response(
            {
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
                'token': token.key
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass
        
        logout(request)
        
        return Response({"detail": _("Successfully logged out.")}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return User.objects.all()
        
        return User.objects.filter(is_public_profile=True) | User.objects.filter(id=user.id)
    
    def get_serializer_class(self):
        user_id = self.kwargs.get('pk')
        
        if user_id and int(user_id) != self.request.user.id and not self.request.user.is_staff:
            return UserPublicSerializer
            
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
            
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticatedOrReadOnly()]
            
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['post'],
        serializer_class=ChangePasswordSerializer,
        url_path='change-password'
    )
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        Token.objects.filter(user=request.user).delete()
        token, created = Token.objects.get_or_create(user=request.user)
        
        return Response(
            {
                "detail": _("Password updated successfully."),
                "token": token.key
            },
            status=status.HTTP_200_OK
        )
