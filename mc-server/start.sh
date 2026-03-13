#!/bin/bash
cd "$(dirname "$0")"
JAVA="/usr/local/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java"
"$JAVA" -Xmx2G -Xms1G -jar server.jar nogui
