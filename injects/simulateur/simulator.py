import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


STATE_DIR = Path(os.environ.get("STATE_DIR", "/state"))
previous_states = {}

SCENARIOS = {
    "11": ("11-dns.active", "dns_query_timeout"),
    "12": ("12-reseau.active", "network_errors_detected"),
    "13": ("13-dhcp.active", "dhcp_pool_exhausted"),
    "14": ("14-tls.active", "certificate_expiry_warning"),
    "15": ("15-backup.active", "backup_job_incomplete"),
    "16": ("16-auth.active", "authentication_backend_unreachable"),
    "17": ("17-disque.active", "storage_operation_slow"),
    "20": ("20-securite.active", "security_auth_failure_burst"),
}


def log(event, **fields):
    print(json.dumps({"event": event, **fields}), flush=True)


def is_active(scenario):
    filename, event = SCENARIOS[scenario]
    active = (STATE_DIR / filename).exists()
    if previous_states.get(scenario) != active:
        previous_states[scenario] = active
        log(event if active else "scenario_returned_to_normal", scenario=scenario, active=active)
    return active


def metric_lines():
    now = time.time()
    states = {scenario: is_active(scenario) for scenario in SCENARIOS}
    return [
        '# HELP lab_dns_query_success Simulated DNS query result.',
        '# TYPE lab_dns_query_success gauge',
        f'lab_dns_query_success{{scenario="11",service="dns-lab"}} {0 if states["11"] else 1}',
        '# HELP lab_dns_query_duration_seconds Simulated DNS query duration.',
        '# TYPE lab_dns_query_duration_seconds gauge',
        f'lab_dns_query_duration_seconds{{scenario="11",service="dns-lab"}} {3.0 if states["11"] else 0.02}',
        '# HELP lab_network_receive_errors_rate Simulated network receive errors per second.',
        '# TYPE lab_network_receive_errors_rate gauge',
        f'lab_network_receive_errors_rate{{scenario="12",interface="lab0"}} {12 if states["12"] else 0}',
        '# HELP lab_network_latency_seconds Simulated network request latency.',
        '# TYPE lab_network_latency_seconds gauge',
        f'lab_network_latency_seconds{{scenario="12",interface="lab0"}} {1.2 if states["12"] else 0.01}',
        '# HELP lab_dhcp_available_leases Simulated available DHCP leases.',
        '# TYPE lab_dhcp_available_leases gauge',
        f'lab_dhcp_available_leases{{scenario="13",pool="lab-pool"}} {0 if states["13"] else 20}',
        '# HELP lab_dhcp_request_success Simulated DHCP request result.',
        '# TYPE lab_dhcp_request_success gauge',
        f'lab_dhcp_request_success{{scenario="13",pool="lab-pool"}} {0 if states["13"] else 1}',
        '# HELP lab_tls_certificate_expiry_timestamp_seconds Simulated TLS certificate expiration timestamp.',
        '# TYPE lab_tls_certificate_expiry_timestamp_seconds gauge',
        f'lab_tls_certificate_expiry_timestamp_seconds{{scenario="14",service="internal-tls"}} {now + (3 if states["14"] else 90) * 86400:.0f}',
        '# HELP lab_backup_last_run_success Simulated backup job result.',
        '# TYPE lab_backup_last_run_success gauge',
        f'lab_backup_last_run_success{{scenario="15",job="daily-backup"}} {0 if states["15"] else 1}',
        '# HELP lab_backup_expected_bytes Expected backup size.',
        '# TYPE lab_backup_expected_bytes gauge',
        'lab_backup_expected_bytes{scenario="15",job="daily-backup"} 104857600',
        '# HELP lab_backup_actual_bytes Actual simulated backup size.',
        '# TYPE lab_backup_actual_bytes gauge',
        f'lab_backup_actual_bytes{{scenario="15",job="daily-backup"}} {31457280 if states["15"] else 104857600}',
        '# HELP lab_auth_backend_up Simulated authentication backend availability.',
        '# TYPE lab_auth_backend_up gauge',
        f'lab_auth_backend_up{{scenario="16",service="lab-auth"}} {0 if states["16"] else 1}',
        '# HELP lab_auth_failures_per_minute Simulated authentication failures per minute.',
        '# TYPE lab_auth_failures_per_minute gauge',
        f'lab_auth_failures_per_minute{{scenario="16",service="lab-auth"}} {24 if states["16"] else 0}',
        '# HELP lab_storage_operation_duration_seconds Simulated application storage operation duration.',
        '# TYPE lab_storage_operation_duration_seconds gauge',
        f'lab_storage_operation_duration_seconds{{scenario="17",operation="write"}} {3.2 if states["17"] else 0.03}',
        '# HELP lab_security_auth_failures_2m Simulated unusual authentication failures in two minutes.',
        '# TYPE lab_security_auth_failures_2m gauge',
        f'lab_security_auth_failures_2m{{scenario="20",source="lab-client"}} {12 if states["20"] else 0}',
        '# HELP lab_simulator_up Simulator process state.',
        '# TYPE lab_simulator_up gauge',
        'lab_simulator_up{service="lab-simulator"} 1',
    ]


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="text/plain; charset=utf-8"):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, "LAB_SIMULATOR_OK\n")
            return
        if self.path == "/metrics":
            self.reply(200, "\n".join(metric_lines()) + "\n", "text/plain; version=0.0.4; charset=utf-8")
            return
        if self.path == "/storage/write":
            delay = 3.0 if is_active("17") else 0.03
            time.sleep(delay)
            log("storage_write_completed", scenario="17", duration_seconds=delay)
            self.reply(200, f"STORAGE_WRITE_OK duration={delay}\n")
            return
        self.reply(404, "NOT_FOUND\n")

    def log_message(self, fmt, *args):
        if self.path != "/metrics":
            log("http_request", client=self.client_address[0], path=self.path, message=fmt % args)


log("lab_simulator_started", port=8083, state_dir=str(STATE_DIR))
ThreadingHTTPServer(("0.0.0.0", 8083), Handler).serve_forever()
