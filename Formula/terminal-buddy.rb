# Homebrew Formula for Terminal Buddy
# This file goes in your homebrew-tap repo:
#   github.com/xiaofeihu/homebrew-tap/Formula/terminal-buddy.rb
#
# Users install with:
#   brew install xiaofeihu/tap/terminal-buddy

class TerminalBuddy < Formula
  include Language::Python::Virtualenv

  desc "AI-powered terminal assistant using local Ollama models"
  homepage "https://github.com/xiaofeihu/terminal-buddy"
  url "https://files.pythonhosted.org/packages/source/t/terminal-buddy/terminal_buddy-0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256_AFTER_PYPI_PUBLISH"
  license "MIT"

  depends_on "python@3.13"
  depends_on "ollama" => :recommended

  # Add resource blocks for each dependency.
  # Generate these with: `poet terminal-buddy`  (brew install poet first)
  #
  # resource "requests" do
  #   url "https://files.pythonhosted.org/packages/..."
  #   sha256 "..."
  # end
  #
  # resource "rich" do
  #   url "https://files.pythonhosted.org/packages/..."
  #   sha256 "..."
  # end

  def install
    virtualenv_install_with_resources

    # Install the shell integration script
    (share / "terminal-buddy").install "shell/buddy.zsh"
  end

  def caveats
    <<~EOS
      To enable auto-error detection, add to your ~/.zshrc:

        eval "$(terminal-buddy --init-shell)"

      Make sure Ollama is running:

        brew services start ollama
        ollama pull qwen3-coder:1.5b
    EOS
  end

  test do
    assert_match "terminal-buddy", shell_output("#{bin}/terminal-buddy 2>&1", 0)
  end
end
