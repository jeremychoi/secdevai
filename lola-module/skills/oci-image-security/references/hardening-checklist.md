# Container Image Hardening Checklist

Environment-specific hardening baselines for OCI container images. Load this file during hardening gap analysis steps.

---

## Baseline: General Production Images

| Control | Check | Pass Condition |
|---|---|---|
| Non-root user | `docker inspect --format='{{.Config.User}}' <image>` | Non-empty, non-root UID |
| No new privileges | `--security-opt=no-new-privileges` compatible | Image does not require SUID/SGID binaries for normal operation |
| Read-only root filesystem | `--read-only` compatible | Writable paths limited to explicitly declared volumes or tmpfs mounts |
| Minimal capabilities | Functional without `--privileged` | Only required capabilities listed in documentation |
| No secrets in layers | `docker history` + layer inspection | No credentials, keys, or tokens in any layer |
| Current base image | Image build date within 90 days | Base image is not stale |
| SBOM available | Cosign attestation or image label | SBOM present and accessible |

---

## Baseline: Red Hat UBI / RHEL Images

| Control | Check | Pass Condition |
|---|---|---|
| UBI base | `com.redhat.component` label present | Built on official UBI base |
| Image signed | `cosign verify` against Red Hat key | Valid signature |
| RPM GPG verification | All packages GPG-verified | No packages installed with `--nogpgcheck` |
| FIPS readiness | Crypto uses RHEL OpenSSL | No non-FIPS algorithm use as default |
| SELinux labels | `io.openshift.tags` or SELinux context labels | Labels present for OpenShift deployability |
| Non-root UID | `USER` directive in Dockerfile | UID ≥ 1000 |

---

## Baseline: FedRAMP High / ROSA GovCloud Images

These controls apply to container images deployed in FedRAMP High environments (e.g., ROSA HCP GovCloud).

| Control | NIST 800-53 Mapping | Check | Pass Condition |
|---|---|---|---|
| FIPS 140-2/3 validated crypto | SC-13 | Only FIPS-validated modules used for cryptographic operations | OpenSSL in FIPS mode; no non-FIPS TLS cipher suites enabled by default |
| No default credentials | IA-5 | No hardcoded or default credentials | All credentials must be injected at runtime via secrets management |
| Audit logging enabled | AU-2, AU-12 | Service produces audit logs in structured format | Logs capture authentication, privilege use, and configuration changes |
| Least privilege | AC-6 | Minimal Linux capabilities required | No `CAP_SYS_ADMIN` unless explicitly justified |
| Image provenance | SI-7, CM-14 | Signed image with verifiable SBOM | SBOM covers all OS packages and application dependencies |
| Vulnerability scan clean | RA-5, SI-2 | No unmitigated HIGH/CRITICAL CVEs at deploy time | All findings either patched or covered by an approved Deviation Request |
| Secrets management integration | IA-5, SC-28 | Credentials sourced from secrets manager (Vault, K8s Secrets) | No plaintext credentials in env vars, config files, or image layers |
| TLS enforced | SC-8, SC-23 | All network communications encrypted | TLS 1.2 minimum; TLS 1.3 preferred; no plaintext fallback |

---

## Baseline: CIS Docker Benchmark (Abbreviated)

Key controls from CIS Docker Benchmark v1.6 most relevant to image-level review:

| CIS Control | Description | Check |
|---|---|---|
| 4.1 | Do not use root user inside containers | `USER` directive present and non-root |
| 4.2 | Use trusted base images | Base image provenance verified |
| 4.6 | Add HEALTHCHECK instruction | `HEALTHCHECK` present in Dockerfile |
| 4.7 | Do not use update instructions in Dockerfile | No `RUN apt-get upgrade` or `yum update -y` in final Dockerfile |
| 4.8 | Remove setuid/setgid permissions | No unexpected SUID/SGID binaries |
| 4.9 | Use COPY instead of ADD | No `ADD` from external URLs |
| 4.10 | Do not store secrets in Dockerfiles | Inspect history for credential patterns |

---

## Hardening Gap Finding Template

```
**Finding:** Missing hardening control — [control name]
**Category:** Hardening
**Severity:** [High if FedRAMP-required | Moderate for general best practice | Low for advisory]
**Component:** Image: [image name:tag]
**Description:** The image does not implement [control]. In [deployment context],
  this means [specific risk]. [NIST control reference if applicable.]
**Evidence:** [Command output or config file content demonstrating the gap]
**Recommendation:** [Specific remediation — Dockerfile change, runtime flag, or
  configuration update needed to satisfy the control]
**References:** [CIS Benchmark section | NIST 800-53 control | Red Hat hardening guide URL]
```
