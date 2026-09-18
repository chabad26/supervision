#!/usr/bin/env bash
# Exécuter dans ~/observabilite sur supervision. Aucun certificat existant écrasé.
set -euo pipefail
umask 077
SUPERVISION_IP="${1:-192.168.122.80}"
OUT="tls-beats"
if [[ -e "$OUT" ]]; then
  echo "Refus : tls-beats existe déjà. Examiner les certificats existants." >&2
  exit 1
fi
command -v openssl >/dev/null
mkdir -p "$OUT"/{ca,server,linux,windows}
openssl req -x509 -newkey rsa:3072 -noenc -sha256 -days 365 \
  -keyout "$OUT/ca/ca.key" -out "$OUT/ca/ca.crt" \
  -subj '/CN=AlpesNet Beats Lab CA' \
  -addext 'basicConstraints=critical,CA:TRUE' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
for role in server linux windows; do
  openssl req -new -newkey rsa:2048 -noenc \
    -keyout "$OUT/$role/key.pem" -out "$OUT/$role/request.csr" \
    -subj "/CN=alpesnet-beats-$role"
  if [[ "$role" == server ]]; then
    printf '%s\n' 'basicConstraints=critical,CA:FALSE' \
      'keyUsage=critical,digitalSignature,keyEncipherment' \
      'extendedKeyUsage=serverAuth' \
      "subjectAltName=IP:$SUPERVISION_IP,DNS:supervision,DNS:logstash-logs" > "$OUT/$role/extensions.cnf"
  else
    printf '%s\n' 'basicConstraints=critical,CA:FALSE' \
      'keyUsage=critical,digitalSignature' 'extendedKeyUsage=clientAuth' > "$OUT/$role/extensions.cnf"
  fi
  openssl x509 -req -sha256 -days 90 \
    -in "$OUT/$role/request.csr" -CA "$OUT/ca/ca.crt" -CAkey "$OUT/ca/ca.key" \
    -CAserial "$OUT/ca/ca.srl" -CAcreateserial \
    -extfile "$OUT/$role/extensions.cnf" -out "$OUT/$role/cert.pem"
  openssl pkcs8 -topk8 -nocrypt -in "$OUT/$role/key.pem" -out "$OUT/$role/key.pkcs8.pem"
  cp "$OUT/ca/ca.crt" "$OUT/$role/ca.crt"
done
openssl verify -CAfile "$OUT/ca/ca.crt" -purpose sslserver -verify_ip "$SUPERVISION_IP" "$OUT/server/cert.pem"
openssl verify -CAfile "$OUT/ca/ca.crt" -purpose sslclient "$OUT/linux/cert.pem" "$OUT/windows/cert.pem"
echo 'Certificats créés : validité clients/serveur 90 jours. Conserver les clés hors Git et hors captures.'
