# good-boy
> Hello, my name is Silas, I'm a bot for messing around in Discord voice and text chat!

Discord's 'new' slash-command API will give you a list of commands I support and how to use them.
But, here's a high level overview of the commands I currently support.

## Currently supported
| Command                               | Description                                          |
| ------------------------------------- | ---------------------------------------------------- |
| `/rng roll $whole $min $max`          | Roll a random number.                                |
| `/rng pick $number $repeats $options` | Pick one or more items from a list.                  |
| `/voice join`                         | Join the voice channel you are in.                   |
| `/voice leave`                        | Leave the voice channel you are in.                  |
| `/voice stop`                         | Stop playing the audio I am currently playing.       |
| `/tts play $text`                     | Say specified text on your behalf in voice chat.     |
| `/tts spoken_name $new_spoken_name`   | Change the name/pronounciation TTS refers to you by. |
| `/tts language $new_language`         | Change the language/accent TTS speaks in for you.    |

## Backlog
| Command                       | Description                                         |
| ----------------------------- | --------------------------------------------------- |
| `/voice volume $new_volume`   | Change the volume of current audio.                 |
| `/voice queue $action $arg  ` | See or modify my audio queue.                       |
| `/library list`               | List the audio in my sound library.                 |
| `/library volume $new_volume` | Change the volume of future sound library audio.    |
| `/library play $file`         | Play audio from my sound library in voice chat.     |
| `/library save`               | Add audio to my sound library.                      |
| `/library get $file`          | Get audio from my sound library.                    |
| `/library delete $file`       | Remove audio from my sound library.                 |
| `/youtube show $url`          | Play video and audio from a Youtube video/playlist. |
| `/youtube play $url`          | Play audio from a Youtube video/playlist.           |
| `/youtube volume $new_volume` | Change the volume of future Youtube audio/playlist. |
| `/spotify play $url`          | Play audio from a Spotify song/playlist.            |
| `/spotify volume $new_volume` | Change the volume of future Spotify audio/playlist. |
| `/listen $on_or_off`          | Set whether to be listened to for commands or not.  |
| `/poll $subject $options`     | Create a basic poll in this text chat.              |
| `/remind $when $what`         | Set a reminder for yourself in this text chat       |
| `/admin blacklist $user $why` | Ban someone (ex. annoying/abusive) from using me.   |
| `/admin unblacklist $user`    | Unban someone previously banned from using me.      |
| `/admin pause`                | Make me unresponsinve to non-admin messages.        |
| `/admin unpause`              | Make me responsive to non-admin messages.           |
| `/admin kill`                 | Disconnect me from the server until I am restarted. |
