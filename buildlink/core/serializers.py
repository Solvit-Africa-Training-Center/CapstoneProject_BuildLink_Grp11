from rest_framework import serializers
from .models import User, NationalID, Trade, WorkerTrade


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    national_id = serializers.CharField(write_only=True, required=False)
    trade = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone','password', 'role', 'national_id', 'trade']
        extra_kwargs = {
            'phone': {'required': True},
        }

    def validate(self, attrs):
        role = attrs.get('role')
        if role == 'worker':
            if not attrs.get('national_id'):
                raise serializers.ValidationError("Workers must provide a National ID.")
            if not attrs.get('trade'):
                raise serializers.ValidationError("Workers must select a trade.")
        return attrs

    def create(self, validated_data):
        national_id_value = validated_data.pop('national_id', None)
        trade_name = validated_data.pop('trade', None)

        # Worker: check National ID exists
        national_id_obj = None
        if validated_data['role'] == 'worker':
            try:
                national_id_obj = NationalID.objects.get(id_number=national_id_value)
            except NationalID.DoesNotExist:
                raise serializers.ValidationError({"national_id": "This ID is not registered in the system."})

        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            role=validated_data['role'],
            national_id=national_id_obj  # Link NationalID if worker
        )

        # Worker: assign trade
        if user.role == 'worker':
            trade, created = Trade.objects.get_or_create(name=trade_name)
            WorkerTrade.objects.create(user=user, trade=trade)

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone','role']