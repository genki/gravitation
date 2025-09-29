#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/gen_dev_cert.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# 開発用自己署名証明書を生成(SAN: localhost, 127.0.0.1)
# 出力: server/certs/dev.key, server/certs/dev.crt

OUTDIR="server/certs"
mkdir -p "$OUTDIR"

KEY="$OUTDIR/dev.key"
CRT="$OUTDIR/dev.crt"

if command -v openssl >/dev/null 2>&1; then
  cat > "$OUTDIR/openssl.cnf" << 'EOF'
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = v3_req
x509_extensions    = v3_req
prompt             = no

[ req_distinguished_name ]
C  = XX
ST = Dev
L  = Dev
O  = Local
OU = Dev
CN = localhost

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
IP.1  = 127.0.0.1
EOF

  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$KEY" -out "$CRT" -config "$OUTDIR/openssl.cnf"
  echo "生成: $CRT, $KEY"
else
  echo "エラー: openssl が見つかりません。インストールしてください。" >&2
  exit 1
fi
