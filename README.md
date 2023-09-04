# good-boy
> Hello, my name is Silas, I'm a bot for messing around in Discord voice and text chat!

Discord's 'new' slash-command API will give you a list of commands I support and how to use them.
But, here's a high level overview of the commands I currently support.

## Currently supported
| Command                               | Description                         |
| ------------------------------------- | ----------------------------------- |
| `\rng roll $whole $min $max`          | Roll a random number.               |
| `\rng pick $number $repeats $options` | Pick one or more items from a list. |

## Backlog
| Command                       | Description                                         |
| ----------------------------- | --------------------------------------------------- |
| `\voice join`                 | Join your voice channel.                            |
| `\voice leave`                | Leave your voice channel.                           |
| `\voice volume $new_volume`   | Change the volume of current audio.                 |
| `\voice stop`                 | Stop playing the current audio.                     |
| `\library list`               | List the audio in my sound library.                 |
| `\library volume $new_volume` | Change volume of future sound library audio.        |
| `\library play $file`         | Play audio from my sound library.                   |
| `\library save`               | Add audio to my sound library.                      |
| `\library get $file`          | Get audio from my sound library.                    |
| `\library remove $file`       | Remove audio from my sound library.                 |
| `\tts play $text`             | Say some text in voice chat.                        |
| `\tts name $new_name`         | Change the spoken name TTS calls you.               |
| `\tts language $new_language` | Change the language TTS uses for you when speaking. |
| `\youtube show $url`          | Play video and audio from a Youtube video.          |
| `\youtube play $url`          | Play audio from a Youtube video.                    |
| `\youtube volume $new_volume` | Change the volume of future Youtube audio.          |
| `\spotify play $url`          | Play audio from a Spotify song.                     |
| `\spotify volume $new_volume` | Change the volume of future Spotify audio.          |
| `\listen $on_or_off`          | Set whether to be listened to for commands or not.  |
