# projects/serializers.py
from rest_framework import serializers
from .models import Job
from trades.models import Trade
from Users.models import User


class JobListSerializer(serializers.ModelSerializer):
    trade = serializers.CharField(source='trade.name', read_only=True)
    posted_by = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'location', 'type', 'trade', 'budget',
            'status', 'posted_by', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'posted_by', 'created_at']

    def get_posted_by(self, obj):
        return {
            "id": obj.posted_by.id,
            "full_name": obj.posted_by.full_name,
            "role": obj.posted_by.role,
            "email": obj.posted_by.email
        }


class JobDetailSerializer(serializers.ModelSerializer):
    trade = serializers.CharField(source='trade.name', read_only=True)
    posted_by = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'location', 'type',
            'trade', 'budget', 'status', 'posted_by', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'posted_by', 'created_at']

    def get_posted_by(self, obj):
        return {
            "id": obj.posted_by.id,
            "full_name": obj.posted_by.full_name,
            "role": obj.posted_by.role,
            "email": obj.posted_by.email
        }


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    trade_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'location',
            'type', 'trade_id', 'budget'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        title = attrs.get('title')
        if title and len(title) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")

        budget = attrs.get('budget')
        if budget is not None and budget <= 0:
            raise serializers.ValidationError("Budget must be a positive number.")

        job_type = attrs.get('type')
        if job_type not in dict(Job.JobType.choices):
            raise serializers.ValidationError(f"Invalid job type. Allowed types: {list(dict(Job.JobType.choices).keys())}")

        return attrs

    def create(self, validated_data):
        trade_id = validated_data.pop('trade_id', None)
        request = self.context['request']
        user = request.user

        job = Job.objects.create(posted_by=user, **validated_data)

        if trade_id:
            try:
                job.trade = Trade.objects.get(pk=trade_id)
                job.save()
            except Trade.DoesNotExist:
                raise serializers.ValidationError({"trade_id": "Trade not found."})

        return job

    def update(self, instance, validated_data):
        trade_id = validated_data.pop('trade_id', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if trade_id is not None:
            try:
                instance.trade = Trade.objects.get(pk=trade_id)
            except Trade.DoesNotExist:
                raise serializers.ValidationError({"trade_id": "Trade not found."})

        instance.save()
        return instance
