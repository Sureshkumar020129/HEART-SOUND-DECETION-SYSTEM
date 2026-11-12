# HeartSound AI — User Manual & Operating Guide

---

## 1. Quick Navigation Guide

| Module | Navigation Link | Description |
|---|---|---|
| **Home** | `/` | Project overview, key features, and disclaimer |
| **Dashboard** | `/dashboard/` | Real-time analysis metrics, charts, and quick actions |
| **Upload / Record** | `/analysis/upload/` | Submit audio files or capture via browser microphone |
| **Analysis History** | `/analysis/history/` | View past analysis records and delete audio |
| **Health Assessment** | `/assessment/` | Complete 14-question cardiac symptom evaluation |
| **HeartCare AI Chat** | `/chatbot/` | Conversational medical guidance and FAQ support |
| **User Profile** | `/accounts/profile/` | Edit personal details and manage data consent |
| **Admin Console** | `/admin/` | Staff audit log and user management console |

---

## 2. Step-by-Step Instructions

### Step 1: User Account Registration & Login
1. Click **Register** on the top navigation bar.
2. Enter your name, username, email, and choose a password (minimum 8 characters).
3. Read and check the **Informed Consent** checkbox acknowledging that the system is for research screening.
4. Click **Create Account** to be redirected automatically to your personal dashboard.

### Step 2: Uploading or Recording Audio
1. From the navigation menu or dashboard, click **Upload / Record**.
2. **To Upload a File:** Drag and drop a `.wav`, `.flac`, `.mp3`, or `.ogg` recording onto the upload zone, or click to browse your computer.
3. **To Record in Browser:** Click the **Record Audio** tab. Grant browser microphone permission when prompted, press **Record**, capture 5–10 seconds of clear heart sound, and press **Stop**.
4. Click **Analyse Recording**.

### Step 3: Reviewing Analysis Results
1. The system displays:
   - **Classification:** `NORMAL`, `ABNORMAL`, or `UNCERTAIN`
   - **Model Confidence Score:** (e.g. 94.2%)
   - **Class Probabilities:** Distribution between healthy baseline and murmur features
   - **Waveform Plot:** Amplitude oscillations over time
   - **Mel-Spectrogram:** Visual distribution of sound frequencies
2. Review the statutory medical disclaimer and guidance notes.

### Step 4: Generating & Downloading PDF Reports
1. On the results page or from the **Analysis History** table, click **Download PDF Report**.
2. A formatted, print-ready medical screening document with your analysis ID, duration, sample rate, and risk summary will download to your device.

### Step 5: Completing a Symptom Assessment
1. Click **Assessment** in the navigation menu.
2. Complete questions concerning chest discomfort, shortness of breath, dizziness, palpitations, and risk factors.
3. Submit to receive an evaluated risk tier (`Low`, `Moderate`, `High`, or `Seek Urgent Care`).

### Step 6: Interacting with HeartCare AI Assistant
1. Access the chatbot via the navigation link, the dashboard shortcut, or the floating cyan robot icon at the bottom-right corner.
2. Ask questions about phonocardiograms, how to interpret your report, or cardiovascular terminology.
3. Select any quick-prompt chip for instant answers.
4. If an emergency phrase is typed (e.g. "I have chest pain and can't breathe"), the assistant displays red high-priority emergency instructions immediately.

---

## 3. Administrator Operations

1. Sign in with staff credentials at `/admin/` or via username `admin` and password `Admin12345!`.
2. Inspect:
   - **Audit Logs:** Track user logins, file uploads, analysis executions, and deletions.
   - **Heart Sound Recordings:** Review file sizes, formats, and processing statuses.
   - **Model Metadata:** Monitor active model versions, sensitivity, and specificity.
   - **Site Configuration:** Toggle maintenance mode, registration permissions, or update the medical disclaimer.
