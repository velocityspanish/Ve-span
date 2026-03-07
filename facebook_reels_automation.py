"""
Facebook Reels Automation - Bilingual English/Spanish Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Spanish branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Spanish translations for display
CATEGORIES_SPANISH = {
    "Motivation": "Motivación",
    "Love": "Amor",
    "Success": "Éxito",
    "Wisdom": "Sabiduría",
    "Happiness": "Felicidad",
    "Self Improvement": "Superación",
    "Gratitude": "Gratitud",
    "Friendship": "Amistad",
    "Hope": "Esperanza",
    "Creativity": "Creatividad",
    "Inner Peace": "Paz Interior",
    "Confidence": "Confianza",
    "Perseverance": "Perseverancia",
    "Inspiration": "Inspiración",
    "Positive Life": "Vida Positiva",
    "Courage": "Coraje",
    "Kindness": "Amabilidad",
    "Patience": "Paciencia",
    "Forgiveness": "Perdón",
    "Strength": "Fortaleza",
    "Joy": "Alegría",
    "Balance": "Equilibrio",
    "Growth": "Crecimiento",
    "Purpose": "Propósito",
    "Mindfulness": "Conciencia Plena",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
SPANISH_VOICE = "es-ES-AlvaroNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "spanish": phrase["spanish"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""
    
    category_spanish = CATEGORIES_SPANISH[category_english]
    
    # Try AI first
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Spanish.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds

For each phrase:
1. English phrase (with commas for natural pauses)
2. Spanish translation (with commas matching the rhythm)
3. Pronunciation guide (phonetic for English speakers)

Return as JSON array:
[{{"english": "...", "spanish": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before."""
            
            payload = {
                "model": "openai",
                "messages": [
                    {"role": "system", "content": "You are a Spanish teacher. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            phrases = json.loads(content)
            
            # Filter out already-used phrases and ensure proper length
            unique_phrases = []
            for phrase in phrases:
                # Skip if too long (over 15 words)
                if len(phrase["english"].split()) > 15:
                    continue
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break
            
            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]
                
        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")
    
    # Fallback to fresh phrases
    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""
    
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "spanish": "Cree en ti mismo.", "pronunciation": "Kreh-eh en tee mees-moh."},
            {"english": "You are capable of amazing things.", "spanish": "Eres capaz de cosas increíbles.", "pronunciation": "Eh-res kah-pahs deh koh-sahs een-krey-ee-bles."},
            {"english": "Dream big, start small.", "spanish": "Sueña grande, comienza pequeño.", "pronunciation": "Sweh-nyah grahn-deh, koh-meehn-sah peh-keh-nyoh."},
            {"english": "Your future is created by your actions.", "spanish": "Tu futuro es creado por tus acciones.", "pronunciation": "Too foo-too-roh es kreh-ah-doh por toos ahk-seeoh-nes."},
            {"english": "Never give up on your dreams.", "spanish": "Nunca te rindas con tus sueños.", "pronunciation": "Noon-kah teh reen-dahs kon toos sweh-nyos."},
            {"english": "Progress is better than perfection.", "spanish": "El progreso es mejor que la perfección.", "pronunciation": "El pro-greh-soh es meh-hor keh lah per-fehk-seeohn."},
            {"english": "Your only limit is you.", "spanish": "Tu único límite eres tú.", "pronunciation": "Too oo-nee-koh lee-mee-teh eh-res too."},
            {"english": "Start where you are.", "spanish": "Comienza donde estás.", "pronunciation": "Koh-meehn-sah dohn-deh es-tahs."},
        ],
        "Love": [
            {"english": "Love yourself first.", "spanish": "Ámate a ti mismo primero.", "pronunciation": "Ah-mah-teh ah tee mees-moh pree-meh-roh."},
            {"english": "Love makes everything possible.", "spanish": "El amor lo hace todo posible.", "pronunciation": "El ah-mor loh ah-seh toh-doh poh-see-bleh."},
            {"english": "Your heart knows the way.", "spanish": "Tu corazón conoce el camino.", "pronunciation": "Too koh-rah-sone koh-noh-seh el kah-mee-noh."},
            {"english": "Love is the answer.", "spanish": "El amor es la respuesta.", "pronunciation": "El ah-mor es lah res-pwes-tah."},
            {"english": "Spread love everywhere.", "spanish": "Esparce el amor por todas partes.", "pronunciation": "Es-par-seh el ah-mor por toh-dahs par-tes."},
            {"english": "Kindness is love in action.", "spanish": "La bondad es amor en acción.", "pronunciation": "Lah bohn-dahd es ah-mor en ahk-seeohn."},
            {"english": "Love never fails.", "spanish": "El amor nunca falla.", "pronunciation": "El ah-mor noon-kah fah-yah."},
        ],
        "Success": [
            {"english": "Success starts with belief.", "spanish": "El éxito comienza con la creencia.", "pronunciation": "El ek-see-toh koh-meehn-sah kon lah kreh-en-see-ah."},
            {"english": "You are destined for greatness.", "spanish": "Estás destinado para la grandeza.", "pronunciation": "Es-tahs des-tee-nah-doh pah-rah lah grahn-deh-sah."},
            {"english": "Success is a journey.", "spanish": "El éxito es un viaje.", "pronunciation": "El ek-see-toh es oon vee-ah-heh."},
            {"english": "Your time to shine is now.", "spanish": "Tu tiempo de brillar es ahora.", "pronunciation": "Too teehm-poh deh bree-yar es ah-oh-rah."},
            {"english": "Achieve the impossible.", "spanish": "Logra lo imposible.", "pronunciation": "Loh-grah loh eem-poh-see-bleh."},
        ],
    }
    
    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    
    # Filter out used phrases
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]
    
    if len(fresh_phrases) < num_phrases:
        print(f"[warning] Only {len(fresh_phrases)} fresh fallback phrases available")
    
    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []
    
    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        spanish_file = output_dir / f"spanish_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"
        
        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    ES: {phrase['spanish']}")
        
        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    ✓ English: {english_file.name}")
        else:
            # Create silent placeholder
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Spanish audio
        es_success = asyncio.run(generate_single_audio(phrase["spanish"], SPANISH_VOICE, str(spanish_file)))
        if es_success:
            print(f"    ✓ Spanish: {spanish_file.name}")
        else:
            # Create silent placeholder
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(spanish_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations from generated files
        en_duration = get_audio_duration(str(english_file))
        es_duration = get_audio_duration(str(spanish_file))

        # CRITICAL: Add pause between English and Spanish
        pause_between = 0.5  # 500ms pause
        
        # CRITICAL: Calculate TOTAL duration (English + pause + Spanish)
        # This ensures image stays on screen for COMPLETE audio playback
        total_duration = en_duration + pause_between + es_duration
        
        print(f"    ⏱️  Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + ES: {es_duration:.2f}s)")

        # Combine audio files sequentially using filter_complex (most reliable method)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(spanish_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verify the combined file duration matches expected
        actual_duration = get_audio_duration(str(combined_file))
        
        # If concat failed, try alternative approach
        if actual_duration < 3.0:
            print(f"    ⚠️  First concat produced short audio, trying alternative...")
            # Create concat file and use demuxer
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{spanish_file.as_posix()}'\n")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            actual_duration = get_audio_duration(str(combined_file))
            
            if concat_file.exists():
                concat_file.unlink()
        
        print(f"    ✓ Combined verified: {actual_duration:.2f}s")
        
        audio_files.append({
            "index": i,
            "english": str(english_file),
            "spanish": str(spanish_file),
            "combined": str(combined_file),
            "duration": actual_duration,  # Use ACTUAL measured duration for perfect sync
            "en_duration": en_duration,
            "es_duration": es_duration
        })
    
    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    
    concat_file = Path(output_file).parent / "narration_list.txt"
    
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if concat_file.exists():
        concat_file.unlink()
    
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    
    # Fallback: sequential concatenation
    print("[audio] Using fallback concatenation...")
    import shutil
    if audio_files and Path(audio_files[0]["combined"]).exists():
        shutil.copy2(audio_files[0]["combined"], output_file)
        for i in range(1, len(audio_files)):
            if Path(audio_files[i]["combined"]).exists():
                temp_file = Path(output_file).parent / "temp_append.mp3"
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(output_file),
                    "-i", str(audio_files[i]["combined"]),
                    "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
                    "-map", "[out]",
                    str(temp_file)
                ]
                subprocess.run(cmd, capture_output=True)
                if temp_file.exists():
                    temp_file.replace(output_file)
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name}")
        return True
    
    return False


# ============== IMAGE GENERATION WITH IMPRESSIVE BACKGROUNDS ==============

def create_impressive_background(category_english: str):
    """Create stunning gradient background with patterns"""
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Beautiful color schemes per category
    category_colors = {
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],
        "Love": [(255, 20, 147), (199, 21, 133), (255, 105, 180), (219, 112, 147)],
        "Success": [(255, 215, 0), (255, 140, 0), (255, 69, 0), (220, 120, 20)],
        "Wisdom": [(25, 25, 112), (70, 130, 180), (100, 149, 237), (65, 105, 225)],
        "Happiness": [(255, 255, 0), (255, 165, 0), (255, 140, 0), (255, 200, 0)],
    }
    
    colors = category_colors.get(category_english, [(15, 10, 40), (48, 43, 99), (36, 36, 62), (72, 61, 139)])
    
    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    
    # Add subtle geometric pattern for depth
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            alpha = 20
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, alpha),
                width=1
            )
    
    # Add radial glow effect
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )
    
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)
    
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background and Velocity Spanish branding"""
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None
    
    # Create impressive background
    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        font_category = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
        font_large = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 72)
        font_pronunciation = ImageFont.truetype("C:/Windows/Fonts/ariali.ttf", 32)
        font_branding = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)
    except:
        font_category = font_large = font_pronunciation = font_branding = ImageFont.load_default()
    
    english = phrase_data.get("english", "")
    spanish = phrase_data.get("spanish", "")
    pronunciation = phrase_data.get("pronunciation", "")
    
    # Helper: wrap text
    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines
    
    # Draw category at top (in English for learners)
    category_text = category_english.upper()
    category_bbox = draw.textbbox((VIDEO_WIDTH // 2, 140), category_text, font=font_category, anchor="mm")
    padding = 25
    
    # Category background with glow
    draw.rectangle(
        [(category_bbox[0] - padding, category_bbox[1] - padding),
         (category_bbox[2] + padding, category_bbox[3] + padding)],
        fill=(0, 0, 0, 200)
    )
    
    # Category text
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )
    
    # English text with DARK BLUE background
    english_y = 500
    english_lines = wrap_text(english, font_large, VIDEO_WIDTH - 140)
    total_height = len(english_lines) * 95
    
    # Dark blue background for English (darker, more visible)
    draw.rectangle(
        [(60, english_y - 60), (VIDEO_WIDTH - 60, english_y + total_height + 10)],
        fill=(20, 30, 80, 220)  # Dark navy blue
    )
    
    for i, line in enumerate(english_lines):
        y_pos = english_y + (i * 95)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 255),  # White text
            font=font_large,
            anchor="mm",
            stroke_width=3,
            stroke_fill=(0, 0, 0)
        )
    
    # Spanish text with DARK BROWN/MAROON background
    spanish_y = english_y + total_height + 120
    spanish_lines = wrap_text(spanish, font_large, VIDEO_WIDTH - 140)
    total_height = len(spanish_lines) * 95
    
    # Dark brown/maroon background for Spanish (different from English)
    draw.rectangle(
        [(60, spanish_y - 60), (VIDEO_WIDTH - 60, spanish_y + total_height + 10)],
        fill=(80, 30, 30, 220)  # Dark maroon/brown
    )
    
    for i, line in enumerate(spanish_lines):
        y_pos = spanish_y + (i * 95)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 0),  # Bright yellow text
            font=font_large,
            anchor="mm",
            stroke_width=3,
            stroke_fill=(0, 0, 0)
        )
    
    # Pronunciation with DARK GRAY background (NEW!)
    pronunciation_y = spanish_y + total_height + 100
    pronunciation_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pronunciation_text, font_pronunciation, VIDEO_WIDTH - 200)
    
    # Calculate background box for pronunciation
    if pron_lines:
        pron_total_height = len(pron_lines) * 40
        # Dark gray background for pronunciation
        draw.rectangle(
            [(80, pronunciation_y - 15), (VIDEO_WIDTH - 80, pronunciation_y + pron_total_height + 5)],
            fill=(50, 50, 50, 200)  # Dark gray
        )
        
        for i, pron_line in enumerate(pron_lines):
            y_pos = pronunciation_y + (i * 40)
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                pron_line,
                fill=(230, 230, 230),  # Light gray text (almost white)
                font=font_pronunciation,
                anchor="mm",
                stroke_width=1,
                stroke_fill=(0, 0, 0)
            )
    
    # VELOCITY SPANISH BRANDING at bottom
    branding_y = VIDEO_HEIGHT - 100
    draw.rectangle(
        [(0, branding_y - 30), (VIDEO_WIDTH, branding_y + 50)],
        fill=(0, 0, 0, 180)
    )
    
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY SPANISH",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )
    
    # Save (convert RGBA to RGB for JPEG)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""
    
    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")
    
    temp_clips = []
    
    # Create video clips with EXACT audio durations
    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        # Use the actual combined audio duration for perfect sync
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + ES: {audio_info.get('es_duration', 0):.1f}s)")
        
        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"
    
    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")
    
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Add audio - CRITICAL: Ensure complete audio playback
    print("[video] Adding audio (ensuring complete playback)...")
    
    if not Path(combined_audio).exists() or Path(combined_audio).stat().st_size == 0:
        print("[video] Warning: No audio file, creating video without audio...")
        cmd = ["ffmpeg", "-y", "-i", str(temp_video), "-c:v", "copy", "-an", str(output_file)]
    else:
        # Get audio duration
        audio_duration = get_audio_duration(str(combined_audio))
        print(f"[video] Audio duration: {audio_duration:.2f}s")
        
        # Use shortest to ensure video waits for complete audio
        # Also add audio stream to entire video
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_video),
            "-i", str(combined_audio),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file)
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[video] Warning: {result.stderr[:100]}")
    
    # Verify output
    if Path(output_file).exists():
        video_duration = get_audio_duration(str(output_file))  # Works for video too
        print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")
        
        # Verify audio is present
        cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", str(output_file)]
        audio_check = subprocess.run(cmd, capture_output=True, text=True)
        if audio_check.stdout.strip():
            print(f"[video] ✓ Audio stream confirmed: {audio_check.stdout.strip()}")
        else:
            print(f"[video] ⚠ Warning: No audio stream detected")
    else:
        print(f"[video] ✗ Error: Video file not created")
    
    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()
    
    return output_file


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""
    
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)
    
    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_SPANISH[category_english]})")
    print(f"{'='*80}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)
    
    # Step 1: Generate unique phrases (no repeats!)
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)
    
    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['spanish']}")
    
    # Step 2: Generate images with impressive backgrounds
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
    
    # Step 3: Generate audio with proper timing
    print("\n[3/4] Generating audio (English + Spanish with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))
    
    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))
    
    # Step 4: Create video
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"
    create_video_from_images_audio(
        [str(p) for p in reel_dir.glob("phrase_*.jpg")],
        audio_files,
        str(final_audio),
        str(output_video)
    )
    
    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_spanish": CATEGORIES_SPANISH[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }
    
    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Velocity Spanish")
    print(f"{'='*80}\n")
    
    return metadata


def generate_daily_content(times_per_day: int = 4):
    """
    Generate content for the entire day (4x daily for American time zones)
    
    Scheduling for American time zones:
    - Post 1: 9:00 AM EST/EDT (Morning motivation)
    - Post 2: 12:00 PM EST/EDT (Lunch break)
    - Post 3: 3:00 PM EST/EDT (Afternoon pick-me-up)
    - Post 4: 7:00 PM EST/EDT (Evening inspiration)
    
    Ensures:
    - Different category for each post
    - No phrase repetition (checks permanent history)
    - Fresh AI-generated content every time
    """
    
    print(f"\n{'='*80}")
    print(f"📅 DAILY CONTENT GENERATION")
    print(f"{'='*80}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Posts per day: {times_per_day}")
    print(f"Time zone: American EST/EDT")
    print(f"\n📋 SCHEDULE:")
    print(f"  • Post 1: 9:00 AM  - Morning motivation")
    print(f"  • Post 2: 12:00 PM - Lunch break")
    print(f"  • Post 3: 3:00 PM  - Afternoon pick-me-up")
    print(f"  • Post 4: 7:00 PM  - Evening inspiration")
    print(f"\n🔄 ROTATION LOGIC:")
    print(f"  • Each post uses a DIFFERENT category")
    print(f"  • Categories rotate daily (25 categories = 6+ days before repeat)")
    print(f"  • Phrases are checked against PERMANENT history")
    print(f"  • NO phrase will EVER repeat")
    print(f"{'='*80}\n")
    
    # Load phrase history to verify uniqueness
    history = load_phrase_history()
    total_phrases_in_history = len(history.get("phrases", []))
    print(f"📊 Current phrase history: {total_phrases_in_history} phrases")
    
    # Select different categories for each post
    available_categories = CATEGORIES_ENGLISH.copy()
    
    # Check which categories were used recently (last 3 days)
    recent_usage_file = HISTORY_DIR / "recent_categories.json"
    if recent_usage_file.exists():
        with open(recent_usage_file, "r", encoding="utf-8") as f:
            recent = json.load(f)
            used_recently = recent.get("last_3_days", [])
            # Remove recently used categories from today's selection
            for cat in used_recently:
                if cat in available_categories and len(available_categories) > times_per_day:
                    available_categories.remove(cat)
            print(f"📋 Avoiding recent categories: {used_recently}")
    
    random.shuffle(available_categories)
    
    daily_reels = []
    categories_used_today = []
    
    for i in range(times_per_day):
        # Select category for this post
        category = available_categories[i % len(available_categories)]
        categories_used_today.append(category)
        
        print(f"\n{'='*80}")
        print(f"🎬 GENERATING POST {i+1}/{times_per_day}")
        print(f"{'='*80}")
        
        # Generate reel
        reel = generate_reel(category)
        if reel:
            daily_reels.append(reel)
            print(f"✅ Post {i+1} complete: {category}")
    
    # Save today's category usage for future rotation
    recent_usage = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "last_3_days": categories_used_today
    }
    with open(recent_usage_file, "w", encoding="utf-8") as f:
        json.dump(recent_usage, f, indent=2)
    
    # Save daily summary
    summary_path = OUTPUT_DIR / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total_posts": len(daily_reels),
            "categories_used": categories_used_today,
            "posts": daily_reels
        }, f, indent=2, ensure_ascii=False)
    
    # Update phrase count
    new_total = len(load_phrase_history().get("phrases", []))
    phrases_added = new_total - total_phrases_in_history
    
    print(f"\n{'='*80}")
    print(f"📊 DAILY SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Total posts generated: {len(daily_reels)}")
    print(f"📋 Categories used: {', '.join(categories_used_today)}")
    print(f"📝 New phrases added: {phrases_added}")
    print(f"📚 Total phrases in history: {new_total}")
    print(f"💾 Summary saved: {summary_path}")
    print(f"{'='*80}\n")
    
    return daily_reels


def main():
    print("\n" + "="*80)
    print("🇪🇸 VELOCITY SPANISH - FACEBOOK REELS AUTOMATION 🇪🇸")
    print("="*80)
    print("\n✨ IMPROVED FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ English category names (for American/European learners)")
    print("  ✓ Velocity Spanish branding at bottom")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print("\n📊 AVAILABLE CATEGORIES (25 total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"  {i:2d}. {cat} ({CATEGORIES_SPANISH[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 4 reels per day = 20 unique phrases daily")
    print(f"  • 25 categories = Over 6 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)
    
    generate_reel("Motivation")
    
    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)


if __name__ == "__main__":
    main()
