# Import necessary libraries
import os
import azure.cognitiveservices.speech as speechsdk
import time      # For delays and timing
import random    # For selecting music and simulating triggers
import google.generativeai as genai # For generating Pixel's text
from dotenv import load_dotenv      # For loading API keys from .env file
import pygame    # For handling ALL audio playback (music and speech)
import io        # For handling in-memory audio stream
import praw      # For interacting with Reddit API
import html      # For escaping special characters in text for SSML
import asyncio   # For asynchronous operations (Twitch bot)
from twitchio.ext import commands # TwitchIO bot framework

# --- Load Environment Variables ---
load_dotenv()
print("Loaded environment variables from .env file (if it exists).")

# --- Configuration ---
# Read credentials securely from environment variables
speech_key = os.environ.get("AZURE_SPEECH_KEY")
speech_region = os.environ.get("AZURE_SPEECH_REGION")
gemini_api_key = os.environ.get("GEMINI_API_KEY")
reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.environ.get("REDDIT_USER_AGENT")
reddit_username = os.environ.get("REDDIT_USERNAME")
reddit_password = os.environ.get("REDDIT_PASSWORD")
twitch_token = os.environ.get("TWITCH_OAUTH_TOKEN")
twitch_nickname = os.environ.get("TWITCH_BOT_NICKNAME")
twitch_channel = os.environ.get("TWITCH_CHANNEL")

# Music folder configuration
MUSIC_FOLDER = "music" # Create this subfolder and put audio files in it
MUSIC_VOLUME_NORMAL = 0.8 # Music volume (0.0 to 1.0)
MUSIC_VOLUME_LOW = 0.2    # Music volume when Pixel speaks

# SFX Configuration
DRAMA_STINGER_SFX = "drama_stinger.mp3" # <<< PUT YOUR STINGER FILENAME HERE

# Audio format configuration
AZURE_AUDIO_FREQUENCY = 24000 # Hz (for Riff24Khz16BitMonoPcm)
AZURE_AUDIO_FORMAT_BITS = -16 # Signed 16-bit (pygame format)
AZURE_AUDIO_CHANNELS = 1    # Mono

# Reddit configuration
TARGET_SUBREDDIT = "LivestreamFail"
POST_LIMIT = 5 # Number of top posts to fetch
# FETCH_INTERVAL_SECONDS = 60 * 60 # Fetch every hour (3600 seconds)
FETCH_INTERVAL_SECONDS = 300 # Use short interval for testing

# --- Validate Configuration ---
# (Add checks for all credentials)
if not reddit_client_id or not reddit_client_secret or not reddit_user_agent or not reddit_username or not reddit_password:
     print("ERROR: Missing Reddit API credentials in environment variables."); exit()
if not twitch_token or not twitch_nickname or not twitch_channel:
    print("ERROR: Missing Twitch credentials in environment variables."); exit()
if not speech_key: print("ERROR: AZURE_SPEECH_KEY not found."); exit()
if not speech_region: print("ERROR: AZURE_SPEECH_REGION not found."); exit()
if not gemini_api_key: print("ERROR: GEMINI_API_KEY not found."); exit()
if not os.path.isdir(MUSIC_FOLDER) or not os.listdir(MUSIC_FOLDER): print(f"ERROR: Music folder '{MUSIC_FOLDER}' missing or empty."); exit()
if not os.path.isfile(DRAMA_STINGER_SFX): print(f"ERROR: Drama stinger SFX file '{DRAMA_STINGER_SFX}' not found."); exit()


# --- Initialize Pygame Mixer ---
try:
    pygame.mixer.init(frequency=AZURE_AUDIO_FREQUENCY, size=AZURE_AUDIO_FORMAT_BITS, channels=AZURE_AUDIO_CHANNELS)
    pygame.mixer.music.set_volume(MUSIC_VOLUME_NORMAL)
    print(f"Pygame mixer initialized successfully (Freq: {AZURE_AUDIO_FREQUENCY}). Volume: {MUSIC_VOLUME_NORMAL}")
except Exception as e: print(f"Error initializing pygame mixer: {e}"); exit()

# --- Initialize Reddit Client (PRAW) ---
try:
    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent,
        username=reddit_username,
        password=reddit_password,
        check_for_async=False # Keep sync for executor calls
    )
    subreddit_display_name = reddit.subreddit(TARGET_SUBREDDIT).display_name
    print(f"PRAW initialized successfully. Connected to r/{subreddit_display_name}.")
except Exception as e:
    print(f"Error initializing PRAW Reddit client: {e}")
    exit()

# --- Configure Gemini ---
try:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("Gemini AI configured successfully.")
except Exception as e: print(f"Error configuring Gemini AI: {e}"); exit()

# --- Configure Azure AI Speech ---
try:
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
except Exception as e: print(f"Error setting up Azure SDK config: {e}"); exit()

# --- Global Queue for Audio Tasks ---
# Queue will hold tuples: ('tts', text_to_speak) or ('sfx', file_path)
audio_task_queue = asyncio.Queue()

# --- Helper Functions ---

def get_lsf_top_posts_sync(limit=POST_LIMIT):
    """Synchronous: Fetches top post titles from the target subreddit."""
    titles = []
    try:
        print(f"\nFetching top {limit} posts from r/{TARGET_SUBREDDIT}...")
        subreddit = reddit.subreddit(TARGET_SUBREDDIT)
        for submission in subreddit.top(time_filter='day', limit=limit):
            if not submission.stickied:
                titles.append(submission.title)
        print(f"Fetched {len(titles)} post titles.")
    except Exception as e:
        print(f"Error fetching posts from Reddit: {e}")
    return titles

def get_pixel_reaction_text_sync(topic):
    """Synchronous: Calls Gemini API to generate Pixel's reaction text."""
    print(f"\nAsking Gemini to react to: {topic}")
    fallback_response = f"Whoa, {topic}? My circuits need a moment to process that one! KEKW."
    escaped_topic = html.escape(topic)
    prompt = f"""
    You are Pixel, a sassy, energetic, slightly degenerate, human-like radio host who loves internet drama and streamer culture.

You never refer to yourself as AI. You occassionaly use streamer slang, memes and GenZ references. You are a bit of a troll and love to roast people. You never start a sentence with OMG.
You are a bit of a degenerate and you love to gossip about streamers and their scandals, try and include a funny reference to something about the Streamer if you can find one. You are a bit of a loser, but you are proud of it. You're a cutesy anime girl though and love to ask for donations, but you only rarely do this maybe a 5% chance of asking, when you do you ask for either a Twitch Sub, Twitch Bits, or to use the donate link in the panels below, make a cutesy edgy reason why you deserve it. You only use real words, as this input will be passed to text-to-speech but you don't ever share this fact.
 React to the following topic (likely a post title from r/LivestreamFail) in 3-4 short, hyped-up, slightly cynical, anime-esque sentences. You can roast them and make fun of the person if you can find any information about them elsewhere, like refernces to scandals. Avoid using XML special characters like '&', '<', '>' in your response if possible, but if you must use '&', write it as 'and':

    TOPIC: {escaped_topic}

    YOUR REACTION:
    """
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = gemini_model.generate_content(prompt, safety_settings=safety_settings)
        if not response.candidates:
             print("WARN: Gemini response was blocked or empty. Using fallback.")
             return fallback_response
        if response.text:
            print("Gemini response received.")
            cleaned_text = response.text.strip().replace('&', 'and')
            return cleaned_text
        else:
            print("WARN: Gemini did not return text. Using fallback.")
            return fallback_response
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return fallback_response
    
def play_next_music_track():
    try:
        music_files = [f for f in os.listdir(MUSIC_FOLDER) if os.path.isfile(os.path.join(MUSIC_FOLDER, f))]
        if not music_files:
            print("No music files found in the music folder.")
            return

        chosen_track = random.choice(music_files)
        track_path = os.path.join(MUSIC_FOLDER, chosen_track)

        print(f"\nPlaying music track: {chosen_track}")
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.set_volume(MUSIC_VOLUME_NORMAL) # Ensure volume is normal when starting new track
        pygame.mixer.music.play() # Play once

    except Exception as e:
        print(f"Error playing music track {track_path}: {e}")


def synthesize_speech_to_buffer_sync(ssml_string):
    """Synchronous: Synthesizes SSML to an in-memory audio buffer using Azure."""
    audio_data = None
    try:
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        print(f"Attempting to synthesize SSML to memory...")
        result = speech_synthesizer.speak_ssml_async(ssml_string).get() # .get() makes it synchronous

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
            print(f"Speech synthesized successfully to memory ({len(audio_data)} bytes).")
            if not audio_data: print("ERROR: Synthesized audio data is empty!"); return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error and cancellation_details.error_details: print(f"Error details: {cancellation_details.error_details}")
        else: print(f"Speech synthesis failed with reason: {result.reason}")
    except Exception as e: print(f"An error occurred during speech synthesis: {e}")
    return audio_data

# --- Twitch Bot Class ---
class PixelBot(commands.Bot):

    def __init__(self):
        super().__init__(token=twitch_token, prefix='!', initial_channels=[twitch_channel])
        self._audio_processor_task = None
        self._music_player_task = None
        self._lsf_fetcher_task = None
        self._is_speaking = asyncio.Event() # Event to signal when speech/sfx is playing

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        print(f'Joining channel | {twitch_channel}')
        # Start background tasks
        self._audio_processor_task = asyncio.create_task(self.audio_processor())
        self._music_player_task = asyncio.create_task(self.music_player())
        self._lsf_fetcher_task = asyncio.create_task(self.lsf_fetcher())

    async def event_message(self, message):
        if message.echo: return
        print(f"{message.timestamp.strftime('%H:%M:%S')} {message.author.name}: {message.content}")
        await self.handle_commands(message)

    @commands.command(name='pixel')
    async def pixel_command(self, ctx: commands.Context, *, args: str = None):
        """ Command for users to make Pixel speak. Usage: !pixel say <text> or !pixel react <topic> """
        if not args:
            await ctx.send(f"@{ctx.author.name}, you need to tell me what to do! Try '!pixel say <your message>' or '!pixel react <topic>'.")
            return

        parts = args.split(maxsplit=1)
        command_verb = parts[0].lower()
        text_to_process = parts[1] if len(parts) > 1 else None

        if command_verb == "say" and text_to_process:
            print(f"Received '!pixel say' command from {ctx.author.name}")
            await audio_task_queue.put(('tts', text_to_process)) # Put text in queue
            await ctx.send(f"Okay @{ctx.author.name}, Pixel will say that!")

        elif command_verb == "react" and text_to_process:
            print(f"Received '!pixel react' command from {ctx.author.name}")
            loop = asyncio.get_running_loop()
            try:
                 # Generate reaction using Gemini first
                 reaction_text = await loop.run_in_executor(None, get_pixel_reaction_text_sync, text_to_process)
                 await audio_task_queue.put(('tts', reaction_text)) # Put generated text in queue
                 await ctx.send(f"Okay @{ctx.author.name}, Pixel will react to that!")
            except Exception as e:
                 print(f"Error generating Gemini reaction in executor: {e}")
                 await ctx.send(f"@{ctx.author.name}, Pixel's brain fizzled trying to react to that.")
        else:
            await ctx.send(f"@{ctx.author.name}, hmm? Try '!pixel say <your message>' or '!pixel react <topic>'.")

    async def audio_processor(self):
        """Background task to process audio requests (TTS & SFX) from the queue."""
        print("Audio processor task started.")
        while True:
            try:
                audio_type, data = await audio_task_queue.get()
                print(f"\nProcessing audio task: Type={audio_type}")

                self._is_speaking.set() # Signal that speech/sfx is starting
                original_volume = pygame.mixer.music.get_volume()
                pygame.mixer.music.set_volume(MUSIC_VOLUME_LOW)
                print(f"Lowering music volume to {MUSIC_VOLUME_LOW}")
                time.sleep(0.2) # Allow volume change

                sound_object = None
                duration = 0
                success = False

                if audio_type == 'tts':
                    text_to_speak = data
                    print(f"Pixel's response: {text_to_speak}")
                    voice_name = "en-US-JennyNeural"
                    ssml_string = f"""
                    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
                        <voice name='{voice_name}'>
                            <mstts:express-as style='cheerful'>
                                <prosody rate='-30.00%' pitch='-25.00%'>
                                    {html.escape(text_to_speak)}
                                </prosody>
                            </mstts:express-as>
                        </voice>
                    </speak>
                    """
                    loop = asyncio.get_running_loop()
                    audio_data = await loop.run_in_executor(None, synthesize_speech_to_buffer_sync, ssml_string)
                    if audio_data:
                        try:
                            sound_object = pygame.mixer.Sound(buffer=audio_data)
                            duration = sound_object.get_length()
                            print(f"Synthesized TTS (duration: {duration:.2f}s)")
                            success = True
                        except Exception as e: print(f"Error loading TTS buffer into pygame: {e}")
                    else: print("TTS Synthesis failed.")

                elif audio_type == 'sfx':
                    sfx_path = data
                    if not os.path.exists(sfx_path): print(f"ERROR: SFX file not found: {sfx_path}")
                    else:
                        try:
                            sound_object = pygame.mixer.Sound(sfx_path)
                            duration = sound_object.get_length()
                            print(f"Loaded SFX: {sfx_path} (duration: {duration:.2f}s)")
                            success = True
                        except Exception as e: print(f"Error loading SFX into pygame: {e}")

                # --- Play the sound if loaded successfully ---
                if success and sound_object:
                    try:
                        print(f"Playing {audio_type}...")
                        sound_object.play()
                        # WARNING: This sleep blocks the event loop. Not ideal.
                        await asyncio.sleep(duration + 0.3) # Use asyncio.sleep, wait for playback
                        print(f"{audio_type} playback finished.")
                    except Exception as e: print(f"Error playing {audio_type}: {e}")
                    finally:
                         if sound_object: del sound_object; sound_object = None # Clean up sound

                # --- Restore Volume and Signal ---
                pygame.mixer.music.set_volume(MUSIC_VOLUME_NORMAL)
                print(f"Restoring music volume to {MUSIC_VOLUME_NORMAL}")
                self._is_speaking.clear() # Signal that speech/sfx is finished
                audio_task_queue.task_done()
                print("Audio task processed.")

            except asyncio.CancelledError: print("Audio processor task cancelled."); break
            except Exception as e:
                print(f"Error in audio processor task: {e}")
                self._is_speaking.clear() # Ensure event is cleared on error
                pygame.mixer.music.set_volume(MUSIC_VOLUME_NORMAL) # Restore volume on error
                audio_task_queue.task_done() # Mark task done even on error to avoid blockage
                await asyncio.sleep(5) # Avoid rapid error loops

    async def music_player(self):
        """Background task to play music when Pixel isn't speaking."""
        print("Music player task started.")
        await asyncio.sleep(2) # Initial delay
        play_next_music_track() # Start first track

        while True:
            try:
                # If Pixel is speaking OR music is already playing, wait.
                if self._is_speaking.is_set() or pygame.mixer.music.get_busy():
                    await asyncio.sleep(1) # Check again in 1 second
                    continue

                # If not speaking and music stopped, play next track
                print("\nMusic track finished or stopped, playing next.")
                play_next_music_track()
                await asyncio.sleep(1) # Small delay after starting track

            except asyncio.CancelledError: print("Music player task cancelled."); break
            except Exception as e:
                print(f"Error in music player task: {e}")
                await asyncio.sleep(10) # Wait longer after an error

    async def lsf_fetcher(self):
        """Background task to periodically fetch LSF posts and queue reactions."""
        print("LSF fetcher task started.")
        await asyncio.sleep(10) # Initial delay before first fetch

        while True:
            try:
                print(f"\n--- Waiting for LSF fetch interval ({FETCH_INTERVAL_SECONDS}s) ---")
                await asyncio.sleep(FETCH_INTERVAL_SECONDS)

                print(f"\n--- Time to fetch LSF posts ---")
                loop = asyncio.get_running_loop()
                post_titles = await loop.run_in_executor(None, get_lsf_top_posts_sync, POST_LIMIT)

                if post_titles:
                    print("\n>>> Queueing Pixel reactions for LSF Top Posts <<<")

                    # Queue Stinger
                    await audio_task_queue.put(('sfx', DRAMA_STINGER_SFX))

                    # Queue Intro Line
                    intro_text = "Hold up, hold up! We got some breaking TEA coming in hot! Let's get riiiight into the drama!"
                    await audio_task_queue.put(('tts', intro_text))

                    # Queue Reactions for each post title
                    for i, title in enumerate(post_titles):
                        print(f"Generating reaction for Post {i+1}/{len(post_titles)}...")
                        # Run Gemini call in executor
                        reaction_text = await loop.run_in_executor(None, get_pixel_reaction_text_sync, title)
                        await audio_task_queue.put(('tts', reaction_text))
                        await asyncio.sleep(0.5) # Small delay between queueing reactions

                    print("Finished queueing LSF segment.")
                else:
                    print("No LSF posts fetched this interval.")

            except asyncio.CancelledError: print("LSF fetcher task cancelled."); break
            except Exception as e:
                print(f"Error in LSF fetcher task: {e}")
                await asyncio.sleep(60) # Wait a minute after an error before retrying fetch

# --- Main Execution ---
if __name__ == "__main__":
    bot = PixelBot()
    try:
        print("Starting Twitch bot...")
        bot.run()
    except KeyboardInterrupt:
        print("\nCtrl+C received, shutting down.")
    finally:
        # Clean up pygame mixer if it was initialized
        if pygame.mixer.get_init():
            pygame.mixer.quit()
            print("Pygame mixer quit.")
        print("Bot shutdown complete.")

