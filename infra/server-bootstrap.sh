#!/bin/bash
# EC2 user data: prepares a fresh Ubuntu server to run the Student API stack.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

install_packages() {
  apt-get update -y
  apt-get install -y make git curl
}

install_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  fi
  systemctl enable --now docker
}

allow_ubuntu_docker() {
  usermod -aG docker ubuntu
}

verify() {
  docker --version
  docker compose version
  make --version | head -1
}

main() {
  install_packages
  install_docker
  allow_ubuntu_docker
  verify
  touch /home/ubuntu/BOOTSTRAP_DONE
}

main