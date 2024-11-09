# Scribey
A Python-based GUI application for transcribing audio and video files using OpenAI's Whisper model. Supports batch processing, YouTube videos, and optional speaker diarization.

# Features

🎯 Transcribe audio and video files with OpenAI's Whisper
📺 Support for YouTube video transcription
👥 Optional speaker diarization (requires HuggingFace token)
📦 Batch processing capability
⌛ Timestamp inclusion options
🎭 Multiple model sizes (tiny to large)
🖱️ Drag-and-drop interface
💾 Flexible output naming options

# Installation
Clone this repository:

clone https://github.com/maantren/scribey.git
cd transcription-tool

Install required Python packages:

pip install openai-whisper yt-dlp tkinterdnd2 ffmpeg-python requests torch pyannote.audio

For speaker diarization support (optional):

pip install pyannote.audio torch

Install FFmpeg:

Windows: Install using Chocolatey:
choco install ffmpeg
Or download manually from FFmpeg's official site
macOS: Install using Homebrew:
brew install ffmpeg

Linux:
sudo apt-get update && sudo apt-get install ffmpeg

# Usage

Run the application:
python scribey.py

Basic Transcription:

Click "Add Files" or drag and drop audio/video files
Select output directory
Choose model size and options
Click "Start Transcription"

YouTube Videos:

Switch to "YouTube URL" mode
Enter YouTube URL
Select output options
Click "Start Transcription"

Speaker Diarization:

Enable "Speaker Diarization" checkbox
Add HuggingFace token in Settings tab
Process files as normal

Model Sizes

tiny: Fastest, lowest accuracy
base: Good balance of speed and accuracy
small: Better accuracy, slower
medium: High accuracy, slower
large: Best accuracy, slowest

File Output Options

Automatic: Uses input filename + "_transcript"
Custom prefix: User-defined prefix for output files
Timestamps can be included in output
Speaker labels included when diarization enabled

# Speaker Diarization Setup

Speaker diarization requires additional setup:

Create a HuggingFace account at https://huggingface.co/join
Go to https://huggingface.co/settings/tokens
Create a new Access Token with 'read' role
Accept the user conditions for both models:

Visit https://huggingface.co/pyannote/speaker-diarization
Visit https://huggingface.co/pyannote/segmentation


Add your token in the app's Settings tabg

# Supported File Formats

Audio: mp3, wav, m4a
Video: mp4, avi, mov, mkv, webm
YouTube URLs

# Common Issues & Solutions

FFmpeg not found:

Ensure FFmpeg is installed and in system PATH
Restart application after installation

Diarization not working:

Verify HuggingFace token is valid
Ensure you've accepted terms for both models
Check internet connection
Try alternative diarization method if primary fails

YouTube download fails:

Check internet connection
Verify URL is valid and video is accessible
Update yt-dlp: pip install -U yt-dlp

### Speaker Diarization Issues on Windows

If you encounter permission errors with speaker diarization:

1. First method: Run the application as administrator
2. Second method: Disable and re-enable speaker diarization
3. If both fail, you can:
   - Continue without speaker diarization
   - Try processing smaller audio files
   - Use the basic transcription and add speaker labels manually

Note: The diarization feature works best with:
- Clear audio quality
- Limited background noise
- Distinct speaker voices
- Audio files under 30 minutes

# Dependencies

Required packages:

Python 3.8+
openai-whisper
yt-dlp
tkinterdnd2
ffmpeg-python
requests
torch
pyannote.audio

System requirements:

FFmpeg installed and in PATH
Internet connection for YouTube and diarization
Sufficient disk space for temporary files

Development
The application structure:
scribey.py
├── TranscriptionGUI (Main GUI class)
├── TranscriptionWorker (Background processing)
├── DependencyManager (Package management)
└── Settings (User preferences)

# Contributing

Fork the repository
Create feature branch
Commit changes
Push to branch
Open Pull Request

# License
GPL

# Acknowledgments

OpenAI's Whisper for transcription
pyannote.audio for diarization
yt-dlp for YouTube support
HuggingFace for model hosting

# Maintainers
Maantren - Initial work - github.com/maantren
Version History

1.1.0

Enhanced speaker diarization handling
Added alternative diarization method
Improved error handling and user feedback
Custom output naming options

1.0.0

Initial Release
Basic transcription functionality
YouTube support
Speaker diarization


