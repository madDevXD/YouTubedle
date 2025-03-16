import streamlit as st
import yt_dlp
import os
import uuid
import base64
from pathlib import Path

st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="📺",
    layout="centered",
)

# Add custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem;
        max-width: 800px;
        margin: 0 auto;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .download-btn {
        background-color: #ff0000;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        font-weight: bold;
    }
    .title {
        color: #ff0000;
        font-size: 2.5rem;
        text-align: center;
    }
    .subtitle {
        color: #666;
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>YouTube Downloader</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Download YouTube videos and audio in different formats and qualities</p>", unsafe_allow_html=True)

# Create a temp directory for downloads if it doesn't exist
TEMP_DIR = Path("temp_downloads")
TEMP_DIR.mkdir(exist_ok=True)

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        st.error(f"Error fetching video information: {str(e)}")
        return None

def get_download_link(file_path, link_text):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    file_name = os.path.basename(file_path)
    href = f'<a href="data:file/octet-stream;base64,{b64}" download="{file_name}" class="download-btn">{link_text}</a>'
    return href

def download_video(url, format_id, output_path):
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return False

def download_audio(url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        st.error(f"Error downloading audio: {str(e)}")
        return False

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    if size_bytes is None:
        return "Unknown"
    
    size_bytes = float(size_bytes)
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"

def get_video_formats(info):
    formats = []
    
    # Get available formats
    for f in info.get('formats', []):
        format_id = f.get('format_id', '')
        extension = f.get('ext', '')
        format_note = f.get('format_note', '')
        resolution = f.get('resolution', '')
        filesize = format_size(f.get('filesize'))
        vcodec = f.get('vcodec', '')
        acodec = f.get('acodec', '')
        
        # Skip formats with no video
        if vcodec == 'none' and not (extension == 'mp3' or acodec != 'none'):
            continue
            
        format_name = f"{resolution} ({extension})"
        if format_note:
            format_name += f" - {format_note}"
        format_name += f" - {filesize}"
        
        formats.append({
            'format_id': format_id,
            'format_name': format_name,
            'extension': extension,
            'resolution': resolution,
            'filesize': filesize
        })
    
    # Sort formats by resolution (highest first)
    formats.sort(key=lambda x: x['resolution'], reverse=True)
    return formats

# URL input
url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

if url:
    with st.spinner("Fetching video information..."):
        info = get_video_info(url)
    
    if info:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(info.get('thumbnail', ''), use_column_width=True)
        
        with col2:
            st.markdown(f"### {info.get('title', 'Unknown Title')}")
            st.markdown(f"**Channel:** {info.get('uploader', 'Unknown')}")
            st.markdown(f"**Duration:** {info.get('duration_string', 'Unknown')}")
            st.markdown(f"**Views:** {info.get('view_count', 'Unknown')}")
        
        st.markdown("---")
        
        # Get video formats
        formats = get_video_formats(info)
        
        # Download options
        download_option = st.radio(
            "Select download option:",
            ["Video", "Audio (MP3)"]
        )
        
        if download_option == "Video":
            # Create a list of format options
            format_options = [f"{format['format_name']}" for format in formats]
            
            if format_options:
                selected_format = st.selectbox("Select video format:", format_options)
                selected_format_id = formats[format_options.index(selected_format)]['format_id']
                
                if st.button("Download Video"):
                    # Create a unique filename
                    file_uuid = uuid.uuid4().hex[:8]
                    extension = formats[format_options.index(selected_format)]['extension']
                    safe_title = "".join(c for c in info.get('title', 'video') if c.isalnum() or c in ' -_').strip()
                    output_path = str(TEMP_DIR / f"{safe_title}_{file_uuid}.{extension}")
                    
                    with st.spinner("Downloading video..."):
                        if download_video(url, selected_format_id, output_path):
                            st.success("Download complete!")
                            st.markdown(get_download_link(output_path, "Download Video"), unsafe_allow_html=True)
                            st.info("Note: The download link will expire after you close this app or refresh the page.")
            else:
                st.warning("No video formats available for this URL.")
        
        else:  # Audio (MP3)
            if st.button("Download MP3"):
                # Create a unique filename
                file_uuid = uuid.uuid4().hex[:8]
                safe_title = "".join(c for c in info.get('title', 'audio') if c.isalnum() or c in ' -_').strip()
                output_path = str(TEMP_DIR / f"{safe_title}_{file_uuid}.%(ext)s")
                
                with st.spinner("Converting and downloading audio..."):
                    if download_audio(url, output_path):
                        # Find the created MP3 file (extension was added by yt-dlp)
                        mp3_path = list(TEMP_DIR.glob(f"{safe_title}_{file_uuid}*.mp3"))[0]
                        st.success("Download complete!")
                        st.markdown(get_download_link(str(mp3_path), "Download MP3"), unsafe_allow_html=True)
                        st.info("Note: The download link will expire after you close this app or refresh the page.")
    else:
        st.error("Could not fetch video information. Please check the URL and try again.")

# Add footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and yt-dlp")

# Delete temporary files when the app is closed
def delete_temp_files():
    for file in TEMP_DIR.glob("*"):
        try:
            file.unlink()
        except:
            pass

# Register the cleanup function
import atexit
atexit.register(delete_temp_files)
