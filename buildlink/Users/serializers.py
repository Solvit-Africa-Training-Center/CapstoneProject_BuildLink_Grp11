from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from Users.models import User, NationalID, Portfolio

# If Trades app is separate
try:
    from trades.models import Trade, WorkerTrade
except Exception:
    from Users.models import Trade, WorkerTrade
class RegisterSerializer(serializers.ModelSerializer):
    """
    Phase 1 - Minimal registration: role, full_name, email, phone, password, confirm_password.
    Additional profile details are completed after login.
    """
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'role', 'full_name', 'email', 'phone', 'password', 'confirm_password'
        ]

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
            role=validated_data['role'],
            password=validated_data['password']
        )
        # Companies start as pending verification
        if user.role == User.Roles.COMPANY:
            user.verification_status = 'pending'
            user.save()
        return user



# ----------------------------
# User Serializer (General)
# ----------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 'location',
            'role', 'verified', 'verification_status',
            'company_name', 'company_license', 'registration_number'
        ]


# ----------------------------
# Worker Profile Serializer
# ----------------------------
class WorkerProfileSerializer(serializers.ModelSerializer):
    """
    Used by workers to view or update their profile.
    Includes trades and verified National ID.
    """
    trades = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    national_id_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender',
            'role', 'verified', 'trades', 'national_id_number'
        ]
        read_only_fields = ['role', 'verified']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        qs = WorkerTrade.objects.filter(user=instance).select_related('trade')
        data['trades'] = [wt.trade.name for wt in qs]
        data['national_id'] = instance.national_id.id_number if instance.national_id else None
        return data

    def update(self, instance, validated_data):
        # Update basic fields
        for field in ['full_name', 'email', 'phone', 'gender']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # National ID verification
        if 'national_id_number' in validated_data:
            id_number = validated_data['national_id_number']
            try:
                national_id_obj = NationalID.objects.get(id_number=id_number)
                instance.national_id = national_id_obj
                instance.verified = True
            except NationalID.DoesNotExist:
                raise ValidationError({"national_id": "Invalid National ID provided."})

        instance.save()

        # Update trades
        trades_in = validated_data.get('trades', None)
        if trades_in is not None:
            if instance.role != User.Roles.WORKER:
                raise ValidationError({"trades": "Only workers can have trades."})

            # Normalize trade names
            names = list({t.strip() for t in trades_in if t and t.strip()})
            new_trades = [Trade.objects.get_or_create(name=name)[0] for name in names]

            # Remove old trades
            WorkerTrade.objects.filter(user=instance).exclude(trade__in=new_trades).delete()

            # Add new trades
            for trade in new_trades:
                WorkerTrade.objects.get_or_create(user=instance, trade=trade)

        return instance


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 'location', 'role'
        ]
        read_only_fields = ['role', 'email']

    def update(self, instance, validated_data):
        for field in ['full_name', 'phone', 'gender', 'location']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class OwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 'location', 'role'
        ]
        read_only_fields = ['role', 'email']

    def update(self, instance, validated_data):
        for field in ['full_name', 'phone', 'gender', 'location']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class CompanyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'location', 'role',
            'company_name', 'company_license', 'registration_number',
            'verification_status', 'verified'
        ]
        read_only_fields = ['role', 'email', 'verification_status', 'verified']

    def update(self, instance, validated_data):
        for field in ['full_name', 'phone', 'location', 'company_name', 'company_license', 'registration_number']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance

# ----------------------------
# Phase 2 - Profile Completion
# ----------------------------
class ProfileCompletionSerializer(serializers.ModelSerializer):
    """
    Allows updating additional fields post-registration.
    - national_id_number links to NationalID record and can set verified
    - portfolio_images allows adding Portfolio entries
    - id_verification_status maps to verification_status
    """
    national_id_number = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    portfolio_images = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False
    )
    id_verification_status = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'full_name', 'phone', 'gender', 'location',
            'company_name', 'company_license', 'registration_number',
            'national_id_number', 'portfolio_images', 'id_verification_status'
        ]

    def validate_id_verification_status(self, value):
        allowed = ['pending', 'approved', 'rejected']
        if value not in allowed:
            raise serializers.ValidationError(f"Invalid id_verification_status. Must be one of: {allowed}")
        return value

    def update(self, instance, validated_data):
        national_id_number = validated_data.pop('national_id_number', None)
        portfolio_images = validated_data.pop('portfolio_images', [])
        id_verification_status = validated_data.pop('id_verification_status', None)

        # Update basic fields
        for field, value in validated_data.items():
            setattr(instance, field, value)

        # National ID linking (workers primarily, but allow opt-in)
        if national_id_number:
            try:
                nid = NationalID.objects.get(id_number=national_id_number)
                instance.national_id = nid
                # Do not auto-verify unless business rules say so; keep pending unless pre-approved
                if instance.role == User.Roles.WORKER and instance.verification_status == 'pending':
                    instance.verified = True
            except NationalID.DoesNotExist:
                raise serializers.ValidationError({"national_id_number": "Not found in registry."})

        # Explicit verification status update (admin workflows may also exist elsewhere)
        if id_verification_status is not None:
            instance.verification_status = id_verification_status

        instance.save()

        # Portfolio additions
        for image_url in portfolio_images:
            if image_url:
                Portfolio.objects.create(user=instance, image_url=image_url)

        return instance


# ----------------------------
# Password Reset
# ----------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, attrs):
        try:
            # Decode user ID
            uid = smart_str(urlsafe_base64_decode(attrs['uidb64']))
            user = User.objects.get(id=uid)

            # Validate token
            if not PasswordResetTokenGenerator().check_token(user, attrs['token']):
                raise serializers.ValidationError("Invalid or expired reset token.")

            attrs['user'] = user
            return attrs

        except (User.DoesNotExist, DjangoUnicodeDecodeError):
            raise serializers.ValidationError("Invalid reset link or user not found.")
