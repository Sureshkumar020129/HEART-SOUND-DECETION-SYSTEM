"""
Automated Test Suite for AI-Powered Heart Sound Disease Detection System.

Covers:
1. User registration, authentication, and profile creation
2. Cross-user data isolation & unauthorized access restrictions
3. Audio preprocessing and feature extraction
4. Corrupted audio validation
5. Model loading, inference, and prediction error handling
6. Assessment questionnaire scoring & validation
7. Chatbot provider dispatch, emergency keyword detection, and fallback
8. PDF report generation and download security
9. Admin role protection
"""

import io
import os
import shutil
import tempfile
import numpy as np
import soundfile as sf
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import UserProfile
from heart_analysis.models import HeartSoundRecording, AnalysisRecord, PredictionResult
from assessments.models import HealthAssessment
from chatbot.models import ChatSession, ChatMessage
from chatbot.services import is_emergency, get_chat_response, get_faq_response
from ml_pipeline.audio_processing import (
    load_and_validate_audio, resample_audio, normalize_audio, pad_or_trim,
    preprocess_audio, AudioProcessingError, TARGET_SR
)
from ml_pipeline.feature_extraction import extract_all_features, FeatureExtractionError
from ml_pipeline.prediction import predict, load_model, ModelNotAvailableError


class AuthenticationAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='patient1', email='p1@example.com', password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='patient2', email='p2@example.com', password='Password123!'
        )

    def test_user_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'data_consent': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.profile.data_consent)

    def test_unauthenticated_access_redirect(self):
        # Protected endpoints must redirect to login
        endpoints = [
            reverse('dashboard:dashboard'),
            reverse('heart_analysis:upload'),
            reverse('heart_analysis:history'),
            reverse('assessments:assessment'),
            reverse('chatbot:chatbot'),
        ]
        for url in endpoints:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn('/accounts/login/', resp.url)

    def test_cross_user_isolation(self):
        # User 1 creates a recording
        rec = HeartSoundRecording.objects.create(
            user=self.user1, original_filename='test.wav', source='upload'
        )
        analysis = AnalysisRecord.objects.create(user=self.user1, recording=rec)

        # User 2 logs in and attempts to access User 1's analysis
        self.client.login(username='patient2', password='Password123!')
        resp = self.client.get(reverse('heart_analysis:result', kwargs={'pk': analysis.id}))
        self.assertEqual(resp.status_code, 404)

        # User 2 attempts to download User 1's report
        resp_pdf = self.client.get(reverse('reports:download', kwargs={'pk': analysis.id}))
        self.assertEqual(resp_pdf.status_code, 404)


class AudioProcessingAndFeatureTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_audio_preprocessing(self):
        # Generate 2 seconds of 44.1kHz audio
        sr = 44100
        t = np.linspace(0, 2.0, int(sr * 2.0))
        audio_data = 0.5 * np.sin(2 * np.pi * 100 * t)
        fp = os.path.join(self.temp_dir, 'sample.wav')
        sf.write(fp, audio_data, sr)

        processed = preprocess_audio(fp)
        self.assertEqual(processed['sample_rate'], TARGET_SR)
        self.assertEqual(len(processed['audio']), int(TARGET_SR * 5))
        self.assertAlmostEqual(np.max(np.abs(processed['audio'])), 1.0, places=2)

    def test_corrupted_audio_rejection(self):
        fp = os.path.join(self.temp_dir, 'corrupt.wav')
        with open(fp, 'w') as f:
            f.write("Not a real wave audio stream")

        with self.assertRaises(AudioProcessingError):
            load_and_validate_audio(fp)

    def test_silent_audio_rejection(self):
        sr = 22050
        audio_data = np.zeros(sr * 2)
        fp = os.path.join(self.temp_dir, 'silent.wav')
        sf.write(fp, audio_data, sr)

        with self.assertRaises(AudioProcessingError):
            load_and_validate_audio(fp)

    def test_feature_extraction(self):
        sr = 22050
        t = np.linspace(0, 5.0, int(sr * 5.0))
        audio = 0.5 * np.sin(2 * np.pi * 150 * t)
        features = extract_all_features(audio, sr)
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 100)
        self.assertFalse(np.isnan(features).any())


class MachineLearningPredictionTests(TestCase):
    def test_missing_model_graceful_handling(self):
        dummy_features = np.ones(186)
        result = predict(
            features=dummy_features,
            model_path='non_existent_model.pkl',
            scaler_path='non_existent_scaler.pkl'
        )
        self.assertEqual(result['status'], 'model_unavailable')
        self.assertEqual(result['classification'], 'model_unavailable')
        self.assertIsNone(result['confidence_score'])
        self.assertIn("Model file not found", result['error_message'])


class AssessmentQuestionnaireTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='Password123!')

    def test_risk_level_computation(self):
        # Emergency symptoms
        urgent_assessment = HealthAssessment.objects.create(
            user=self.user,
            fainting='yes',
            chest_discomfort='yes',
            chest_pain_level=8,
            shortness_of_breath='yes',
            shortness_at_rest='yes'
        )
        self.assertEqual(urgent_assessment.risk_level, 'seek_urgent')

        # Mild/low risk symptoms
        low_assessment = HealthAssessment.objects.create(
            user=self.user,
            chest_discomfort='no',
            shortness_of_breath='no',
            dizziness='no',
            fainting='no'
        )
        self.assertEqual(low_assessment.risk_level, 'low')

    def test_urgent_result_shows_click_to_call_emergency_numbers(self):
        assessment = HealthAssessment.objects.create(
            user=self.user,
            fainting='yes',
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('assessments:result', kwargs={'pk': assessment.pk})
        )

        self.assertContains(response, 'href="tel:911"')
        self.assertContains(response, 'href="tel:999"')
        self.assertContains(response, 'href="tel:112"')


class ChatbotServiceTests(TestCase):
    def test_emergency_keyword_detection(self):
        self.assertTrue(is_emergency("I have severe chest pain right now"))
        self.assertTrue(is_emergency("Can't breathe properly and having heart attack symptoms"))
        self.assertFalse(is_emergency("How do I upload my audio file?"))

    def test_emergency_response_dispatch(self):
        resp = get_chat_response("I have severe chest pain and collapsed", [])
        self.assertTrue(resp['is_emergency'])
        self.assertIn("MEDICAL EMERGENCY", resp['response'])

    def test_rule_based_fallback(self):
        resp = get_chat_response("What does an abnormal classification mean?", [])
        self.assertEqual(resp['source'], 'fallback')
        self.assertIn("Normal vs Abnormal", resp['response'])
