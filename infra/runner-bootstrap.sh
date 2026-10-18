#!/bin/bash
# EC2 user data: turns a fresh Ubuntu 24.04 instance into a CI runner host.
# Runs once, as root, on first boot. Its output goes to /var/log/cloud-init-output.log
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y make git unzip curl python3.12-venv

# Docker, and let the ubuntu user run it without sudo
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable --now docker

# AWS CLI v2, needed for "aws ecr get-login-password"
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install

# A folder for the GitHub runner. Registering it is done by hand,
# because it needs a short-lived token from GitHub.
mkdir -p /home/ubuntu/actions-runner
chown ubuntu:ubuntu /home/ubuntu/actions-runner

echo "Bootstrap finished" > /home/ubuntu/BOOTSTRAP_DONE