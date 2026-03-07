"""
Velocity Spanish - Unified Social Media Upload Script
Uploads generated reels to all connected social media platforms
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add upload directory to Python path
upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

# Import individual uploaders - initialize as None first
upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None
upload_to_twitter = None
upload_to_vk = None
upload_to_telegram = None
upload_to_threads = None
upload_to_tiktok = None

# Try importing each uploader
try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError as e:
    print(f"[!] Facebook upload module not available: {e}")

try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError as e:
    print(f"[!] Instagram upload module not available: {e}")

try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError as e:
    print(f"[!] YouTube upload module not available: {e}")

try:
    from upload_twitter import upload_to_twitter as tw_upload
    upload_to_twitter = tw_upload
except ImportError as e:
    print(f"[!] Twitter upload module not available: {e}")

try:
    from upload_vk import upload_to_vk as vk_upload
    upload_to_vk = vk_upload
except ImportError as e:
    print(f"[!] VK upload module not available: {e}")

try:
    from upload_telegram import upload_to_telegram as tg_upload
    upload_to_telegram = tg_upload
except ImportError as e:
    print(f"[!] Telegram upload module not available: {e}")

try:
    from upload_threads import upload_to_threads as th_upload
    upload_to_threads = th_upload
except ImportError as e:
    print(f"[!] Threads upload module not available: {e}")

try:
    from upload_tiktok import upload_to_tiktok as tk_upload
    upload_to_tiktok = tk_upload
except ImportError as e:
    print(f"[!] TikTok upload module not available: {e}")


def get_latest_reel():
    """Find the most recently generated reel"""
    video_dir = Path("output/video")
    
    if not video_dir.exists():
        print("❌ No output/video directory found")
        return None
    
    # Find all final_reel.mp4 files
    reels = list(video_dir.glob("*/final_reel.mp4"))
    
    if not reels:
        print("❌ No reels found in output/video directory")
        return None
    
    # Sort by modification time (newest first)
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    
    # Get metadata
    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    
    return {
        "video_path": str(latest),
        "metadata": metadata,
        "category": metadata.get("category_english", "Spanish Learning"),
        "phrases": metadata.get("phrases", [])
    }


def generate_caption(phrases, category, platform="facebook"):
    """Generate social media caption from phrases - optimized per platform"""

    # Get first phrase for hook
    first_phrase = phrases[0] if phrases else {"english": "Learn Spanish", "spanish": "Aprende Español"}
    
    if platform == "facebook":
        # Longer, more engaging Facebook caption
        caption_lines = [
            f"🇪🇸 **Learn Spanish with Velocity Spanish!** 🇪🇸",
            f"",
            f"📚 Category: {category}",
            f"",
            f"🎯 Master Spanish one phrase at a time! Today's {category} lesson:",
            f""
        ]
        
        # Add all phrases with emojis
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, phrase in enumerate(phrases[:5], 0):
            emoji = emojis[i] if i < len(emojis) else f"{i+1}."
            caption_lines.append(f"{emoji} {phrase['english']}")
            caption_lines.append(f"   📍 {phrase['spanish']}")
            caption_lines.append(f"   🔊 [{phrase.get('pronunciation', '')}]")
            caption_lines.append("")
        
        # Call to action
        caption_lines.extend([
            f"💡 **Tip:** Repeat each phrase out loud 3 times!",
            f"👍 Like this video if you learned something new!",
            f"💬 Comment your favorite phrase below!",
            f"🔔 Follow for daily Spanish lessons!",
            f"",
            f"📖 **Pronunciation Guide:**",
            f"   The phonetic spelling in brackets helps you say it correctly!",
            f"",
        ])
        
        # Hashtags for Facebook
        hashtags = [
            "#LearnSpanish",
            "#SpanishLessons",
            "#SpanishForBeginners",
            "#LanguageLearning",
            "#SpanishVocabulary",
            "#VelocitySpanish",
            "#DailySpanish",
            "#SpanishGrammar",
            "#LearnLanguages",
            "#SpanishTeacher",
            "#SpeakSpanish",
            "#SpanishPractice",
            "#Bilingual",
            "#SpanishWords",
            "#LanguageTips"
        ]
        
        caption_lines.extend(hashtags)
        
    else:
        # Standard caption for other platforms
        caption_lines = [
            f"🇪🇸 Learn Spanish with Velocity Spanish! 🇪🇸",
            f"",
            f"Category: {category}",
            f"",
            f"Today's phrases:",
            f""
        ]
        
        for i, phrase in enumerate(phrases[:3], 1):
            caption_lines.append(f"{i}. {phrase['english']}")
            caption_lines.append(f"   → {phrase['spanish']}")
            caption_lines.append("")
        
        hashtags = [
            "#LearnSpanish",
            "#SpanishLessons",
            "#SpanishForBeginners",
            "#LanguageLearning",
            "#SpanishVocabulary",
            "#VelocitySpanish",
            "#DailySpanish",
            "#SpanishGrammar",
            "#LearnLanguages",
            "#SpanishTeacher"
        ]
        
        caption_lines.extend(hashtags)

    return "\n".join(caption_lines)


def upload_to_all_platforms(video_path, caption, category):
    """Upload to all configured social media platforms with comprehensive summary"""

    results = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "video": video_path,
        "uploads": {},
        "platforms_attempted": [],
        "platforms_successful": [],
        "platforms_skipped": [],
        "platforms_failed": []
    }

    print("\n" + "="*80)
    print("🚀 VELOCITY SPANISH - MULTI-PLATFORM UPLOAD")
    print("="*80)
    print(f"Video: {video_path}")
    print(f"Category: {category}")
    print(f"Caption length: {len(caption)} characters")
    print("="*80)

    # Check if video exists
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return results

    # Platform configuration: (name, function, display_name)
    platforms = [
        ("facebook", upload_to_facebook, "📘 Facebook"),
        ("instagram", upload_to_instagram, "📸 Instagram"),
        ("youtube", upload_to_youtube, "📺 YouTube"),
        ("twitter", upload_to_twitter, "🐦 Twitter/X"),
        ("vk", upload_to_vk, "🔵 VK (VKontakte)"),
        ("telegram", upload_to_telegram, "📧 Telegram"),
        ("threads", upload_to_threads, "🧵 Threads"),
        ("tiktok", upload_to_tiktok, "🎵 TikTok"),
    ]

    # Upload to each platform
    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)
        
        if upload_func:
            try:
                # Call upload function with appropriate parameters per platform
                upload_result = None
                
                if platform_name == "facebook":
                    upload_result = upload_func(
                        video_path=video_path,
                        description=caption,
                        title=f"Spanish: {category}"
                    )
                elif platform_name == "instagram":
                    upload_result = upload_func(
                        video_path=video_path,
                        caption=caption,
                        is_story=False
                    )
                elif platform_name == "youtube":
                    upload_result = upload_func(
                        video_path=video_path,
                        title=f"Spanish: {category}",
                        description=caption
                    )
                elif platform_name == "twitter":
                    upload_result = upload_func(
                        video_path=video_path,
                        text=caption
                    )
                elif platform_name == "vk":
                    upload_result = upload_func(
                        video_path=video_path,
                        caption=caption,
                        name=f"Spanish: {category}"
                    )
                elif platform_name == "telegram":
                    upload_result = upload_func(
                        video_path=video_path,
                        caption=caption
                    )
                elif platform_name == "threads":
                    upload_result = upload_func(
                        video_path=video_path,
                        text=caption
                    )
                elif platform_name == "tiktok":
                    upload_result = upload_func(
                        video_path=video_path,
                        description=caption
                    )
                
                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                    print(f"✅ {display_name} upload successful")
                else:
                    results["uploads"][platform_name] = {"status": "failed", "error": "Upload function returned None"}
                    results["platforms_failed"].append(platform_name)
                    print(f"❌ {display_name} upload failed: No result returned")
                
            except Exception as e:
                error_msg = str(e)
                results["uploads"][platform_name] = {"status": "failed", "error": error_msg}
                results["platforms_failed"].append(platform_name)
                print(f"❌ {display_name} upload failed: {error_msg}")
        else:
            print(f"⚠️  {display_name} upload skipped (module not available / no credentials)")
            results["uploads"][platform_name] = {"status": "skipped", "reason": "Module not available"}
            results["platforms_skipped"].append(platform_name)

    # ===== BEAUTIFUL SUMMARY =====
    print("\n" + "="*80)
    print("📊 UPLOAD SUMMARY")
    print("="*80)
    
    total_attempted = len(results["platforms_attempted"])
    successful_count = len(results["platforms_successful"])
    failed_count = len(results["platforms_failed"])
    skipped_count = len(results["platforms_skipped"])
    
    print(f"\n📈 Overall Status:")
    print(f"   ├─ Total Platforms: {total_attempted}")
    print(f"   ├─ ✅ Successful: {successful_count}")
    print(f"   ├─ ❌ Failed: {failed_count}")
    print(f"   └─ ⚠️  Skipped: {skipped_count}")
    
    # Success rate
    if total_attempted > 0:
        success_rate = (successful_count / total_attempted) * 100
        print(f"\n🎯 Success Rate: {success_rate:.0f}%")
    
    # Detailed breakdown
    if results["platforms_successful"]:
        print(f"\n✅ SUCCESSFUL UPLOADS ({len(results['platforms_successful'])}):")
        for platform in results["platforms_successful"]:
            platform_data = results["uploads"].get(platform, {})
            video_id = platform_data.get("video_id", "N/A")
            print(f"   ✅ {platform.upper()}: Success (Video ID: {video_id})")
    
    if results["platforms_failed"]:
        print(f"\n❌ FAILED UPLOADS ({len(results['platforms_failed'])}):")
        for platform in results["platforms_failed"]:
            platform_data = results["uploads"].get(platform, {})
            error = platform_data.get("error", "Unknown error")
            print(f"   ❌ {platform.upper()}: Failed - {error[:80]}...")
    
    if results["platforms_skipped"]:
        print(f"\n⚠️  SKIPPED PLATFORMS ({len(results['platforms_skipped'])}):")
        skipped_list = ", ".join([p.upper() for p in results["platforms_skipped"]])
        print(f"   ⚠️  {skipped_list}")
        print(f"   💡 Add credentials to enable these platforms")
    
    print("\n" + "="*80)
    
    # Save upload results
    results_file = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved: {results_file}")
    print("="*80)

    return results


def main():
    """Main upload workflow"""

    print("\n" + "="*80)
    print("🇪🇸 VELOCITY SPANISH - AUTOMATED UPLOAD 🇪🇸")
    print("="*80)

    # Get latest reel
    reel = get_latest_reel()

    if not reel:
        print("\n❌ No reel found! Run facebook_reels_automation.py first.")
        sys.exit(1)

    print(f"\n✅ Found latest reel:")
    print(f"   Category: {reel['category']}")
    print(f"   Video: {reel['video_path']}")
    print(f"   Phrases: {len(reel['phrases'])}")

    # Generate caption (standard version for display)
    caption = generate_caption(reel['phrases'], reel['category'], platform="facebook")
    print(f"\n📝 Generated caption ({len(caption)} chars):")
    print("-"*80)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("-"*80)

    # Upload to all platforms (pass phrases in results for platform-specific captions)
    results = upload_to_all_platforms(
        reel['video_path'],
        caption,
        reel['category']
    )
    
    # Add phrases to results for reference
    results["phrases"] = reel['phrases']

    # Exit with appropriate code
    successful = len(results.get("platforms_successful", []))
    failed = len(results.get("platforms_failed", []))
    skipped = len(results.get("platforms_skipped", []))
    
    if successful > 0:
        print(f"\n✅ Upload complete! {successful} platform(s) successful.")
        if skipped > 0:
            print(f"💡 {skipped} platform(s) skipped - add credentials to enable them")
        sys.exit(0)
    elif failed > 0:
        print(f"\n⚠️  All attempted uploads failed ({failed} failed, {skipped} skipped).")
        print("💡 Check the error messages above and verify your credentials")
        sys.exit(1)
    else:
        print(f"\n⚠️  All uploads skipped ({skipped} skipped).")
        print("💡 Add credentials in GitHub Secrets to enable uploads")
        sys.exit(1)


if __name__ == "__main__":
    main()
