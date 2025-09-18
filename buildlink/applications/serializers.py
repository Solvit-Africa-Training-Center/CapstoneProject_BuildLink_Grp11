from rest_framework import serializers
from .models import Application
from projects.models import Job


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for workers/students applying to a job."""

    class Meta:
        model = Application
        fields = ['id', 'status']  # status is automatically 'pending' on creation
        read_only_fields = ['status']

    def validate(self, attrs):
        request = self.context['request']
        job = self.context['job']

        # Job must be open
        if job.status == Job.Status.CLOSED:
            raise serializers.ValidationError("You cannot apply to a closed job.")

        # Prevent duplicate applications
        if Application.objects.filter(job=job, applicant=request.user).exists():
            raise serializers.ValidationError("You have already applied for this job.")

        return attrs

    def create(self, validated_data):
        job = self.context['job']
        user = self.context['request'].user
        return Application.objects.create(job=job, applicant=user, **validated_data)


class MyApplicationListSerializer(serializers.ModelSerializer):
    """Serializer for listing applications of a worker/student."""
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_location = serializers.CharField(source='job.location', read_only=True)
    job_type = serializers.CharField(source='job.type', read_only=True)
    job_status = serializers.CharField(source='job.status', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_title', 'job_location', 'job_type', 'job_status',
            'status', 'created_at'
        ]


class ApplicantForOwnerSerializer(serializers.ModelSerializer):
    """Serializer for job owners to view applications to their jobs."""
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)
    applicant_email = serializers.EmailField(source='applicant.email', read_only=True)
    applicant_phone = serializers.CharField(source='applicant.phone', read_only=True)
    applicant_role = serializers.CharField(source='applicant.role', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'applicant_name', 'applicant_email', 'applicant_phone', 'applicant_role',
            'status', 'created_at'
        ]





class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'status', 'updated_at']

    def validate_status(self, value):
        valid_statuses = [s[0] for s in Application.Status.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
        return value


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer to return full details of an application.
    Includes related job and applicant information.
    """
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_title', 'applicant_name', 'status',
            'created_at', 'updated_at'
        ]
