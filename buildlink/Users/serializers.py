from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from Users.models import User, NationalID

# If Trades app is separate
try:
    from trades.models import Trade, WorkerTrade
except Exception:
    from Users.models import Trade, WorkerTrade
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    national_id = serializers.CharField(write_only=True, required=False)
    trade = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'gender', 'password', 'confirm_password',
            'role', 'national_id', 'trade',
            'company_name', 'company_license', 'registration_number'
        ]

    def validate(self, attrs):
        role = attrs.get('role')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        # Role-specific validation
        if role == User.Roles.WORKER:
            if not attrs.get('national_id'):
                raise ValidationError("Workers must provide a National ID.")
            if not attrs.get('trade'):
                raise ValidationError("Workers must select a trade.")

        elif role == User.Roles.COMPANY:
            if not attrs.get('company_name'):
                raise ValidationError("Company name is required for company accounts.")
            if not attrs.get('company_license'):
                raise ValidationError("Business license is required for company accounts.")
            if not attrs.get('registration_number'):
                raise ValidationError("Registration number is required for company accounts.")

        return attrs

    def create(self, validated_data):
        national_id_value = validated_data.pop('national_id', None)
        trade_name = validated_data.pop('trade', None)
        validated_data.pop('confirm_password', None)

        # Worker: Verify National ID
        national_id_obj = None
        if validated_data.get('role') == User.Roles.WORKER:
            try:
                national_id_obj = NationalID.objects.get(id_number=national_id_value)
            except NationalID.DoesNotExist:
                raise ValidationError({"national_id": "This ID is not registered in the system."})

        # Create the user using the custom manager
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone=validated_data['phone'],
            gender=validated_data.get('gender'),
            role=validated_data['role'],
            password=validated_data['password'],
            national_id=national_id_obj,
            company_name=validated_data.get('company_name'),
            company_license=validated_data.get('company_license'),
            registration_number=validated_data.get('registration_number')
        )

        # Worker: Assign trade
        if user.role == User.Roles.WORKER and trade_name:
            trade, _ = Trade.objects.get_or_create(name=trade_name.strip())
            WorkerTrade.objects.create(user=user, trade=trade)

        # Company: Default status pending
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
            'id', 'full_name', 'email', 'phone', 'gender',
            'role', 'verified', 'verification_status'
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
