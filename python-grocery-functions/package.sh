#!/bin/bash

OUTPUT_ZIP="serverless_artifact.zip"

rm -f $OUTPUT_ZIP || { echo "Failed to remove existing $OUTPUT_ZIP"; exit 1; }

rm -rf .package || { echo "Failed to remove existing temporary directory"; exit 1; }
mkdir .package || { echo "Failed to create temporary directory"; exit 1; }
TEMP_DIR=.package

# Copy the necessary folders to the temporary directory
cp -R aws_config.py $TEMP_DIR/ || { echo "Failed to copy aws_config.py"; exit 1; }
cp -R offer_feed $TEMP_DIR/ || { echo "Failed to copy offer_feed"; exit 1; }
cp -R scraper_feed $TEMP_DIR/ || { echo "Failed to copy scraper_feed"; exit 1; }
cp -R book_feed $TEMP_DIR/ || { echo "Failed to copy book_feed"; exit 1; }
cp -R scraper_management $TEMP_DIR/ || { echo "Failed to copy scraper_management"; exit 1; }
cp -R storage $TEMP_DIR/ || { echo "Failed to copy storage"; exit 1; }
cp -R util $TEMP_DIR/ || { echo "Failed to copy util"; exit 1; }
cp -R parsing $TEMP_DIR/ || { echo "Failed to copy parsing"; exit 1; }
cp -R config $TEMP_DIR/ || { echo "Failed to copy config"; exit 1; }
cp -R amp_types $TEMP_DIR/ || { echo "Failed to copy amp_types"; exit 1; }
cp -R transform $TEMP_DIR/ || { echo "Failed to copy transform"; exit 1; }

# Clean up unnecessary files
find $TEMP_DIR -type d -name "__tests__" -exec rm -rf {} + || { echo "Failed to remove __tests__"; exit 1; }
find $TEMP_DIR -type d -name "__pycache__" -exec rm -rf {} + || { echo "Failed to remove __pycache__"; exit 1; }

SIZE_MB_UNZIPPED=$(du -shm $TEMP_DIR | cut -f1)

cd $TEMP_DIR

zip -r "../${OUTPUT_ZIP}" * || { echo "Failed to create zip"; exit 1; }

cd ..

SIZE_MB_ZIPPED=$(du -m $OUTPUT_ZIP | cut -f1)

echo "Package created: $OUTPUT_ZIP ($SIZE_MB_UNZIPPED MB, $SIZE_MB_ZIPPED MB zipped)"
