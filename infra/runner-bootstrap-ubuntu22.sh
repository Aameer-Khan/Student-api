#!/bin/bash
# Prepares an Ubuntu 22.04 server as a GitHub Actions self-hosted runner for Student-api.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
RUNNER_USER="${RUNNER_USER:-cloud_user}"

install_packages() {
  apt-get update -y
  apt-get install -y make git curl jq
}

install_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  fi
  systemctl enable --now docker
}

allow_docker() {
  usermod -aG docker "$RUNNER_USER"
}

enable_multiarch() {
  docker run --privileged --rm tonistiigi/binfmt --install arm64
}

main() {
  install_packages
  install_docker
  allow_docker
  enable_multiarch
  docker buildx version
}

main