# KappaCore FM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) An experimental, automated AI radio station broadcasting live on Twitch. Featuring AI-generated music and an AI host discussing the latest happenings from Twitter and r/LivestreamFail, powered primarily by Azure AI services.

## About The Project

This project explores the intersection of AI, streaming culture, and automated content generation. Inspired by streamers, it aims to create an entertaining, ambient background stream hosted entirely by AI.

Can an AI host keep up with the chaos of streamer news scraped from Reddit and Twitter? Can it generate engaging commentary and mix it with AI music seamlessly? This project is an attempt to find out!

**Current Stage:** Proof-of-Concept (Focusing on core AI voice generation).

## Features (Planned)

* **AI Host Voice:** Realistic voice generation using Azure AI Speech.
* **Content Engine:**
    * Automated scraping and discussion of top/hot posts from r/LivestreamFail (via Reddit API).
    * Automated scraping and discussion of specific Twitter feeds (Planned).
* **AI Music:** Integration of AI-generated background music (from external services or local files).
* **Text Processing:** Summarization and commentary generation using Azure AI Language / Azure OpenAI Service / Gemini API.
* **Live Streaming:** Broadcasting the final audio mix to Twitch via OBS Studio.
* **Automation:** Orchestration using Azure Functions and potentially Azure Logic Apps.

## Built With

* [Python](https://www.python.org/)
* [Azure AI Speech](https://azure.microsoft.com/en-us/products/ai-services/ai-speech/)
* [Azure Functions](https://azure.microsoft.com/en-us/products/functions/)
* [Azure Blob Storage](https://azure.microsoft.com/en-us/products/storage/blobs/)
* [Azure AI Language](https://azure.microsoft.com/en-us/products/ai-services/ai-language/) / [Azure OpenAI Service](https://azure.microsoft.com/en-us/products/ai-services/openai-service/) (or potentially Google Gemini API Free Tier)
* [PRAW (Python Reddit API Wrapper)](https://praw.readthedocs.io/en/stable/)
* [OBS Studio](https://obsproject.com/) (for streaming)
* [Playsound3](https://github.com/sjmikler/playsound3) (or similar for local audio playback)
* Virtual Audio Cable / Voicemeeter (for local audio routing)

## Getting Started (Proof-of-Concept: Local TTS Test)

This initial setup focuses only on testing the core Text-to-Speech functionality locally using Azure.

### Prerequisites

* Python 3.8+ installed
* Git installed
* An Azure Account (Free Tier is sufficient for this PoC)
* An Azure AI Speech service resource created in the Azure Portal (Note its **Key** and **Region**)

### Installation & Setup

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/YourUsername/](https://github.com/YourUsername/)[Project Name].git
    cd [Project Name]
    ```
2.  **Create and activate a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install Python requirements:**
    *(Make sure you have a `requirements.txt` file with at least `azure-cognitiveservices-speech` and `playsound3` listed)*
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Azure Credentials:**
    * It's recommended to use environment variables. Set the following:
        ```bash
        # Linux/macOS
        export SPEECH_KEY="YOUR_AZURE_SPEECH_KEY"
        export SPEECH_REGION="YOUR_AZURE_SPEECH_REGION"

        # Windows (Command Prompt)
        set SPEECH_KEY="YOUR_AZURE_SPEECH_KEY"
        set SPEECH_REGION="YOUR_AZURE_SPEECH_REGION"

        # Windows (PowerShell)
        $env:SPEECH_KEY="YOUR_AZURE_SPEECH_KEY"
        $env:SPEECH_REGION="YOUR_AZURE_SPEECH_REGION"
        ```
    * Alternatively, modify the initial test script (`test_speech.py` or similar) directly with your key and region (less secure, only okay for initial local testing).

### Running the PoC

1.  Ensure your Azure credentials are set correctly (either as environment variables or in the script).
2.  Run the initial test script:
    ```bash
    python test_speech.py
    ```
3.  You should hear the test sentence spoken through your default speakers.

## Usage (Intended Final Product)

Once fully developed, the project aims to run as an automated background process:
1.  Scheduled tasks (Azure Functions/Logic Apps) trigger content scraping (Reddit/Twitter).
2.  Scraped text is processed and summarized by an AI Language model.
3.  Commentary scripts are generated.
4.  Azure AI Speech converts scripts to audio files, saved to Azure Blob Storage.
5.  A local orchestrator downloads new speech segments and AI music tracks from Blob Storage.
6.  The orchestrator plays back speech and music through separate channels routed into OBS Studio via virtual audio cables.
7.  OBS Studio streams the final mixed audio output live to a dedicated Twitch channel.

## Roadmap

* [X] Initial local Azure TTS setup (`test_speech.py`).
* [ ] Move TTS generation to Azure Function.
* [ ] Integrate Azure Blob Storage for audio file input/output.
* [ ] Implement basic Reddit scraping using PRAW in Azure Function.
* [ ] Add basic text processing/summarization (Azure AI Language).
* [ ] Set up local music playback and OBS audio mixing.
* [ ] Explore reliable Twitter scraping methods/APIs.
* [ ] Implement more sophisticated text-to-script generation (Azure OpenAI / Gemini API).
* [ ] Develop robust cloud orchestration (Logic Apps / Durable Functions).
* [ ] Configure and automate OBS streaming setup.
* [ ] Add error handling and monitoring.

## Contributing

Contributions are welcome! Please open an issue first to discuss what you would like to change or add.

## License

Distributed under the MIT License. See `LICENSE` file for more information.

## Acknowledgements

* Azure AI Services
* Python Community
* README Template inspiration (Optional: link to any template you used)
