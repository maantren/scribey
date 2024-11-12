# Scribey - Advanced Audio Transcription Tool

A powerful, user-friendly GUI application for transcribing audio and video files using OpenAI's Whisper model, with support for speaker diarization, batch processing, and YouTube video transcription.

## Features

- 🎯 **Smart Transcription**: Uses OpenAI's Whisper model for accurate speech-to-text conversion
- 👥 **Speaker Detection**: Identifies different speakers in the audio
- 📺 **YouTube Support**: Direct transcription from YouTube URLs
- 📦 **Batch Processing**: Handle multiple files efficiently
- 🖱️ **User-Friendly**: Simple drag-and-drop interface
- ⚡ **Smart Processing**: Handles large files through intelligent chunking
- 🎛️ **Multiple Models**: Choose from different Whisper models based on your needs

## Complete Installation Guide

### 1. Install Python

1. Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
2. During installation:
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"
   - ✅ Check "Install for all users" (recommended)

3. Verify installation by opening Command Prompt and typing:
   ```bash
   python --version
   pip --version
   ```

### 2. Install FFmpeg

#### Windows:
Option 1 - Using Chocolatey (Recommended):
1. Install [Chocolatey](https://chocolatey.org/install)
2. Open Command Prompt as Administrator and run:
   ```bash
   choco install ffmpeg
   ```

Option 2 - Manual Installation:
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., C:\ffmpeg)
3. Add to PATH:
   - Search "Environment Variables" in Windows search
   - Edit System Variables
   - Add FFmpeg's bin folder to Path (e.g., C:\ffmpeg\bin)

#### macOS:
```bash
brew install ffmpeg
```

#### Linux:
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Install Required Python Packages

1. Download or clone this repository:
   ```bash
   git clone https://github.com/yourusername/scribey.git
   cd scribey
   ```

2. Install required packages:
   ```bash
   pip install openai-whisper
   pip install yt-dlp
   pip install tkinterdnd2
   pip install ffmpeg-python
   pip install torch
   pip install pyannote.audio
   pip install pydub
   ```

### 4. Set Up Speaker Diarization (Optional)

1. Create a HuggingFace account at [huggingface.co](https://huggingface.co/join)
2. Get your access token:
   - Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Create new token with 'read' access (specifically, 'Read access to contents of all public gated repos you can access' under 'Repositories' - this makes sure that you can use Pyannote, below)
3. Accept the model terms:
   - Visit [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
   - Visit [pyannote/segmentation](https://huggingface.co/pyannote/segmentation)
   - Click "Accept" on both model pages
4. Enter your token in Scribey's Settings tab

## Usage

1. Launch the application:
   ```bash
   python Scribey.py
   ```

2. Add files:
   - Click "Add Files" or drag-and-drop
   - Supported formats: mp3, wav, m4a, mp4, avi, mov, mkv, webm

3. Configure options:
   - Select Whisper model (tiny to large)
   - Enable/disable speaker diarization
   - Choose output format

4. Click "Start Transcription"

## Technical Details

### Large File Processing

Scribey uses smart chunking for processing large files:
- Audio files are automatically split into 30-minute segments
- Each segment is processed independently
- Results are merged seamlessly
- Speakers are tracked consistently across chunks
- Memory usage is optimized for large files

This approach allows Scribey to handle files of any length while maintaining consistent speaker identification and transcription quality.

### Output Format

The transcript is formatted with clear speaker separation:
```
SPEAKER 1
This is the first speaker talking.

SPEAKER 2
This is the second speaker responding.
```

Optional timestamps can be included:
```
SPEAKER 1
[0.00s - 2.34s] This is the first speaker talking.

SPEAKER 2
[2.34s - 4.56s] This is the second speaker responding.
```

## Troubleshooting

### Common Issues:

1. **FFmpeg Not Found**:
   - Verify FFmpeg is installed: `ffmpeg -version`
   - Check if it's in your system PATH
   - Try reinstalling FFmpeg

2. **Speaker Diarization Issues**:
   - Verify your HuggingFace token
   - Ensure you've accepted both model terms
   - For large files, expect longer processing times
   - GPU acceleration is recommended but not required

3. **Memory Issues**:
   - The application automatically manages memory for large files
   - Consider using a smaller Whisper model for faster processing
   - For very large files, the chunking system will handle processing automatically

### Performance Tips:

1. **Model Selection**:
   - tiny: Fastest, lowest accuracy
   - base: Good balance (recommended)
   - small: Better accuracy, slower
   - medium: High accuracy, slower
   - large: Best accuracy, slowest

2. **Processing Time**:
   - Transcription: ~0.3-0.5x audio duration with GPU
   - Diarization: ~0.3-2x audio duration depending on hardware
   - Total time varies based on file length and chosen options

## Key fixes
**Key Fixes in 1.2.0**

- Fixed YouTube download file handling issues
- Resolved memory issues with large file diarization
- Fixed inconsistent speaker labeling across chunks
- Improved temporary file management
- Fixed drag-and-drop issues when running as administrator
- Resolved output formatting inconsistencies
- Fixed progress display ANSI code issues

## Changelog
**Version 1.2.0**

- Improved YouTube download reliability and error handling
- Added proper YouTube URL input dialog
- Enhanced speaker diarization for large files with chunked processing
- Improved file queue display with clear YouTube video titles
- Added automatic cleanup of temporary files
- Fixed drag-and-drop functionality
- Added progress indicators for YouTube downloads
- Separated "Add Files" and "Add YouTube URL" functions for better UX

**Version 1.1.0**

- Enhanced speaker diarization handling
- Added alternative diarization method
- Improved error handling and user feedback
- Added custom output naming options
- Added batch processing capabilities

**Version 1.0.0**

- Initial Release
- Basic transcription functionality
- YouTube support
- Simple speaker diarization

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## License

GPL License - See LICENSE file for details

## Acknowledgments

- OpenAI's Whisper for transcription
- pyannote.audio for speaker diarization
- yt-dlp for YouTube support
- HuggingFace for model hosting
