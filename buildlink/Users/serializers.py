from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# If you split apps, prefer this:
try:
    from trades.models import Trade, WorkerTrade
except Exception:
    # fallback if Trade/WorkerTrade are still inside Users app
    from Users.models import Trade, WorkerTrade

from Users.models import User, NationalID


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    national_id = serializers.CharField(write_only=True, required=False)
    trade = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'password', 'role', 'national_id', 'trade']

    # --- Field-level validation ---
    def validate_phone(self, value):
        v = (value or '').strip()
        if not v:
            raise ValidationError("Phone is required.")
        # Optional: keep it simple (digits only)
        if not v.replace('+', '').isdigit():
            raise ValidationError("Phone must contain only digits (and optional leading +).")
        return v

    def validate(self, attrs):
        role = attrs.get('role')
        if role == 'worker':
            if not attrs.get('national_id'):
                raise ValidationError("Workers must provide a National ID.")
            if not attrs.get('trade'):
                raise ValidationError("Workers must select a trade.")
        return attrs

    def create(self, validated_data):
        national_id_value = validated_data.pop('national_id', None)
        trade_name = validated_data.pop('trade', None)

        # Worker: verify National ID exists
        national_id_obj = None
        if validated_data.get('role') == 'worker':
            try:
                national_id_obj = NationalID.objects.get(id_number=national_id_value)
            except NationalID.DoesNotExist:
                raise ValidationError({"national_id": "This ID is not registered in the system."})

        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            phone=validated_data['phone'],
            password=validated_data['password'],
            role=validated_data['role'],
            national_id=national_id_obj
        )

        # Worker: assign trade
        if user.role == 'worker' and trade_name:
            trade, _ = Trade.objects.get_or_create(name=trade_name.strip())
            WorkerTrade.objects.create(user=user, trade=trade)

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role']


class WorkerProfileSerializer(serializers.ModelSerializer):
    """
    Read/write worker profile.
    - Read: returns trades as a list of trade names.
    - Update: accepts 'trades' as a list of trade names and syncs them.
    """
    trades = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'trades']
        read_only_fields = ['role']  # role isn’t editable via this endpoint

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Attach trades for workers
        qs = WorkerTrade.objects.filter(user=instance).select_related('trade')
        data['trades'] = [wt.trade.name for wt in qs]
        return data

    def update(self, instance, validated_data):
        # Basic updatable fields
        for field in ['username', 'email', 'phone']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        # Sync trades only for workers
        trades_in = validated_data.get('trades', None)
        if trades_in is not None:
            if instance.role != 'worker':
                raise ValidationError({"trades": "Only workers can have trades."})
            # Normalize and de-duplicate
            names = list({t.strip() for t in trades_in if t and t.strip()})
            # Build/ensure trades
            new_trades = []
            for name in names:
                trade, _ = Trade.objects.get_or_create(name=name)
                new_trades.append(trade.id)

            # Current links
            current_ids = set(
                WorkerTrade.objects.filter(user=instance).values_list('trade_id', flat=True)
            )
            desired_ids = set(new_trades)

            # Remove old
            if current_ids - desired_ids:
                WorkerTrade.objects.filter(user=instance, trade_id__in=current_ids - desired_ids).delete()
            # Add new
            to_add = desired_ids - current_ids
            WorkerTrade.objects.bulk_create(
                [WorkerTrade(user=instance, trade_id=tid) for tid in to_add]
            )

        return instance
