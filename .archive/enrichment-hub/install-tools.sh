#!/bin/bash
# Installation script for Obsidian, GitKraken, and Git tools
# Run this script with: bash install-tools.sh or ./install-tools.sh

set -e  # Exit on error

echo "========================================"
echo "CTB Project Tools Installation Script"
echo "========================================"
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    echo "⚠️  Unsupported OS: $OSTYPE"
    echo "Please install tools manually"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Git
echo "📥 Checking Git installation..."
if command_exists git; then
    echo "✅ Git is already installed"
    git --version
else
    echo "Installing Git..."
    if [[ "$OS" == "mac" ]]; then
        if command_exists brew; then
            brew install git
        else
            echo "❌ Homebrew not found. Please install from https://brew.sh"
            exit 1
        fi
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y git
        elif command_exists yum; then
            sudo yum install -y git
        elif command_exists dnf; then
            sudo dnf install -y git
        else
            echo "❌ Package manager not found. Please install Git manually."
            exit 1
        fi
    fi
    echo "✅ Git installed!"
fi

echo ""

# Install Node.js
echo "📥 Checking Node.js installation..."
if command_exists node; then
    echo "✅ Node.js is already installed"
    node --version
    npm --version
else
    echo "Installing Node.js..."
    if [[ "$OS" == "mac" ]]; then
        brew install node
    elif [[ "$OS" == "linux" ]]; then
        if command_exists apt-get; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        else
            echo "❌ Please install Node.js manually from https://nodejs.org"
            exit 1
        fi
    fi
    echo "✅ Node.js installed!"
fi

echo ""

# Install Obsidian
echo "📥 Checking Obsidian installation..."
if command_exists obsidian; then
    echo "✅ Obsidian is already installed"
else
    echo "Installing Obsidian..."
    if [[ "$OS" == "mac" ]]; then
        brew install --cask obsidian
    elif [[ "$OS" == "linux" ]]; then
        echo "For Linux, please download Obsidian from:"
        echo "https://obsidian.md/download"
        echo "Or use snap: sudo snap install obsidian --classic"
    fi
fi

echo ""

# Install GitKraken
echo "📥 Checking GitKraken installation..."
if command_exists gitkraken; then
    echo "✅ GitKraken is already installed"
else
    echo "Installing GitKraken..."
    if [[ "$OS" == "mac" ]]; then
        brew install --cask gitkraken
    elif [[ "$OS" == "linux" ]]; then
        echo "For Linux, please download GitKraken from:"
        echo "https://www.gitkraken.com/download"
        echo "Or use snap: sudo snap install gitkraken --classic"
    fi
fi

echo ""

# Configure Git hooks (make them executable)
echo "🔧 Setting up Git hooks..."
if [ -d ".git/hooks" ]; then
    chmod +x .git/hooks/pre-commit 2>/dev/null || true
    chmod +x .git/hooks/commit-msg 2>/dev/null || true
    chmod +x .git/hooks/pre-push 2>/dev/null || true
    echo "✅ Git hooks configured!"
else
    echo "⚠️  Git repository not initialized. Run 'git init' first."
fi

echo ""

# Install project dependencies
echo "📦 Installing project dependencies..."
if [ -f "package.json" ]; then
    npm install
    echo "✅ Dependencies installed!"
else
    echo "⚠️  package.json not found in current directory"
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Configure your environment variables in .env file"
echo "2. Open Obsidian and select this folder as vault"
echo "3. Open GitKraken and add this repository"
echo "4. Configure Git user:"
echo "   git config user.name 'Your Name'"
echo "   git config user.email 'your.email@example.com'"
echo ""
echo "Happy coding! 🚀"
