#! /usr/bin/env bash
if [ -z ${PLAYWRIGHT_BROWSERS_PATH} ]; then
    playwright install --with-deps chromium
fi
