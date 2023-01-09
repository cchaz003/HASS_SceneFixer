
# HASS_SceneFixer
A python script that monitors a Home Assistant scenes file for changes and fixes missing entities

I built this to solve the problem that arises when you edit a scene with entities that are unavailable and the unavailable state gets saved to the scene (overwriting the previous settings for that entity). For example, if you have a light set to red in a scene and go to edit that scene while that light is offline then the "set to red" setting gets overwritten with "device unavailable". The next time that scene is activated and the light is available it wont do anything as the "set to red" setting is gone from the scene. 

What this script does is make a backup of the `scenes.yaml` file and monitor the original for updates (modification time). When a modification is detected it searches for entities whose state is marked as "unavailable" and attempts to recover the state (if there was one available) from the backup file. It then sends a '1' through MQTT which can be picked up by HASS through this mqtt entry in `configuration.yaml`:

    mqtt:
      binary_sensor:
        name: "Scene Fixer Notifier"
        state_topic: "homeassistant/scenesUpdate"
        payload_on: "1"
        payload_off: "0"
        off_delay: 2


An automation can then be triggered to reload the scenes file:

    alias: Scene Fixer
    description: ""
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.scene_fixer_notifier
        to: "on"
    condition: []
    action:
      - service: scene.reload
        data: {}
    mode: single


## Installation:

Included is a docker-compose file that can be used in conjunction with your HASS setup (my HASS it setup via docker so it only seemed natural) or this can be run as a standalone script. Make sure to update the various settings at the top of the script to match your setup before using.

To run locally you must first install the requirements with 

    pip install -r requirements.txt

Then run using

    python3 sceneFixer.py


## Something not working?

If you have a question/problem feel free to post in the issues tracker and if I have an easy/quick fix or can point you in the right direction I'm happy to do so but for anything that might take more than 10 minutes I'm less likely to get around to it in any sort of timely manner (just trying being honest). This script is the kind of thing that I'm not likely to revisit unless I run into issues myself but feel free to fix things if they seem like a problem and I'll merge them in if it makes sense. Mainly this is something I wanted to put out into the world since I'm sure someone else will also google this issue hoping that someone already did the hard part. 





