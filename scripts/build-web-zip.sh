#!/bin/bash

# Run with project root as cwd.

OUTPUT_DIR="$1"
if [ -z "$OUTPUT_DIR" ]; then
    OUTPUT_DIR="boa-nimbus/s3"
fi

ZIP_NAME="web-static.zip"
SOURCE_DIR="web-static/www"

PREVIOUS_PWD=$(pwd)

cd "$SOURCE_DIR"

if [ $? -ne 0 ]; then
    echo "Run this from the project root."
    exit 1
fi

cd "$PREVIOUS_PWD"

mkdir -p "$OUTPUT_DIR"

cd "$SOURCE_DIR"

TEMP_DIR=$(mktemp -d)
TEMP_ZIP_PATH="$TEMP_DIR/$ZIP_NAME"

echo "Creating archive..."
zip "$TEMP_ZIP_PATH" -r * >/dev/null

ZIP_RESULT=$?

cd "$PREVIOUS_PWD"

if [ $ZIP_RESULT -ne 0 ]; then
    rm -rf "$TEMP_DIR"
    exit $ZIP_RESULT
fi

mv "$TEMP_ZIP_PATH" "$OUTPUT_DIR"

MV_RESULT=$?

rm -rf "$TEMP_DIR"

if [ $MV_RESULT -ne 0 ]; then
    exit $MV_RESULT
fi

echo "Archive $ZIP_NAME added to directory: $OUTPUT_DIR."