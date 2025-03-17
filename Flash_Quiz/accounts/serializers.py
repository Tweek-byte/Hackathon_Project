from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'department', 
                 'major', 'semester', 'profile_picture')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        
        if user.is_professor():
            user.department = validated_data.get('department', '')
        elif user.is_student():
            user.major = validated_data.get('major', '')
            user.semester = validated_data.get('semester')
            
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'department', 
                 'major', 'semester', 'profile_picture') 