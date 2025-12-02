#!/bin/bash
# =============================================================================
# Create macOS .icns Icon File
# =============================================================================
# Converts PNG icon to macOS .icns format using iconutil.
# This script should be run on macOS.
#
# Usage:
#   ./scripts/create-icns.sh
#
# Input:
#   src/cosmetics_records/resources/icons/icon-256.png
#
# Output:
#   src/cosmetics_records/resources/icons/icon.icns
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ICONS_DIR="$PROJECT_ROOT/src/cosmetics_records/resources/icons"

SOURCE_PNG="$ICONS_DIR/icon-256.png"
OUTPUT_ICNS="$ICONS_DIR/icon.icns"
ICONSET_DIR="$ICONS_DIR/AppIcon.iconset"

echo "=== Creating macOS .icns Icon ==="

# Check if we're on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Warning: This script should be run on macOS for best results."
    echo "On other platforms, the .icns file won't be created."
    exit 0
fi

# Check source file exists
if [ ! -f "$SOURCE_PNG" ]; then
    echo "Error: Source PNG not found: $SOURCE_PNG"
    exit 1
fi

# Create iconset directory
rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

# Generate all required sizes using sips
echo "Generating icon sizes..."

# Standard sizes for macOS icons
sips -z 16 16     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16.png" > /dev/null
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" > /dev/null
sips -z 32 32     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32.png" > /dev/null
sips -z 64 64     "$SOURCE_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" > /dev/null
sips -z 128 128   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128.png" > /dev/null
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" > /dev/null
sips -z 256 256   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256.png" > /dev/null
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" > /dev/null
sips -z 512 512   "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512.png" > /dev/null
sips -z 1024 1024 "$SOURCE_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" > /dev/null 2>&1 || \
    cp "$SOURCE_PNG" "$ICONSET_DIR/icon_512x512@2x.png"  # Use 256 if 1024 fails

# Create .icns file
echo "Creating .icns file..."
iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_ICNS"

# Clean up iconset directory
rm -rf "$ICONSET_DIR"

echo "=== Icon Created Successfully ==="
echo "Output: $OUTPUT_ICNS"
