"""
Chatbot service layer.

Handles:
1. AI provider integration (OpenAI, Gemini, Anthropic) — server-side only
2. Rule-based FAQ fallback when no AI provider is configured
3. Emergency symptom detection
4. Conversation context management
"""

import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)

# ===========================================================
# EMERGENCY DETECTION
# ===========================================================
EMERGENCY_KEYWORDS = [
    r'\bsevere\s+chest\s+pain\b',
    r'\bchest\s+pain\b.*\bbad\b',
    r'\bcan[\'t\s]+breathe\b',
    r'\bdifficult(y)?\s+breath(ing)?\b.*\bsevere\b',
    r'\bfaint(ing)?\b.*\bnow\b',
    r'\bheart\s+attack\b',
    r'\bstroke\b',
    r'\bcollaps(e|ing)\b',
    r'\bunconscious\b',
    r'\bemergency\b',
]

EMERGENCY_RESPONSE = (
    "⚠️ **THIS SOUNDS LIKE A MEDICAL EMERGENCY.**\n\n"
    "Please **stop using this chatbot** and immediately:\n"
    "- 🚨 **Call emergency services NOW**: 911 (US), 999 (UK), 112 (EU), or your local emergency number.\n"
    "- Do NOT drive yourself to the hospital.\n"
    "- Stay calm and follow the dispatcher's instructions.\n\n"
    "*This chatbot cannot provide emergency medical assistance.*"
)


def is_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(pat, text_lower) for pat in EMERGENCY_KEYWORDS)


# ===========================================================
# FAQ FALLBACK
# ===========================================================
FAQ_RESPONSES = {
    r'upload|how.*(upload|add|submit)': (
        "To upload a heart sound recording:\n"
        "1. Go to **Analysis → Upload Heart Sound** in the navigation menu.\n"
        "2. Click 'Choose File' or drag and drop your audio file onto the upload area.\n"
        "3. Supported formats: WAV, FLAC, MP3, OGG, AIFF (max 50 MB).\n"
        "4. Click **Analyse** to start processing.\n"
        "You can also use **Record** to capture audio directly from your browser microphone."
    ),
    r'abnormal|normal.*abnormal|abnormal.*normal|difference.*classif': (
        "**Normal vs Abnormal Heart Sound Classification:**\n\n"
        "- **Normal**: The model's output suggests the heart sound has characteristics "
        "consistent with typical recordings in the training data.\n"
        "- **Abnormal**: The model detected patterns that differ from typical normal sounds. "
        "This could include murmurs, extra sounds (S3/S4), clicks, or other variations.\n\n"
        "⚠️ *This is a research screening tool, NOT a clinical diagnosis. "
        "An 'abnormal' result does not confirm heart disease. "
        "Please consult a qualified cardiologist for proper evaluation.*"
    ),
    r'report|download|pdf': (
        "To download your analysis report:\n"
        "1. Go to **Analysis History**.\n"
        "2. Click on any completed analysis.\n"
        "3. Select **Download PDF Report**.\n\n"
        "Reports include the analysis ID, date, model output, confidence information, "
        "waveform and spectrogram images, and the medical disclaimer."
    ),
    r'heart.*murmur|murmur': (
        "**Heart Murmurs:**\n\n"
        "A heart murmur is an extra or unusual sound heard during a heartbeat. "
        "They are caused by turbulent blood flow through the heart.\n\n"
        "- **Innocent murmurs**: Common in children and adults, usually harmless.\n"
        "- **Abnormal murmurs**: May indicate valve problems, septal defects, or other conditions.\n\n"
        "Only a cardiologist using a stethoscope (auscultation) and further investigations "
        "(echocardiogram, ECG) can properly diagnose the cause of a murmur."
    ),
    r'mfcc|feature|spectrogram|waveform|mel': (
        "**Audio Features Used by the Model:**\n\n"
        "- **MFCC** (Mel-Frequency Cepstral Coefficients): Captures the spectral shape of the sound, "
        "sensitive to tonal characteristics.\n"
        "- **Mel Spectrogram**: A visual representation of frequencies over time, weighted to human "
        "hearing perception.\n"
        "- **Waveform**: The raw amplitude of the audio signal over time.\n"
        "- **Spectral Contrast, Chroma, ZCR**: Additional texture and rhythm features.\n\n"
        "These features are combined into a vector that the trained classifier uses to predict "
        "whether the heart sound is 'normal' or 'abnormal'."
    ),
    r'confident|confidence|accuracy|reliable': (
        "**About Confidence Scores:**\n\n"
        "The confidence score shown with the prediction is the model's probability output — "
        "how certain the classifier is about its choice between 'normal' and 'abnormal'.\n\n"
        "⚠️ **Important**: This is NOT the same as the medical probability that you have or "
        "do not have heart disease. The model has been trained on a limited dataset and has "
        "not been clinically validated. Always seek professional medical evaluation."
    ),
    r'what.*app|this.*app|system.*do|purpose': (
        "**AI-Powered Heart Sound Disease Detection System**\n\n"
        "This application allows you to:\n"
        "✅ Upload or record heart sounds\n"
        "✅ Run AI-based screening classification (normal / abnormal)\n"
        "✅ View waveforms and spectrograms\n"
        "✅ Complete a heart health questionnaire\n"
        "✅ Download analysis reports\n"
        "✅ Chat with HeartCare AI for education and guidance\n\n"
        "🔬 *This is a research and educational tool — not a diagnostic medical device.*"
    ),
    r'chatbot|you|who are you|assistant': (
        "I am **HeartCare AI Assistant** — an educational chatbot for the Heart Sound Disease "
        "Detection System. I can answer questions about:\n"
        "- How to use the application\n"
        "- Heart sound terminology and education\n"
        "- Understanding your analysis results\n"
        "- General heart health information\n\n"
        "I am NOT a medical professional and cannot provide diagnoses or treatment advice. "
        "For medical concerns, please consult a qualified healthcare provider."
    ),
    r'delete|privacy|data|store': (
        "**Data Privacy:**\n\n"
        "- Your uploaded audio recordings are stored securely and are only accessible to you.\n"
        "- You can delete your recordings and analysis history from your profile settings.\n"
        "- We do not share your personal data or medical recordings with third parties.\n"
        "- See our full Privacy Policy for details."
    ),
}


def get_faq_response(message: str) -> str | None:
    """Return a matching FAQ answer or None if no match found."""
    lower = message.lower()
    for pattern, response in FAQ_RESPONSES.items():
        if re.search(pattern, lower):
            return response
    return None


FALLBACK_DEFAULT = (
    "I'm HeartCare AI Assistant (FAQ mode). I can help with questions about:\n"
    "- Uploading heart sound recordings\n"
    "- Understanding analysis results\n"
    "- Heart sound terminology\n"
    "- Downloading reports\n"
    "- Using this application\n\n"
    "Try asking: *\"How do I upload a heart sound?\"* or *\"What does abnormal mean?\"*\n\n"
    "*Note: I'm currently running in rule-based mode. Configure an AI provider for more "
    "natural conversations.*"
)


# ===========================================================
# AI PROVIDER INTEGRATIONS
# ===========================================================

def _call_openai(messages: list) -> str:
    """Call OpenAI Chat Completions API."""
    import urllib.request
    import json

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    payload = json.dumps({
        'model': settings.OPENAI_MODEL,
        'messages': messages,
        'max_tokens': 600,
        'temperature': 0.7,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['choices'][0]['message']['content'].strip()


def _call_gemini(messages: list) -> str:
    """Call Google Gemini API."""
    import urllib.request
    import json

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    # Convert OpenAI message format to Gemini contents
    contents = []
    for m in messages:
        if m['role'] == 'system':
            continue  # Gemini doesn't support system role in contents
        role = 'user' if m['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': m['content']}]})

    # Find system message for systemInstruction
    system_msg = next((m['content'] for m in messages if m['role'] == 'system'), None)

    body = {'contents': contents}
    if system_msg:
        body['systemInstruction'] = {'parts': [{'text': system_msg}]}

    model = settings.GEMINI_MODEL
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    payload = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=payload,
                                  headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['candidates'][0]['content']['parts'][0]['text'].strip()


def _call_anthropic(messages: list) -> str:
    """Call Anthropic Claude API."""
    import urllib.request
    import json

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    system_msg = next((m['content'] for m in messages if m['role'] == 'system'), '')
    conv_messages = [m for m in messages if m['role'] != 'system']

    payload = json.dumps({
        'model': settings.ANTHROPIC_MODEL,
        'max_tokens': 600,
        'system': system_msg,
        'messages': conv_messages,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return data['content'][0]['text'].strip()


# ===========================================================
# MAIN SERVICE FUNCTION
# ===========================================================

def get_chat_response(user_message: str, history: list) -> dict:
    """
    Generate a chatbot response.

    Args:
        user_message: The user's latest message.
        history: List of dicts [{'role': 'user'|'assistant', 'content': '...'}]

    Returns:
        {
            'response': str,
            'source': 'ai' | 'fallback' | 'error',
            'is_emergency': bool,
        }
    """
    # Emergency check always first
    if is_emergency(user_message):
        return {'response': EMERGENCY_RESPONSE, 'source': 'fallback', 'is_emergency': True}

    provider = getattr(settings, 'AI_PROVIDER', '').lower().strip()

    if provider:
        # Build message list for API call
        api_messages = [{'role': 'system', 'content': settings.CHATBOT_SYSTEM_PROMPT}]
        for h in history[-settings.CHATBOT_MAX_HISTORY:]:
            api_messages.append({'role': h['role'], 'content': h['content']})
        api_messages.append({'role': 'user', 'content': user_message})

        try:
            if provider == 'openai':
                response_text = _call_openai(api_messages)
            elif provider == 'gemini':
                response_text = _call_gemini(api_messages)
            elif provider == 'anthropic':
                response_text = _call_anthropic(api_messages)
            else:
                raise ValueError(f"Unknown AI provider: {provider}")

            return {'response': response_text, 'source': 'ai', 'is_emergency': False}

        except Exception as exc:
            logger.warning(f"AI provider '{provider}' failed: {exc}. Using fallback.")

    # Rule-based fallback
    faq_resp = get_faq_response(user_message)
    if faq_resp:
        return {'response': faq_resp, 'source': 'fallback', 'is_emergency': False}

    return {'response': FALLBACK_DEFAULT, 'source': 'fallback', 'is_emergency': False}
