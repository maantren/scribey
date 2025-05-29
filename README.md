# Scribey - Advanced Audio Transcription Tool

A powerful, user-friendly GUI application for transcribing audio and video files using OpenAI's Whisper model (via faster-whisper), with support for speaker diarization, batch processing, and YouTube video transcription.

## Features

- 🎯 **Smart Transcription**: Uses faster-whisper for accurate and efficient speech-to-text conversion
- 👥 **Speaker Detection**: Identifies different speakers in the audio (optional)
- 📺 **YouTube Support**: Direct transcription from YouTube URLs
- 📦 **Batch Processing**: Handle multiple files efficiently
- 🖱️ **User-Friendly**: Simple drag-and-drop interface
- ⚡ **Fast Processing**: Uses faster-whisper for improved speed and efficiency
- 🎛️ **Multiple Models**: Choose from different Whisper models based on your needs
- 🐍 **Python 3.13 Compatible**: Works with the latest Python versions

## Complete Installation Guide

### 1. Install Python

1. Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
   - **Note**: Python 3.13 is fully supported!
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

2. Install core packages (required):
   ```bash
   pip install faster-whisper
   pip install yt-dlp
   pip install tkinterdnd2
   pip install ffmpeg-python
   pip install requests
   pip install pandas
   ```

3. Install PyTorch (required):
   ```bash
   # For most users (CPU + GPU support):
   pip install torch torchvision torchaudio
   
   # OR for CPU-only (smaller download):
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

4. Install speaker diarization packages (optional):
   ```bash
   pip install pyannote.audio
   ```
   **Note**: Speaker diarization may not work with Python 3.13. If you encounter issues, you can still use all other features.

### 4. Set Up Speaker Diarization (Optional)

If you want speaker identification features:

1. Create a HuggingFace account at [huggingface.co](https://huggingface.co/join)
2. Get your access token:
   - Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Create new token with 'read' access (specifically, 'Read access to contents of all public gated repos you can access' under 'Repositories')
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
   - Enable/disable speaker diarization (if available)
   - Choose output format

4. Click "Start Transcription"

## Technical Details

### Performance Improvements

Scribey now uses **faster-whisper** instead of the original openai-whisper, providing:
- **2-4x faster transcription** on most hardware
- **Lower memory usage** for large files
- **Better Python 3.13 compatibility**
- **Same accuracy** as original Whisper models

### Large File Processing

Scribey uses smart chunking for processing large files:
- Audio files are automatically split into manageable segments
- Each segment is processed independently
- Results are merged seamlessly
- Speakers are tracked consistently across chunks
- Memory usage is optimized for large files

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

1. **Python 3.13 Compatibility**:
   - ✅ **Core transcription**: Fully supported
   - ✅ **YouTube downloads**: Fully supported  
   - ⚠️ **Speaker diarization**: May have issues with Python 3.13
   - **Solution**: All features except speaker diarization will work perfectly

2. **Missing Dependencies**:
   - The app will automatically detect missing packages on startup
   - Install packages one by one as errors appear
   - Use `pip install --user` if you get permission errors

3. **FFmpeg Not Found**:
   - Verify FFmpeg is installed: `ffmpeg -version`
   - Check if it's in your system PATH
   - Try reinstalling FFmpeg

4. **Speaker Diarization Issues**:
   - Verify your HuggingFace token in Settings tab
   - Ensure you've accepted both model terms
   - If it fails to install, you can still use transcription without speaker identification

5. **PyTorch Installation Problems**:
   - Try CPU-only version: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
   - For older systems, use: `pip install torch==1.13.1`

### Performance Tips:

1. **Model Selection**:
   - `tiny`: Fastest, lowest accuracy (~32x realtime)
   - `base`: Good balance (recommended) (~16x realtime)
   - `small`: Better accuracy (~6x realtime)
   - `medium`: High accuracy (~2x realtime)
   - `large`: Best accuracy (~1x realtime)

2. **Processing Time with faster-whisper**:
   - Transcription: ~0.1-0.3x audio duration (much faster than before!)
   - Diarization: ~0.3-2x audio duration depending on hardware
   - YouTube downloads: Depends on video length and internet speed

## Version History

### Version 1.3.0 (Latest)
- **🚀 Major Update**: Switched to faster-whisper for 2-4x speed improvement
- **🐍 Python 3.13 Support**: Full compatibility with latest Python
- **⚡ Performance**: Significantly faster transcription times
- **📦 Better Dependency Management**: Graceful handling of missing packages
- **🔧 Improved Error Handling**: Better user feedback for installation issues
- **💾 Lower Memory Usage**: More efficient processing of large files

### Version 1.2.0
- Improved YouTube download reliability and error handling
- Added proper YouTube URL input dialog
- Enhanced speaker diarization for large files with chunked processing
- Improved file queue display with clear YouTube video titles
- Added automatic cleanup of temporary files
- Fixed drag-and-drop functionality
- Added progress indicators for YouTube downloads

### Version 1.1.0
- Enhanced speaker diarization handling
- Added alternative diarization method
- Improved error handling and user feedback
- Added custom output naming options
- Added batch processing capabilities

### Version 1.0.0
- Initial Release
- Basic transcription functionality
- YouTube support
- Simple speaker diarization

## What's New in 1.3.0

The biggest change is the switch to **faster-whisper**, which provides:
- Much faster transcription speeds
- Better compatibility with newer Python versions
- Lower memory usage
- Same transcription quality

If you're upgrading from an older version, you'll need to:
1. Uninstall old whisper: `pip uninstall openai-whisper`
2. Install faster-whisper: `pip install faster-whisper`
3. The rest works exactly the same!

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

- OpenAI's Whisper for the underlying AI models
- faster-whisper for the efficient implementation
- pyannote.audio for speaker diarization
- yt-dlp for YouTube support
- HuggingFace for model hosting
- The Python community for excellent package ecosystem
