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

# Import individual uploaders
try:
    from upload_facebook import upload_to_facebook
except ImportError as e:
    upload_to_facebook = None
    print(f"[!] Facebook upload module not available: {e}")

try:
    from upload_instagram import upload_to_instagram
except ImportError as e:
    upload_instagram = None
    print(f"[!] Instagram upload module not available: {e}")


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


def generate_caption(phrases, category):
    """Generate social media caption from phrases"""
    
    # Create caption with first few phrases
    caption_lines = [
        f"🇪🇸 Learn Spanish with Velocity Spanish! 🇪🇸",
        f"",
        f"Category: {category}",
        f"",
        f"Today's phrases:",
        f""
    ]
    
    # Add first 3 phrases (keep caption concise)
    for i, phrase in enumerate(phrases[:3], 1):
        caption_lines.append(f"{i}. {phrase['english']}")
        caption_lines.append(f"   → {phrase['spanish']}")
        caption_lines.append("")
    
    # Add hashtags
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
    """Upload to all configured social media platforms"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "video": video_path,
        "uploads": {}
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
    
    # Upload to Facebook
    print("\n📘 FACEBOOK UPLOAD...")
    if upload_to_facebook:
        try:
            fb_result = upload_to_facebook(video_path, caption, title=f"Spanish: {category}")
            results["uploads"]["facebook"] = fb_result
            print("✅ Facebook upload successful")
        except Exception as e:
            print(f"❌ Facebook upload failed: {e}")
            results["uploads"]["facebook"] = {"status": "failed", "error": str(e)}
    else:
        print("⚠️  Facebook upload skipped (module not available)")
        results["uploads"]["facebook"] = {"status": "skipped"}
    
    # Upload to Instagram
    print("\n📸 INSTAGRAM UPLOAD...")
    if upload_instagram:
        try:
            ig_result = upload_to_instagram(video_path, caption, is_story=False)
            results["uploads"]["instagram"] = ig_result
            print("✅ Instagram upload successful")
        except Exception as e:
            print(f"❌ Instagram upload failed: {e}")
            results["uploads"]["instagram"] = {"status": "failed", "error": str(e)}
    else:
        print("⚠️  Instagram upload skipped (module not available)")
        results["uploads"]["instagram"] = {"status": "skipped"}
    
    # Summary
    print("\n" + "="*80)
    print("📊 UPLOAD SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results["uploads"].values() if r.get("status") == "success")
    total = len(results["uploads"])
    
    print(f"Successful: {successful}/{total}")
    
    for platform, result in results["uploads"].items():
        status = result.get("status", "unknown")
        if status == "success":
            print(f"  ✅ {platform.upper()}: Success")
        elif status == "failed":
            print(f"  ❌ {platform.upper()}: Failed - {result.get('error', 'Unknown error')}")
        else:
            print(f"  ⚠️  {platform.upper()}: {status}")
    
    print("="*80)
    
    # Save upload results
    results_file = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved: {results_file}")
    
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
    
    # Generate caption
    caption = generate_caption(reel['phrases'], reel['category'])
    print(f"\n📝 Generated caption ({len(caption)} chars):")
    print("-"*80)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("-"*80)
    
    # Upload to all platforms
    results = upload_to_all_platforms(
        reel['video_path'],
        caption,
        reel['category']
    )
    
    # Exit with appropriate code
    successful = sum(1 for r in results["uploads"].values() if r.get("status") == "success")
    if successful > 0:
        print(f"\n✅ Upload complete! {successful} platform(s) successful.")
        sys.exit(0)
    else:
        print(f"\n❌ All uploads failed or were skipped.")
        sys.exit(1)


if __name__ == "__main__":
    main()
