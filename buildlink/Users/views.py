from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema

from Users.models import User
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    WorkerProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)


# ----------------------------
# Register API
# ----------------------------
class RegisterView(generics.CreateAPIView):
    """
    Handles registration for all roles:
    - Worker: Requires national ID and trade
    - Company: Requires company_name, license, and registration number
    - Owner: Standard registration with optional company details
    - Student: Simple registration
    """
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        Register a new user with their role and credentials.
        """
        return super().post(request, *args, **kwargs)
    

# ----------------------------
# Login API
# ----------------------------
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomLoginSerializer(TokenObtainPairSerializer):
    """
    Custom login serializer to authenticate using role, email, and password.
    """
    def validate(self, attrs):
        email = self.initial_data.get("email")
        role = self.initial_data.get("role")
        password = self.initial_data.get("password")

        if not email or not role or not password:
            raise status.ValidationError("Email, role, and password are required for login.")

        try:
            user = User.objects.get(email=email, role=role)
        except User.DoesNotExist:
            raise status.ValidationError("Invalid credentials or role.")

        if not user.check_password(password):
            raise status.ValidationError("Invalid credentials.")

        # Generate JWT tokens
        data = super().validate(attrs)
        data['role'] = user.role
        data['full_name'] = user.full_name
        data['email'] = user.email
        return data


class LoginView(TokenObtainPairView):
    serializer_class = CustomLoginSerializer
    serializer_class= permissions.AllowAny
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        Login with credentials.
        """
        return super().post(request, *args, **kwargs)
    

# ----------------------------
# Logout API
# ----------------------------
class LogoutView(APIView):
    """
    Blacklist the refresh token upon logout.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        Logout.
        """
        return super().post(request, *args, **kwargs)
    
    
    

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------
# User Profile (Generic)
# ----------------------------
class UserProfileView(APIView):
    """
    Fetch current user's profile based on token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        User profile.
        """
        return super().post(request, *args, **kwargs)
    

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ----------------------------
# Worker Profile
# ----------------------------
class WorkerProfileView(generics.RetrieveUpdateAPIView):
    """
    Workers can view and update their profile,
    including trades and National ID verification.
    """
    serializer_class = WorkerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        worker profile.
        """
        return super().post(request, *args, **kwargs)
    

    def get_object(self):
        return self.request.user


# ----------------------------
# Company Verification
# ----------------------------
class CompanyVerificationView(APIView):
    """
    Allows admin to verify or reject a company account.
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        verify company by admin
        """
        return super().post(request, *args, **kwargs)

    def post(self, request, company_id):
        try:
            company = User.objects.get(id=company_id, role=User.Roles.COMPANY)
        except User.DoesNotExist:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        if action == 'approve':
            company.verified = True
            company.verification_status = 'approved'
        elif action == 'reject':
            company.verified = False
            company.verification_status = 'rejected'
        else:
            return Response({"detail": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        company.save()
        return Response({"detail": f"Company {action} successfully."}, status=status.HTTP_200_OK)


# ----------------------------
# Password Reset - Step 1: Request Link
# ----------------------------
class PasswordResetRequestView(APIView):
    """
    User requests a password reset link via email.
    
    """
    
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        Request Link to Confirm and Set New Password
        """
        return super().post(request, *args, **kwargs)
    
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        # Generate UID and token
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)

        # Build reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/"

        # Send email
        send_mail(
            subject="BuildLink - Password Reset",
            message=f"Hi {user.full_name},\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "Password reset link sent to email."}, status=status.HTTP_200_OK)


# ----------------------------
# Password Reset - Step 2: Confirm and Set New Password
# ----------------------------
class PasswordResetConfirmView(APIView):
    """
    User sets a new password using the token from their email.

    """
    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        Confirm and Set New Password
        """
        return super().post(request, *args, **kwargs)
    
    
    
    def post(self, request, uidb64, token):
        data = {
            'uidb64': uidb64,
            'token': token,
            'new_password': request.data.get('new_password')
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"detail": "Password reset successful."}, status=status.HTTP_200_OK)
