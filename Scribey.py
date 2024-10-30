import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import whisper
import yt_dlp
import os
import sys
import re
import json
from tkinterdnd2 import DND_FILES, TkinterDnD
from urllib.parse import urlparse
import subprocess
from pathlib import Path
import torch
from datetime import datetime
import queue

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
        try:
            # Download if YouTube
            if self._is_youtube_url(input_path):
                self.callback.on_status("Downloading YouTube audio...")
                input_path = self._download_youtube_audio(input_path)

            # Load model (using the parent's model_size setting)
            self.callback.on_status("Loading Whisper model...")
            model = whisper.load_model(self.callback.model_size.get())

            # Transcribe (without model_size in options)
            self.callback.on_status("Transcribing audio...")
            result = model.transcribe(input_path)

            # Handle diarization if requested
            if options.get("use_diarization"):
                self.callback.on_status("Processing speaker diarization...")
                result = self._add_speaker_diarization(result, input_path)

            # Save output
            self.callback.on_status("Saving transcript...")
            self._save_transcript(result, output_path, options)

            self.callback.on_complete(output_path)

        except Exception as e:
            self.callback.on_error(str(e))
        finally:
            # Cleanup temp files
            if self._is_youtube_url(input_path):
                try:
                    os.remove(input_path)
                except:
                    pass

    def _is_youtube_url(self, url):
        try:
            parsed = urlparse(url)
            return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc
        except:
            return False

    def _download_youtube_audio(self, url):
        temp_path = f"temp_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return temp_path

    def _add_speaker_diarization(self, whisper_result, audio_path):
        try:
            from pyannote.audio import Pipeline
            settings = Settings().current
            token = settings.get("hf_token")
            
            if not token:
                raise ValueError("No HuggingFace token found in settings")
                
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=token
            )
            
            # Combine whisper results with diarization
            # This is a simplified version - we'd want to do proper timestamp matching
            speakers = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })
            
            # Add speaker information to whisper segments
            for segment in whisper_result["segments"]:
                # Find matching speaker
                for speaker in speakers:
                    if (segment['start'] >= speaker['start'] and 
                        segment['end'] <= speaker['end']):
                        segment['speaker'] = speaker['speaker']
                        break
            
            return whisper_result
        except Exception as e:
            print(f"Diarization failed: {str(e)}")
            return whisper_result

    def _save_transcript(self, result, output_path, options):
        with open(output_path, "w", encoding="utf-8") as f:
            if options.get("include_timestamps"):
                for segment in result["segments"]:
                    timestamp = f"[{segment['start']:.2f}s - {segment['end']:.2f}s]"
                    speaker = f"[{segment.get('speaker', 'Unknown')}] " if options.get("use_diarization") else ""
                    f.write(f"{timestamp} {speaker}{segment['text']}\n")
            else:
                f.write(result["text"])

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
        
        # Initialize worker
        self.worker = TranscriptionWorker(self)
        
        self.setup_ui()
        self.check_initial_dependencies()

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
        
        ttk.Radiobutton(input_frame, text="Local File(s)", 
                       variable=self.input_type, value="file",
                       command=self.toggle_input_mode).pack(side="left")
        ttk.Radiobutton(input_frame, text="YouTube URL", 
                       variable=self.input_type, value="youtube",
                       command=self.toggle_input_mode).pack(side="left")
        
        # Files list
        self.files_frame = ttk.LabelFrame(parent, text="Files", padding="5")
        self.files_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.files_list = tk.Listbox(self.files_frame, selectmode=tk.EXTENDED)
        self.files_list.pack(fill="both", expand=True, side="left")

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
        ttk.Button(btn_frame, text="Remove Selected", 
                  command=self.remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_files).pack(side="left", padx=5)
        
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

    def get_output_filename(self, input_path, index=0):
        """Generate output filename based on settings"""
        if self.naming_mode.get() == "auto":
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

    def check_diarization(self):
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
        is_file = self.input_type.get() == "file"
        self.files_list["state"] = "normal" if is_file else "disabled"
        self.batch_processing.set(is_file)

    def add_files(self):
        if self.input_type.get() == "file":
            files = filedialog.askopenfilenames(
                filetypes=[("Audio/Video files", 
                          "*.mp3 *.wav *.mp4 *.avi *.mov *.mkv *.m4a *.webm")]
            )
            for file in files:
                if file not in self.input_paths:
                    self.input_paths.append(file)
                    self.files_list.insert(tk.END, os.path.basename(file))
        else:
            url = simpledialog.askstring("YouTube URL", "Enter YouTube URL:")
            if url:
                self.input_paths.append(url)
                self.files_list.insert(tk.END, url)

    def remove_selected(self):
        selected = self.files_list.curselection()
        for index in reversed(selected):
            self.files_list.delete(index)
            self.input_paths.pop(index)

    def clear_files(self):
        self.files_list.delete(0, tk.END)
        self.input_paths.clear()

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
    
        options = {
            "include_timestamps": self.timestamps.get(),
            "use_diarization": self.speaker_diarization.get(),
        }
    
        for idx, input_path in enumerate(self.input_paths):
            output_filename = self.get_output_filename(input_path, idx)
            output_path = os.path.join(self.output_path.get(), output_filename)
        
        # Check if file exists
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