# QGIS Sound Effects Plugin

This plugin plays sound effects when certain actions are performed in QGIS.
After installation, add the **Sound Effects toolbar** to your workspace to control the plugin.


### Functionality

Currently supported actions are:

- Enable/Disable all sound effects from the plugin toolbar.
- Enable/Disable sound effects for any specific event from the settings dialog.
- Select which sound effect, and at what volume, will be played for each event from the settings dialog.
- Test the selected sound effect for each event from the settings dialog.
- The `Play Sound Effect` processing algorithm, also works within the graphic modeler.
- The `Play Audio File` processing algorithm, also works within the graphic modeler.
- The `Say Some Text` processing algorithm, also works within the graphic modeler.


### Supported Events
<a id="events"></a>

- Processing Success - when a processing algorithm completes successfully.
- Processing Failure - when a processing algorithm fails.
- Layers Changed - when a layer is added or removed from the map canvas.
- Render Complete - when the map canvas finishes rendering.
- Render Error - when the map canvas fails to render correctly.
- Zoom In - when the user zooms in the map canvas.
- Zoom Out - when the user zooms out the map canvas.

> [!NOTE]
> Yes, there is a plan to split the `Layers Changed` event into `Layer Added` and `Layer Removed` events in the future.

### Installation

Install the plugin from the QGIS Plugin Repository, I upload the newest version whenever it is ready.

### Usage

Once the plugin is installed, add the **Sound Effects Toolbar** to your workspace to control the plugin.
You can toggle all sound effects on/off from the checkbox on the toolbar, or click on the settings button ( <img style="width:24px;height:24px" src="qgs_effects_config_icon.png"/> ) to open the settings dialog.


### Attribution

* success.wav - (SFX-Success!.wav) by HenryRichard -- https://freesound.org/s/448274/ -- License: Creative Commons 0
* fail.wav - Fail Jingle (stereo mix) by unfa -- https://freesound.org/s/181351/ -- License: Creative Commons 0
* retro_jump.wav - Retro Jump SFX  by suntemple -- https://freesound.org/s/253178/ -- License: Creative Commons 0
* sprout.wav - Comical Sprout by Jofae -- https://freesound.org/s/364692/ -- License: Creative Commons 0
* access_denied_buzz.wav - acess denied buzz by Jacco18 -- https://freesound.org/s/419023/ -- License: Creative Commons 0
* pop.wav - Pop sound by deraj -- https://freesound.org/s/202230/ -- License: Creative Commons 0
* synth-glide.wav - Synth Glide Effect 3 by nomiqbomi -- https://freesound.org/s/578659/ -- License: Creative Commons 0
* gliding_beep.wav - Gliding Beep long.aif by TiesWijnen -- https://freesound.org/s/233574/ -- License: Creative Commons 0
* burp.wav - Burp - Belch by Jagadamba -- https://freesound.org/s/254280/ -- License: Attribution NonCommercial 4.0
* fart.wav - Short, definite fart by ycbcr -- https://freesound.org/s/249583/ -- License: Creative Commons 0
* woodenfrog.wav - perc_woodenfrog.wav by harrisonlace -- https://freesound.org/s/611501/ -- License: Creative Commons 0
* tada.wav - Tada Fanfare A by plasterbrain -- https://freesound.org/s/397355/ -- License: Creative Commons 0
* laser_shot.wav - Retro, Laser Shot 04.wav by MATRIXXX_ -- https://freesound.org/s/414888/ -- License: Creative Commons 0
* good_answer_harp.wav - Good answer harp glissando.wav by oggraphics -- https://freesound.org/s/610703/ -- License: Creative Commons 0
* sad_trombone.wav - Sad Trombone.wav by Benboncan -- https://freesound.org/s/73581/ -- License: Attribution 4.0