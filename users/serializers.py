from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'bio', 'profile_picture', 'weight_unit', 'is_public_profile',
            'date_joined'
        ]
        read_only_fields = ['id', 'email', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserPublicSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'profile_picture', 'date_joined']
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'weight_unit']
        extra_kwargs = {
            'email': {'required': True},
            'weight_unit': {'required': False}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': _("Passwords don't match.")})
        
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': _("User with this email already exists.")})
            
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            weight_unit=validated_data.get('weight_unit', 'g')
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({'email': _("User with this email doesn't exist.")})
                
            user = authenticate(
                request=self.context.get('request'),
                username=user.username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError({'password': _("Invalid password.")})
        else:
            raise serializers.ValidationError(_("Both email and password are required."))
            
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {'new_password_confirm': _("New passwords don't match.")}
            )
            
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': _("New password must be different from the old one.")}
            )
            
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Incorrect old password."))
        return value