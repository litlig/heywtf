# Homebrew Formula for heywtf
# This file goes in your homebrew-tap repo:
#   github.com/litlig/homebrew-tap/Formula/heywtf.rb
#
# Users install with:
#   brew install litlig/tap/heywtf

class Heywtf < Formula
  include Language::Python::Virtualenv

  desc "AI-powered terminal assistant — ask anything or diagnose failures with 'hey wtf'"
  homepage "https://github.com/litlig/heywtf"
  url "https://files.pythonhosted.org/packages/source/h/heywtf/heywtf-0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256_AFTER_PYPI_PUBLISH"
  license "MIT"

  depends_on "python@3.13"
  depends_on "ollama" => :recommended

  # Add resource blocks for each dependency.
  # Generate these with: `poet heywtf`  (brew install poet first)
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
    (share / "heywtf").install "shell/buddy.zsh"
  end

  def caveats
    <<~EOS
      To enable auto-error detection, add to your ~/.zshrc:

        eval "$(heywtf --init-shell)"

      Make sure Ollama is running:

        brew services start ollama
        ollama pull qwen2.5-coder:0.5b
    EOS
  end

  test do
    assert_match "heywtf", shell_output("#{bin}/heywtf 2>&1", 0)
  end
end
