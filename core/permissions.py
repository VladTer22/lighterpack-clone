from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        owner_attr = getattr(obj, "owner", None)
        if owner_attr is not None:
            return obj.owner == request.user
            
        user_attr = getattr(obj, "user", None)
        if user_attr is not None:
            return obj.user == request.user
            
        creator_attr = getattr(obj, "creator", None)
        if creator_attr is not None:
            return obj.creator == request.user
            
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        owner_attr = getattr(obj, "owner", None)
        if owner_attr is not None:
            return obj.owner == request.user
            
        user_attr = getattr(obj, "user", None)
        if user_attr is not None:
            return obj.user == request.user
            
        creator_attr = getattr(obj, "creator", None)
        if creator_attr is not None:
            return obj.creator == request.user
            
        return False


class IsOwnerOrPublic(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
            
        if request.method in permissions.SAFE_METHODS:
            is_public_attr = getattr(obj, "is_public", None)
            if is_public_attr is not None:
                return obj.is_public
                
            public_attr = getattr(obj, "public", None)
            if public_attr is not None:
                return obj.public
                
        return False