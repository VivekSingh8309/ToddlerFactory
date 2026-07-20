print("Testing YouTube backend...")

try:
    from services.youtube_backend import YouTubeUploader
    print("✓ Imported YouTubeUploader")
except Exception as e:
    print("✗ Import failed")
    print(e)
    raise

try:
    uploader = YouTubeUploader()
    print("✓ Authentication successful")
except Exception as e:
    print("✗ Authentication failed")
    print(e)