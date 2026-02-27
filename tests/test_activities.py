"""
Tests for the Mergington High School Activities API
Uses AAA (Arrange-Act-Assert) pattern for clarity
"""
import pytest
from urllib.parse import quote
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client: TestClient):
        """Should return a list of all available activities"""
        # Arrange
        expected_activity_count = 9

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == expected_activity_count

    def test_get_activities_has_correct_structure(self, client: TestClient):
        """Should return activities with required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_includes_chess_club(self, client: TestClient):
        """Should include Chess Club with correct data"""
        # Arrange
        expected_name = "Chess Club"

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert expected_name in activities
        assert activities[expected_name]["description"] == "Learn strategies and compete in chess tournaments"
        assert len(activities[expected_name]["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client: TestClient):
        """Should successfully sign up a new student for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_for_nonexistent_activity(self, client: TestClient):
        """Should return 404 when signing up for non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_participant(self, client: TestClient):
        """Should return 400 when student attempts to sign up twice"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_with_special_characters_in_email(self, client: TestClient):
        """Should handle emails with special characters"""
        # Arrange
        activity_name = "Programming Class"
        email = "student+tag@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={quote(email)}"
        )

        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_to_full_activity(self, client: TestClient):
        """Should still allow signup even if activity is at max capacity"""
        # Arrange
        activity_name = "Basketball Team"
        email = "newplayer@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client: TestClient):
        """Should successfully remove a participant from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant exists before removal
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_remove_participant_from_nonexistent_activity(self, client: TestClient):
        """Should return 404 when removing from non-existent activity"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonexistent_participant(self, client: TestClient):
        """Should return 404 when trying to remove participant not in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_participant_then_signup_again(self, client: TestClient):
        """Should allow a participant to sign up again after being removed"""
        # Arrange
        activity_name = "Drama Club"
        email = "lucas@mergington.edu"

        # Act - Remove participant
        response_delete = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )

        # Assert removal was successful
        assert response_delete.status_code == 200

        # Act - Sign up again
        response_signup = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert signup was successful
        assert response_signup.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_remove_with_special_characters_in_email(self, client: TestClient):
        """Should handle removing participants with special characters in email"""
        # Arrange
        activity_name = "Programming Class"
        email = "special+email@mergington.edu"
        
        # First add the participant
        client.post(f"/activities/{activity_name}/signup?email={quote(email)}")

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{quote(email)}"
        )

        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
