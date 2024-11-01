#! /usr/bin/env bash
if ! [ -x "$(command -v chromium)" ]; then
    playwright install --with-deps chromium
fi
