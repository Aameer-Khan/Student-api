#!/usr/bin/env bash
# Checks for the tools needed to run the Student API and installs any that are missing.
set -euo pipefail

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_make() {
  if command_exists make; then
    echo "✔ make is already installed"
    return
  fi
  echo "Installing make..."
  case "$(uname -s)" in
    Darwin) xcode-select --install ;;
    Linux)  sudo apt-get update && sudo apt-get install -y make ;;
    *)      echo "Unsupported OS. Please install make manually."; exit 1 ;;
  esac
}

install_docker() {
  if command_exists docker; then
    echo "✔ docker is already installed"
    return
  fi
  echo "Installing docker..."
  case "$(uname -s)" in
    Darwin)
      if ! command_exists brew; then
        echo "Homebrew is required. Install it from https://brew.sh, then rerun this script."
        exit 1
      fi
      brew install --cask docker
      ;;
    Linux)
      curl -fsSL https://get.docker.com | sh
      ;;
    *) echo "Unsupported OS. Please install Docker manually."; exit 1 ;;
  esac
}

check_docker_running() {
  if docker info >/dev/null 2>&1; then
    echo "✔ Docker engine is running"
  else
    echo "✘ Docker is installed, but the engine isn't running. Start Docker Desktop and rerun this script."
    exit 1
  fi
}

install_make
install_docker
check_docker_running
echo "All set. Next: cp .env.example .env, then make docker-run"
