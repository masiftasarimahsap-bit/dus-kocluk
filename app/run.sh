#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "📦 Sanal ortam oluşturuluyor..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "📥 Bağımlılıklar yükleniyor..."
pip install -q -r requirements.txt

echo ""
echo "🦷 DUS Koçluk Sistemi başlatılıyor..."
echo "🌐 Tarayıcıda aç: http://localhost:8000"
echo "   (Durdurmak için Ctrl+C)"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
