import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
import whisper
import yt_dlp
import os
import sys
import re
import json
from urllib.parse import urlparse
import subprocess
from pathlib import Path
import torch
import warnings
import requests
import traceback
import webbrowser
from datetime import datetime
import queue
import shutil
import subprocess
from pathlib import Path

# Constants and Configuration
DEPENDENCIES = {
    'base': ['openai-whisper', 'yt-dlp', 'tkinterdnd2', 'ffmpeg-python'],
    'diarization': ['pyannote.audio', 'torch'],
    'enhanced_formats': ['pandas']
}

HF_TOKEN_INSTRUCTIONS = """
To use speaker diarization, you need a HuggingFace token:
1. Go to https://huggingface.co/settings/tokens
2. Create a new token
3. Save it in the settings
"""

class YouTubeInputDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Configure dialog
        self.title("Add YouTube Video")
        self.geometry("500x150")
        
        # Create widgets
        ttk.Label(self, text="Enter YouTube URL:", padding=10).pack()
        
        self.url_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.url_var, width=50)
        self.entry.pack(padx=10, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Add", command=self._on_add).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=5)
        
        # Center dialog on parent
        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        
        # Set focus on entry
        self.entry.focus_set()
        self.bind("<Return>", lambda e: self._on_add())
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        # Wait for user input
        self.wait_window(self)
    
    def _on_add(self):
        self.result = self.url_var.get()
        self.destroy()
    
    def _on_cancel(self):
        self.destroy()

class ChoiceDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.result = None
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create widgets
        ttk.Label(self, text=message, wraplength=400, padding=20).pack()
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, 
                  text="Continue without diarization", 
                  command=lambda: self.set_result(1)).pack(pady=5)
        ttk.Button(btn_frame, 
                  text="Try alternative method", 
                  command=lambda: self.set_result(2)).pack(pady=5)
        ttk.Button(btn_frame, 
                  text="Cancel transcription", 
                  command=lambda: self.set_result(3)).pack(pady=5)
        
        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                 parent.winfo_rooty()+50))
        
        self.wait_window(self)
    
    def set_result(self, value):
        self.result = value
        self.destroy()

class Settings:
    def __init__(self):
        self.config_file = "transcription_settings.json"
        self.default_settings = {
            "model_size": "base",
            "output_format": "raw",
            "include_timestamps": False,
            "use_diarization": False,
            "output_directory": "",
            "last_input_directory": "",
            "hf_token": "",
            "dark_mode": False,
            "batch_processing": False,
            "recent_files": [],
            "last_used": datetime.now().isoformat()
        }
        self.current = self.load()
    
    def load(self):
        try:
            with open(self.config_file, 'r') as f:
                settings = json.load(f)
                # Update with any new default settings
                for key in self.default_settings:
                    if key not in settings:
                        settings[key] = self.default_settings[key]
                return settings
        except:
            return self.default_settings.copy()
    
    def save(self):
        self.current["last_used"] = datetime.now().isoformat()
        with open(self.config_file, 'w') as f:
            json.dump(self.current, f, indent=2)

    def update_recent_files(self, filepath):
        if filepath not in self.current["recent_files"]:
            self.current["recent_files"].insert(0, filepath)
            self.current["recent_files"] = self.current["recent_files"][:10]  # Keep last 10
            self.save()

class DependencyManager:
    @staticmethod
    def check_dependencies(feature='base'):
        missing = []
        required = DEPENDENCIES.get(feature, [])
        
        for package in required:
            try:
                if package == 'openai-whisper':
                    import whisper
                elif package == 'ffmpeg-python':
                    # Try running ffmpeg directly
                    result = subprocess.run(['ffmpeg', '-version'], 
                                         capture_output=True, 
                                         text=True)
                    if result.returncode != 0:
                        missing.append(package)
                else:
                    __import__(package.replace('-', '_'))
            except (ImportError, FileNotFoundError, subprocess.SubprocessError):
                missing.append(package)
        
        return missing

    @staticmethod
    def install_dependencies(packages):
        results = []
        for package in packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                results.append((package, True, "Successfully installed"))
            except Exception as e:
                results.append((package, False, str(e)))
        return results

    @staticmethod
    def check_ffmpeg():
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except:
            return False

    @staticmethod
    def check_diarization_auth():
        """Check for HuggingFace token in settings"""
        try:
            settings = Settings().current
            token = settings.get("hf_token")
            if token and len(token) > 0:
                return True
        except:
            pass
        return False

class TranscriptionWorker:
    def __init__(self, callback):
        self.callback = callback
        self.queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        self.speaker_map = {}  # Add this line to store speaker mappings

    def _get_speaker_label(self, original_label):
        """Convert pyannote speaker labels to friendly names"""
        if original_label == "UNKNOWN":
            return "UNKNOWN"
            
        if original_label not in self.speaker_map:
            # Create new speaker number (1-based indexing)
            speaker_num = len(self.speaker_map) + 1
            self.speaker_map[original_label] = f"{speaker_num}"
            
        return self.speaker_map[original_label]

    def _process_queue(self):
        while self.running:
            try:
                task = self.queue.get(timeout=1)
                if task is None:
                    continue
                
                input_path, output_path, options = task
                self._process_task(input_path, output_path, options)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.callback.on_error(str(e))

    def _process_task(self, input_path, output_path, options):
        """Process a single transcription task with proper resource management"""
        temp_files = []
        try:
            # Download if YouTube
            if self._is_youtube_url(input_path):
                self.callback.on_status("Downloading YouTube audio...")
                temp_audio = self._download_youtube_audio(input_path)
                temp_files.append(temp_audio)
                processed_input = temp_audio
            else:
                processed_input = input_path

            # Load model
            self.callback.on_status("Loading Whisper model...")
            model = whisper.load_model(self.callback.model_size.get())

            # Transcribe
            self.callback.on_status("Transcribing audio...")
            result = model.transcribe(processed_input)

            # Handle diarization if requested
            if options.get("use_diarization"):
                self.callback.on_status("Processing speaker diarization...")
                result = self._add_speaker_diarization(result, processed_input)

            # Save output
            self.callback.on_status("Saving transcript...")
            self._save_transcript(result, output_path, options)

            self.callback.on_complete(output_path)

        except Exception as e:
            self.callback.log(f"Error details: {str(e)}")
            self.callback.on_error(str(e))
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self.callback.log(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    self.callback.log(f"Failed to clean up {temp_file}: {str(e)}")

    def _is_youtube_url(self, url):
        try:
            parsed = urlparse(url)
            return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc
        except:
            return False

    def _download_youtube_audio(self, url):
        """Download YouTube audio with improved error handling and path management"""
        import os
        import tempfile
        from datetime import datetime
        
        try:
            # Create temp file in system temp directory
            temp_dir = tempfile.gettempdir()
            temp_filename = f"scribey_yt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            self.callback.log(f"Downloading to: {temp_path}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,  # No extension - let yt-dlp handle it
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._download_progress_hook]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.callback.log("Starting YouTube download...")
                ydl.download([url])
                
                # The actual file will have .mp3 extension added by yt-dlp
                final_path = temp_path + '.mp3'
                
                # Verify file exists after download
                if not os.path.exists(final_path):
                    # Try alternate path (some yt-dlp versions handle this differently)
                    alt_path = temp_path + '.audio.mp3'
                    if os.path.exists(alt_path):
                        final_path = alt_path
                    else:
                        # List all files in temp directory for debugging
                        files = os.listdir(temp_dir)
                        matching_files = [f for f in files if f.startswith(temp_filename)]
                        if matching_files:
                            final_path = os.path.join(temp_dir, matching_files[0])
                        else:
                            raise FileNotFoundError(f"Downloaded file not found. Tried paths:\n"
                                                f"- {final_path}\n"
                                                f"- {alt_path}")
                
                self.callback.log(f"Download completed: {final_path}")
                return final_path
            
        except Exception as e:
            self.callback.log(f"Download error: {str(e)}")
            raise Exception(f"YouTube download failed: {str(e)}")

    def _download_progress_hook(self, d):
        """Progress hook for YouTube download"""
        if d['status'] == 'downloading':
            try:
                # Remove ANSI color codes from the percentage string
                percent = d['_percent_str'].replace('[0;94m', '').replace('[0m', '')
                speed = d.get('_speed_str', 'N/A').replace('[0;32m', '').replace('[0m', '')
                self.callback.on_status(f"Downloading: {percent.strip()} at {speed.strip()}")
            except:
                pass
        elif d['status'] == 'finished':
            self.callback.on_status("Download finished, processing audio...")
            
    def _add_speaker_diarization(self, whisper_result, audio_path):
        try:
            from pyannote.audio import Pipeline
            import soundfile as sf
            import librosa
            import tempfile
            import os
            settings = Settings().current
            token = settings.get("hf_token")
            
            if not token:
                raise ValueError("No HuggingFace token found in settings")
            
            # Suppress torchaudio warning
            import warnings
            warnings.filterwarnings("ignore", message=".*torchaudio.*backend.*")
            
            try:
                # Convert audio to WAV format first
                self.callback.on_status("Converting audio format...")
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_wav_path = temp_wav.name
                    # Load and resample audio
                    y, sr = librosa.load(audio_path, sr=16000)
                    sf.write(temp_wav_path, y, sr, format='WAV')
                
                # First try to load the pipeline
                self.callback.on_status("Loading diarization model...")
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization@2.1",
                    use_auth_token=token
                )

                self.callback.on_status("Performing speaker diarization...")
                diarization = pipeline(temp_wav_path)
                
                # Process results
                speakers = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    speakers.append({
                        'start': turn.start,
                        'end': turn.end,
                        'speaker': speaker
                    })
                
                # Clean up temporary file
                try:
                    os.remove(temp_wav_path)
                except:
                    pass
                    
                # Add speaker information to whisper segments
                for segment in whisper_result.get("segments", []):
                    if not isinstance(segment, dict):
                        continue
                        
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', 0)
                    
                    matching_speakers = []
                    for speaker in speakers:
                        if (start_time >= speaker['start'] and 
                            end_time <= speaker['end']):
                            matching_speakers.append(speaker['speaker'])
                    
                    if matching_speakers:
                        from collections import Counter
                        segment['speaker'] = Counter(matching_speakers).most_common(1)[0][0]
                    else:
                        segment['speaker'] = "UNKNOWN"
                
                return whisper_result

            except Exception as e:
                error_msg = str(e)
                if "gated" in error_msg.lower() or "private" in error_msg.lower():
                    error_msg = (
                        "Please accept the model terms for both:\n"
                        "1. https://huggingface.co/pyannote/speaker-diarization\n"
                        "2. https://huggingface.co/pyannote/segmentation\n\n"
                        "After accepting, ensure your token has 'read' access."
                    )
                elif "Format not recognised" in str(e):
                    error_msg = (
                        "Audio format not supported directly.\n"
                        "Converting to compatible format..."
                    )
                elif "connection" in error_msg.lower():
                    error_msg = "Failed to connect. Please check your internet connection."
                
                dialog = ChoiceDialog(
                    self.callback.root,
                    "Diarization Failed",
                    f"Diarization failed: {error_msg}\n\nWhat would you like to do?"
                )
                
                if dialog.result == 1:  # Continue without
                    return whisper_result
                elif dialog.result == 2:  # Try alternative
                    return self._alternative_diarization(whisper_result, audio_path)
                else:  # Cancel
                    raise ValueError("Transcription cancelled by user")

        except Exception as e:
            self.callback.on_status(f"Diarization failed: {str(e)}")
            import traceback
            self.callback.log(f"Full diarization error:\n{traceback.format_exc()}")
            
            dialog = ChoiceDialog(
                self.callback.root,
                "Diarization Failed",
                f"Diarization failed: {str(e)}\n\nWhat would you like to do?"
            )
            
            if dialog.result == 1:
                return whisper_result
            elif dialog.result == 2:
                return self._alternative_diarization(whisper_result, audio_path)
            else:
                raise ValueError("Transcription cancelled by user")

    def _alternative_diarization(self, whisper_result, audio_path):
        """Alternative diarization method using direct pipeline"""
        try:
            self.callback.on_status("Attempting alternative diarization method...")
            
            # Try using a different model configuration
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization@2.1",
                use_auth_token=self.callback.settings.current.get("hf_token")
            )

            # Apply diarization
            self.callback.on_status("Running diarization...")
            diarization = pipeline(audio_path)
            
            # Process results
            speakers = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })
            
            # Add speaker information to whisper segments
            for segment in whisper_result["segments"]:
                matching_speakers = []
                for speaker in speakers:
                    if (segment['start'] >= speaker['start'] and 
                        segment['end'] <= speaker['end']):
                        matching_speakers.append(speaker['speaker'])
                
                if matching_speakers:
                    # If multiple speakers found, use the most common one
                    from collections import Counter
                    segment['speaker'] = Counter(matching_speakers).most_common(1)[0][0]
                else:
                    segment['speaker'] = "UNKNOWN"
            
            return whisper_result
            
        except Exception as e:
            self.callback.on_status(f"Alternative diarization failed: {str(e)}")
            self.callback.log(f"Alternative diarization error:\n{traceback.format_exc()}")
            
            if messagebox.askyesno("Alternative Method Failed",
                "Alternative diarization method also failed.\n\n"
                "Would you like to continue without speaker diarization?"):
                return whisper_result
            else:
                raise ValueError("Transcription cancelled by user")

    def _save_transcript(self, result, output_path, options):
        """Save transcript with improved formatting for speaker diarization"""
        with open(output_path, "w", encoding="utf-8") as f:
            current_speaker = None
            
            for segment in result["segments"]:
                # Get timestamp if needed
                timestamp = ""
                if options.get("include_timestamps"):
                    timestamp = f"[{segment['start']:.2f}s - {segment['end']:.2f}s] "
                
                # Handle speaker changes
                speaker = segment.get('speaker', 'UNKNOWN')
                text = segment['text'].strip()
                
                # Only write speaker header when speaker changes
                if speaker != current_speaker:
                    # Add single blank line between speakers (but not at the start of file)
                    if current_speaker is not None:
                        f.write("\n")
                    f.write(f"SPEAKER {speaker}\n")
                    current_speaker = speaker
                
                # Write the text with optional timestamp
                if options.get("include_timestamps"):
                    f.write(f"{timestamp}{text}")
                else:
                    f.write(text)
                
                # Add a single newline after each utterance
                f.write("\n")

    def add_task(self, input_path, output_path, options):
        self.queue.put((input_path, output_path, options))

    def stop(self):
        self.running = False

class TranscriptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Transcription Tool")
        self.root.geometry("800x900")
        
        # Initialize settings
        self.settings = Settings()
        
        # Setup variables
        self.input_type = tk.StringVar(value="file")
        self.model_size = tk.StringVar(value=self.settings.current["model_size"])
        self.output_format = tk.StringVar(value=self.settings.current["output_format"])
        self.timestamps = tk.BooleanVar(value=self.settings.current["include_timestamps"])
        self.speaker_diarization = tk.BooleanVar(value=self.settings.current["use_diarization"])
        self.batch_processing = tk.BooleanVar(value=self.settings.current["batch_processing"])
        self.input_paths = []
        self.output_path = tk.StringVar()
        self.youtube_titles = {}
        
        # Initialize worker
        self.worker = TranscriptionWorker(self)
        
        self.check_diarization_setup()
        self.setup_ui()
        self.check_initial_dependencies()

    def check_diarization_setup(self):
        """Check if diarization is properly set up, if not, run setup script"""
        if self.settings.current.get("use_diarization", False):
            cache_dir = Path.home() / ".cache" / "pyannote"
            hub_dir = Path.home() / ".cache" / "hub"
            
            if not (cache_dir.exists() and hub_dir.exists()):
                try:
                    # Run the setup script
                    setup_script = Path(__file__).parent / "diarization_setup.py"
                    result = subprocess.run([sys.executable, str(setup_script), "--setup"],
                                         capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        self.log("Warning: Diarization setup failed. Some features may not work.")
                        self.log(f"Setup error: {result.stderr}")
                except Exception as e:
                    self.log(f"Error running diarization setup: {e}")   

    def check_initial_dependencies(self):
        """Check for required dependencies when the app starts"""
        # Check base dependencies
        missing = DependencyManager.check_dependencies('base')
        if missing:
            if messagebox.askyesno("Missing Dependencies", 
                f"Some required packages are missing: {', '.join(missing)}\n"
                "Would you like to install them now?"):
                results = DependencyManager.install_dependencies(missing)
                for package, success, message in results:
                    self.log(f"{package}: {'Success' if success else 'Failed - ' + message}")
            else:
                self.root.quit()
                return

        # Check ffmpeg
        if not DependencyManager.check_ffmpeg():
            messagebox.showwarning("FFmpeg Required", 
                "FFmpeg is required but not found in system PATH.\n"
                "Please install FFmpeg and ensure it's in your system PATH.")

        # Check for diarization if enabled
        if self.speaker_diarization.get():
            self.check_diarization()

    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Main tab
        main_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_frame, text="Main")
        
        # Settings tab
        settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_frame, text="Settings")
        
        # Setup main tab
        self.setup_main_tab(main_frame)
        
        # Setup settings tab
        self.setup_settings_tab(settings_frame)
        
        # Status bar at bottom of window
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        self.progress = ttk.Progressbar(status_frame, mode='determinate')
        self.progress.pack(fill="x", side="top")
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side="left")

    def setup_main_tab(self, parent):
        # Input section
        input_frame = ttk.LabelFrame(parent, text="Input", padding="5")
        input_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Radiobutton(input_frame, text="Local Files", 
                       variable=self.input_type, value="file",
                       command=self.toggle_input_mode).pack(side="left")
        ttk.Radiobutton(input_frame, text="YouTube URLs", 
                       variable=self.input_type, value="youtube",
                       command=self.toggle_input_mode).pack(side="left")
        
        # Files list
        self.files_frame = ttk.LabelFrame(parent, text="Files", padding="5")
        self.files_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.files_list = tk.Listbox(self.files_frame, selectmode=tk.EXTENDED)
        self.files_list.pack(fill="both", expand=True, side="left")

        # Add placeholder text
        self.files_list.insert(tk.END, "Drag files here or use 'Add Files/URLs' button")
        self.files_list.config(foreground="gray")
        
        # Bind the list change handler
        self.files_list.bind('<<ListboxSelect>>', self.on_list_change)

        self.files_list.drop_target_register(DND_FILES)
        self.files_list.dnd_bind('<<Drop>>', self.handle_drop)
        
        scrollbar = ttk.Scrollbar(self.files_frame, orient="vertical", 
                                command=self.files_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.files_list.configure(yscrollcommand=scrollbar.set)
        
        # Buttons for file management
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add Files", 
                  command=self.add_files).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Add YouTube URL", 
                  command=self.add_youtube_url).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Selected", 
                  command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_files).pack(side="left", padx=5)
        
        help_text = ttk.Label(input_frame, 
            text="You can add multiple files or YouTube URLs to the queue",
            foreground="gray")
        help_text.pack(side="right", padx=5)

        # Output section
        output_frame = ttk.LabelFrame(parent, text="Output", padding="5")
        output_frame.pack(fill="x", padx=5, pady=5)
        
        # Directory selection
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill="x", pady=2)

        ttk.Label(dir_frame, text="Output Directory:").pack(side="left")
        ttk.Entry(dir_frame, textvariable=self.output_path).pack(side="left", 
                                                                   fill="x", 
                                                                   expand=True, 
                                                                   padx=5)
        ttk.Button(dir_frame, text="Browse", 
                  command=self.browse_output).pack(side="right")
        
        # File naming options
        name_frame = ttk.Frame(output_frame)
        name_frame.pack(fill="x", pady=2)
        ttk.Label(name_frame, text="File naming:").pack(side="left")
        self.naming_mode = tk.StringVar(value="auto")
        ttk.Radiobutton(name_frame, text="Automatic", 
                        variable=self.naming_mode, 
                        value="auto").pack(side="left", padx=5)
        ttk.Radiobutton(name_frame, text="Custom prefix", 
                        variable=self.naming_mode, 
                        value="custom").pack(side="left", padx=5)
        self.custom_prefix = tk.StringVar()
        self.prefix_entry = ttk.Entry(name_frame, textvariable=self.custom_prefix)
        self.prefix_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Options", padding="5")
        options_frame.pack(fill="x", padx=5, pady=5)
        
        # Model selection
        ttk.Label(options_frame, text="Model:").pack(side="left")
        model_combo = ttk.Combobox(options_frame, 
                                 values=["tiny", "base", "small", "medium", "large"],
                                 textvariable=self.model_size)
        model_combo.pack(side="left", padx=5)
        
        # Checkboxes for options
        ttk.Checkbutton(options_frame, text="Include Timestamps", 
                       variable=self.timestamps).pack(side="left", padx=5)
        
        self.diarization_check = ttk.Checkbutton(options_frame, 
                                                text="Speaker Diarization", 
                                                variable=self.speaker_diarization,
                                                command=self.check_diarization)
        self.diarization_check.pack(side="left", padx=5)
        
        ttk.Checkbutton(options_frame, text="Batch Processing", 
                       variable=self.batch_processing).pack(side="left", padx=5)
        
        # Start button
        self.start_button = ttk.Button(parent, text="Start Transcription", 
                                     command=self.start_transcription)
        self.start_button.pack(pady=10)
        
        # Log area
        log_frame = ttk.LabelFrame(parent, text="Log", padding="5")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True)

    def on_list_change(self, event=None):
        """Clear placeholder text when items are added"""
        if self.files_list.size() == 1 and \
        self.files_list.get(0) == "Drag files here or use 'Add Files/URLs' button":
            self.files_list.delete(0)
            self.files_list.config(foreground="black")

    def get_output_filename(self, input_path, index=0):
        """Updated filename generation for YouTube videos"""
        if self.naming_mode.get() == "auto":
            if input_path in self.youtube_titles:
                # Use video title for YouTube URLs
                base = self.youtube_titles[input_path]
                # Clean the title for use as filename
                base = "".join(c for c in base if c.isalnum() or c in (' ', '-', '_')).rstrip()
            else:
                base = os.path.splitext(os.path.basename(input_path))[0]
            return f"{base}_transcript.txt"
        else:
            prefix = self.custom_prefix.get() or "transcript"
            if self.batch_processing.get():
                return f"{prefix}_{index + 1}.txt"
            return f"{prefix}.txt"

    def setup_settings_tab(self, parent):
        # HuggingFace Token
        token_frame = ttk.LabelFrame(parent, text="HuggingFace Token", padding="5")
        token_frame.pack(fill="x", padx=5, pady=5)
        
        self.hf_token = tk.StringVar(value=self.settings.current.get("hf_token", ""))
        ttk.Entry(token_frame, textvariable=self.hf_token, show="*").pack(fill="x", padx=5)
        ttk.Button(token_frame, text="Save Token", 
                  command=self.save_hf_token).pack(pady=5)
        
        # Instructions
        ttk.Label(parent, text=HF_TOKEN_INSTRUCTIONS, 
                 wraplength=500, justify="left").pack(pady=10)
        
        # Default settings
        defaults_frame = ttk.LabelFrame(parent, text="Default Settings", padding="5")
        defaults_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Checkbutton(defaults_frame, text="Dark Mode", 
                       variable=tk.BooleanVar(value=self.settings.current["dark_mode"]),
                       command=self.toggle_theme).pack()
        
        ttk.Label(token_frame, text="Note: Token must have 'Read public gated models' permission", 
              wraplength=400).pack(pady=5)
    
        link = ttk.Label(token_frame, 
                        text="Configure token permissions", 
                        foreground="blue", 
                        cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://huggingface.co/settings/tokens"))
        
    def verify_huggingface_token(self):
        """Verify HuggingFace token and model access"""
        if not self.speaker_diarization.get():
            return True
            
        token = self.settings.current.get("hf_token")
        if not token:
            messagebox.showerror("Error", 
                "HuggingFace token not found. Please add it in Settings.")
            return False
        
        models = [
            "pyannote/speaker-diarization",
            "pyannote/segmentation"
        ]
        
        try:
            for model in models:
                response = requests.get(
                    f"https://huggingface.co/{model}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    messagebox.showwarning("Model Access Required", 
                        f"Please accept the terms for {model}:\n\n"
                        f"1. Visit https://huggingface.co/{model}\n"
                        "2. Accept the user conditions\n"
                        "3. Ensure your token has 'read' access\n\n"
                        "After completing these steps, try again.")
                    return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", 
                f"Failed to verify model access: {str(e)}\n"
                "Please check your internet connection.")
            return False

    def check_diarization(self):
        """Modified check_diarization method"""
        if self.speaker_diarization.get():
            missing = DependencyManager.check_dependencies('diarization')
            if missing:
                if messagebox.askyesno("Missing Dependencies", 
                    f"Speaker diarization requires additional packages: {', '.join(missing)}\n"
                    "Would you like to install them now?"):
                    results = DependencyManager.install_dependencies(missing)
                    for package, success, message in results:
                        self.log(f"{package}: {'Success' if success else 'Failed - ' + message}")
                else:
                    self.speaker_diarization.set(False)
                    return
            
            # Run diarization setup if needed
            self.check_diarization_setup()
            
            # Check for token in settings
            if not DependencyManager.check_diarization_auth():
                messagebox.showwarning("Authentication Required", 
                    "Speaker diarization requires HuggingFace authentication.\n"
                    "Please add your token in the Settings tab.")
                self.speaker_diarization.set(False)
                self.notebook.select(1)  # Switch to settings tab

    def save_hf_token(self):
        token = self.hf_token.get()
        if token:
            self.settings.current["hf_token"] = token
            self.settings.save()
            messagebox.showinfo("Success", "Token saved successfully!")
        else:
            messagebox.showwarning("Warning", "Please enter a token first.")

    def toggle_theme(self):
        # Implement dark/light theme switching
        pass

    def toggle_input_mode(self):
        """Updated toggle function to handle YouTube mode better"""
        is_file = self.input_type.get() == "file"
        
        # Update button states
        self.add_files_btn["state"] = "normal" if is_file else "disabled"
        self.add_url_btn["state"] = "disabled" if is_file else "normal"
        
        # Enable/disable drag and drop
        if is_file:
            self.files_list.drop_target_register(DND_FILES)
        else:
            try:
                self.files_list.drop_target_unregister()
            except:
                pass
                    
        # Keep batch processing enabled for both modes
        self.batch_processing["state"] = "normal"

    def add_files(self):
        """Handle adding local files"""
        files = filedialog.askopenfilenames(
            filetypes=[("Audio/Video files", 
                      "*.mp3 *.wav *.mp4 *.avi *.mov *.mkv *.m4a *.webm")]
        )
        for file in files:
            if file not in self.input_paths:
                self.input_paths.append(file)
                self.files_list.insert(tk.END, os.path.basename(file))

    def add_youtube_url(self):
        """Handle adding YouTube URLs with improved UI"""
        dialog = YouTubeInputDialog(self.root)
        url = dialog.result
        
        if url:
            if url not in self.input_paths:
                # Show loading indicator
                self.status_label["text"] = "Fetching video info..."
                self.root.update()
                
                try:
                    # Get video title
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title = info.get('title', url)
                        
                    self.input_paths.append(url)
                    self.youtube_titles[url] = title
                    display_text = f"🎬 {title}"  # Using emoji for visual distinction
                    self.files_list.insert(tk.END, display_text)
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to fetch video info: {str(e)}")
                finally:
                    self.status_label["text"] = "Ready"
            else:
                messagebox.showwarning("Warning", "This URL is already in the queue.")

    def remove_selected(self):
        """Updated remove function to handle YouTube entries"""
        selected = self.files_list.curselection()
        for index in reversed(selected):
            path = self.input_paths[index]
            self.files_list.delete(index)
            self.input_paths.pop(index)
            if path in self.youtube_titles:
                del self.youtube_titles[path]

    def clear_files(self):
            """Updated clear function to handle YouTube entries"""
            self.files_list.delete(0, tk.END)
            self.input_paths.clear()
            self.youtube_titles.clear()

    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_path.set(directory)
            self.settings.current["output_directory"] = directory
            self.settings.save()

    def handle_drop(self, event):
        """Handle drag and drop of files"""
        files = event.data
        if files:
            # Handle multiple files from drag and drop
            file_list = self.root.tk.splitlist(files)
            for file in file_list:
                # Clean up the file path (remove braces and quotes if present)
                file = file.strip('{}')
                if file not in self.input_paths:
                    self.input_paths.append(file)
                    self.files_list.insert(tk.END, os.path.basename(file))

    def start_transcription(self):
        if not self.input_paths:
            messagebox.showwarning("Warning", "Please add input files first.")
            return
        
        if not self.output_path.get():
            messagebox.showwarning("Warning", "Please select an output directory.")
            return
        
        # Verify HuggingFace token if diarization is enabled
        if self.speaker_diarization.get() and not self.verify_huggingface_token():
            return
        
        options = {
            "include_timestamps": self.timestamps.get(),
            "use_diarization": self.speaker_diarization.get(),
        }
        
        for idx, input_path in enumerate(self.input_paths):
            output_filename = self.get_output_filename(input_path, idx)
            output_path = os.path.join(self.output_path.get(), output_filename)
            
            if os.path.exists(output_path):
                if not messagebox.askyesno("File exists", 
                    f"{output_filename} already exists. Overwrite?"):
                    continue
            
            self.worker.add_task(input_path, output_path, options)

    def log(self, message):
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')}: {message}\n")
        self.log_text.see(tk.END)

    # Callback methods for TranscriptionWorker
    def on_status(self, message):
        self.status_label["text"] = message
        self.log(message)

    def on_progress(self, value):
        self.progress["value"] = value

    def on_error(self, error):
        self.log(f"Error: {error}")
        messagebox.showerror("Error", error)

    def on_complete(self, output_path):
        self.log(f"Completed: {output_path}")
        self.status_label["text"] = "Ready"
        self.progress["value"] = 0

def main():
    root = TkinterDnD.Tk()
    app = TranscriptionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()