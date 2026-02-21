# PicoChat

A minimalist LLM chat application that only keeps one *temporary* chat session running. A new session can be created using a simple shortcut `Ctrl+Shift+D`. Built using Python and PyQt (PySide6).

Ideal for short and quick tasks. Inspired by Firefox Focus.

### 🤔 Why build this?
I wanted a quick and efficient way to execute simple tasks like proofreading, minor bug/code explanations, etc., using language models. Things I don't mind storing for later use.
Utilising small language models running locally on my laptop couldn't have been a better solution.

Another reason was that I wanted to vibecode a simple app whilst testing Google's Antigravity.

## Installation & Running
- If you're a **Linux** user, download the pre-built binary from the [Releases](https://github.com/redromnon/picochat/releases/tag/v1.0) section. All binaries are built on a Fedora machine.
- If you're using Windows or macOS, you'll need to build the app yourself.

You will need a language model already running on your system using an inference engine like LMStudio, Ollama, etc. Then insert the OpenAI-compatible model endpoint in the app's top bar.
