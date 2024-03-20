from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from releasecab_api.tenant.models import Tenant
from releasecab_api.user.models import Role, Team, User

from ..models import (Release, ReleaseComment, ReleaseConfig, ReleaseStage,
                      ReleaseStageConnection, ReleaseStageConnectionApprover,
                      ReleaseType)


def create_access_token(user):
    token = AccessToken.for_user(user)
    return str(token)


class ReleaseViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            number_of_employees=50,
            invite_code="TEST123")
        self.admin_user = User.objects.create(
            email="admin@example.com",
            password="password123",
            tenant=self.tenant,
            is_staff=True,
            is_superuser=True,
            is_tenant_owner=True
        )
        self.normal_user = User.objects.create(
            email="user@example.com",
            password="password456",
            tenant=self.tenant,
            is_tenant_owner=True
        )
        self.release = Release.objects.create(
            name="Test Release",
            identifier="TEST-123",
            tenant=self.tenant,
            release_type=ReleaseType.objects.create(
                name="Test Type",
                tenant=self.tenant,
            ),
            created_at=datetime.now(),
            start_date=datetime.now(),
            end_date=datetime.now() +
            timedelta(
                hours=1),
            owner=self.admin_user,
            current_stage=ReleaseStage.objects.create(
                name="Test Stage",
                tenant=self.tenant,
            ))
        self.comment = ReleaseComment.objects.create(
            comment_body="Test Comment",
            tenant=self.tenant,
            writer=self.admin_user,
            release=self.release
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
            {create_access_token(self.admin_user)}')

    def test_admin_can_retrieve_release_comments_success(self):
        url = reverse('admin-release-comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_retrieve_release_comment_detail_success(self):
        url = reverse(
            'admin-release-comment-detail',
            kwargs={
                'pk': self.comment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['comment_body'],
            self.comment.comment_body)

    def test_user_can_create_release_comment_success(self):
        url = reverse('release-comment-create')
        payload = {
            "release": self.release.pk,
            "comment_body": "New Comment"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReleaseComment.objects.count(), 2)

    def test_only_admin_can_retrieve_release_comments_failure(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
                {create_access_token(self.normal_user)}')
        url = reverse('admin-release-comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_retrieve_non_existent_release_comment_failure(self):
        url = reverse('admin-release-comment-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_create_release_comment_failure(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='')
        url = reverse('release-comment-create')
        payload = {
            "release": self.release.pk,
            "comment_body": "New Comment"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ReleaseComment.objects.count(), 1)


class ReleaseConfigViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            number_of_employees=50,
            invite_code="TEST123")
        self.admin_user = User.objects.create(
            email="admin@example.com",
            password="password123",
            tenant=self.tenant,
            is_staff=True,
            is_superuser=True,
            is_tenant_owner=True
        )
        self.normal_user = User.objects.create(
            email="user@example.com",
            password="password456",
            tenant=self.tenant,
            is_tenant_owner=True
        )
        self.release_config = ReleaseConfig.objects.create(
            tenant=self.tenant,
            initial_stage=ReleaseStage.objects.create(
                name="Test Stage",
                tenant=self.tenant,
            )
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
            {create_access_token(self.admin_user)}')

    def test_admin_can_retrieve_release_configs_success(self):
        url = reverse('admin-release-config-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_can_retrieve_release_config_detail_success(self):
        url = reverse(
            'admin-release-config-detail',
            kwargs={'pk': self.release_config.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['initial_stage'],
            self.release_config.initial_stage.pk
        )

    def test_user_cannot_retrieve_release_configs_failure(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
                {create_access_token(self.normal_user)}')
        url = reverse('admin-release-config-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_retrieve_non_existent_release_config_failure(self):
        url = reverse('admin-release-config-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestStageConnectionViews(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            number_of_employees=50,
            invite_code="TEST123")
        self.admin_user = User.objects.create(
            email="admin@example.com",
            password="password123",
            tenant=self.tenant,
            is_staff=True,
            is_superuser=True,
            is_tenant_owner=True
        )
        self.normal_user = User.objects.create(
            email="user@example.com",
            password="password456",
            tenant=self.tenant,
            is_tenant_owner=True
        )
        self.planning_stage = ReleaseStage.objects.create(
            name='Planning in Progress',
            description='Planning in Progress',
            allow_release_delete=True,
            allow_release_update=True,
            tenant=self.tenant
        )
        self.in_progress_stage = ReleaseStage.objects.create(
            name='In Progress',
            description='In Progress',
            allow_release_delete=False,
            allow_release_update=False,
            tenant=self.tenant
        )
        self.connection = ReleaseStageConnection.objects.create(
            from_stage=self.planning_stage,
            to_stage=self.in_progress_stage,
            tenant=self.tenant,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
                {create_access_token(self.admin_user)}')

    def test_admin_can_retrieve_stage_connections_list(self):
        url = reverse('admin-release-stage-connections-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_admin_not_found_stage_connection_detail(self):
        url = reverse(
            'admin-release-stage-connections-detail',
            kwargs={
                'pk': '2'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_retrieve_stage_connections_by_tenant_id(self):
        url = reverse('release-stage-connection-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_retrieve_release_stage_connections(self):
        release_stage_id = self.in_progress_stage.pk
        url = reverse('release-stage-connection-get-to-stages',
                      kwargs={'release_stage_id': release_stage_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_update_stage_connection(self):
        new_to_stage = ReleaseStage.objects.create(
            name='New Stage',
            description='New Stage',
            allow_release_delete=False,
            allow_release_update=False,
            tenant=self.tenant
        )
        payload = {
            'to_stage': new_to_stage.pk
        }
        url = reverse('release-stage-connection-update',
                      kwargs={'pk': self.connection.pk})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['to_stage'], new_to_stage.pk)

    def test_admin_can_delete_stage_connection(self):
        url = reverse('release-stage-connection-delete',
                      kwargs={'pk': self.connection.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ReleaseStageConnection.objects.filter(
                pk=self.connection.pk).exists())

    def test_user_can_update_stage_connection(self):
        new_to_stage = ReleaseStage.objects.create(
            name='New Stage',
            description='New Stage',
            allow_release_delete=False,
            allow_release_update=False,
            tenant=self.tenant
        )
        payload = {
            'to_stage': new_to_stage.pk
        }
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
                {create_access_token(self.normal_user)}')
        url = reverse('release-stage-connection-update',
                      kwargs={'pk': self.connection.pk})
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_can_delete_stage_connection(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer \
                {create_access_token(self.normal_user)}')
        url = reverse('release-stage-connection-delete',
                      kwargs={'pk': self.connection.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_create_stage_connection(self):
        new_to_stage = ReleaseStage.objects.create(
            name='New Stage',
            description='New Stage',
            allow_release_delete=False,
            allow_release_update=False,
            tenant=self.tenant
        )
        payload = {
            'from_stage': self.planning_stage.pk,
            'to_stage': new_to_stage.pk,
            'tenant': self.tenant.pk,
            'owner_only': False
        }
        url = reverse('release-stage-connection-create')
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ReleaseStageConnection.objects.filter(
            from_stage=self.planning_stage,
            to_stage=new_to_stage
        ).exists())

    def test_admin_can_update_approvers(self):
        approver_role = Role.objects.create(
            name='Approver', tenant=self.tenant)
        approver_team = Team.objects.create(
            name='Approver Team', tenant=self.tenant)
        connection = ReleaseStageConnection.objects.create(
            from_stage=self.planning_stage,
            to_stage=self.in_progress_stage,
            tenant=self.tenant,
            owner_only=False
        )
        payload = {
            'approvers_list': [
                {
                    'roles': [approver_role.pk],
                    'teams': [approver_team.pk]
                }
            ]
        }
        url = reverse(
            'release-stage-connection-update',
            kwargs={
                'pk': connection.pk})
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ReleaseStageConnectionApprover.objects.filter(
            approver_role=approver_role,
            approver_team=approver_team
        ).exists())
