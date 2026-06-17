#!/usr/bin/env bash
# Сборка sources.avar.me.
# Использование:  ./build.sh
# Локальная проверка: python3 -m http.server -d docs 8000
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

python3 src/build_site.py

# Защита от мусорных файлов из-за неверных шагов
if [ ! -f "docs/index.html" ]; then
  echo "build.sh: docs/index.html не создан — что-то пошло не так" >&2
  exit 1
fi

echo ""
echo "Готово. Локально:  python3 -m http.server -d docs 8000"
