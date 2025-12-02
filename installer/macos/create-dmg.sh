#!/bin/bash
# =============================================================================
# Cosmetics Records - macOS DMG Creator
# =============================================================================
# Creates a distributable DMG file with:
#   - Application bundle
#   - Applications folder symlink (drag-to-install)
#   - Custom window size and icon positions
#
# Requirements:
#   - macOS with hdiutil (built-in)
#   - create-dmg (brew install create-dmg) - optional but recommended
#   - CosmeticsRecords.app in dist/ directory
#
# Usage:
#   ./installer/macos/create-dmg.sh [version]
#
# Output:
#   dist/CosmeticsRecords-macOS-{arch}-Setup.dmg
# =============================================================================

set -e

# Configuration
APP_NAME="Cosmetics Records"
APP_BUNDLE="CosmeticsRecords.app"
VERSION="${1:-0.9.0}"

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    ARCH_LABEL="AppleSilicon"
else
    ARCH_LABEL="Intel"
fi

DMG_NAME="CosmeticsRecords-macOS-${ARCH_LABEL}-Setup"
DIST_DIR="dist"

# Ensure we're in project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Creating macOS DMG Installer ==="
echo "App: $APP_NAME"
echo "Version: $VERSION"
echo "Architecture: $ARCH_LABEL"
echo ""

# Check that the app bundle exists
if [ ! -d "$DIST_DIR/$APP_BUNDLE" ]; then
    echo "Error: $DIST_DIR/$APP_BUNDLE not found"
    echo "Please build the app first with: pyinstaller cosmetics_records.spec"
    exit 1
fi

# Remove any existing DMG
rm -f "$DIST_DIR/$DMG_NAME.dmg"

# Check if create-dmg is available (preferred method)
if command -v create-dmg &> /dev/null; then
    echo "Using create-dmg for professional DMG creation..."

    create-dmg \
        --volname "$APP_NAME" \
        --volicon "$DIST_DIR/$APP_BUNDLE/Contents/Resources/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "$APP_BUNDLE" 150 190 \
        --hide-extension "$APP_BUNDLE" \
        --app-drop-link 450 190 \
        --no-internet-enable \
        "$DIST_DIR/$DMG_NAME.dmg" \
        "$DIST_DIR/$APP_BUNDLE"

else
    echo "create-dmg not found, using hdiutil (basic DMG)..."
    echo "For a better DMG, install create-dmg: brew install create-dmg"
    echo ""

    # Create a temporary directory for DMG contents
    DMG_TEMP="$DIST_DIR/dmg_temp"
    rm -rf "$DMG_TEMP"
    mkdir -p "$DMG_TEMP"

    # Copy app bundle
    cp -R "$DIST_DIR/$APP_BUNDLE" "$DMG_TEMP/"

    # Create Applications symlink
    ln -s /Applications "$DMG_TEMP/Applications"

    # Create DMG using hdiutil
    hdiutil create -volname "$APP_NAME" \
        -srcfolder "$DMG_TEMP" \
        -ov -format UDZO \
        "$DIST_DIR/$DMG_NAME.dmg"

    # Clean up
    rm -rf "$DMG_TEMP"
fi

echo ""
echo "=== DMG Created Successfully ==="
echo "Output: $DIST_DIR/$DMG_NAME.dmg"
echo ""

# Show file size
DMG_SIZE=$(du -h "$DIST_DIR/$DMG_NAME.dmg" | cut -f1)
echo "Size: $DMG_SIZE"
