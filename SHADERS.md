# Shaders

A **shader** is what the whole picture goes through before it reaches the screen: a stack of **effects**, applied one after the other. You build one in the game (from a menu of about 103 effects, no code), keep it, and it works on every map.

- **Backslash** (`\`) shows the next shader, **Shift + Backslash** the previous one, round and round. The game starts on the first one (`default`, which is the picture as it is).
- **`]`** opens a menu on the right of the window to do all of it with the mouse. **T** opens the chat, where the `.fx` and `.shader` commands do the same. Use either or both, they change the same thing.
- The built-in shaders can't be changed or deleted. Yours are saved in `shaders/custom` (one `.json` file each, change `SHADER_DIR` in `.env` to move them), come after the built-in ones in alphabetical order, and are not tied to a map.

## The stack

Effects are layers: the first one is applied to the picture of the game, the next one to the result, and so on. The one on top (the highest number) is applied last. Any effect can be in the stack any number of times, in any order, and the order matters: a vignette before a dither is dithered, a vignette after it is smooth.

```
.fx add vignette amount=0.6        puts it on top of the stack
.fx add dither bayer8 4 2          the same effect can come again, and again
.fx stack                          what is on the screen (the top one first)
.fx up 1                           move effect 1 up (so it is applied after more of the others)
.fx swap 1 3                       swap two effects
.fx off 2                          switch one off without taking it out
.fx mix 3 0.4                      use only 40% of effect 3
.fx clear                          nothing on the screen: the picture as it is
.shader save my-look               keep what is on the screen as a shader of your own
```

## Settings

Every effect has settings (`.fx info <effect>` lists them). Write them as `name=value`, in any order, or only the values in the order `.fx info` lists them; both mean the same:

```
.fx add dither type=bayer8 levels=4 size=2
.fx add dither bayer8 4 2
.fx add dither levels=4 cluster         (a mix: the values without a name fill the settings you did not name)
.fx set 2 levels=8 type=noise           (change an effect that is in the stack: its number is in .fx stack)
.fx set 2 levels 8                      (also: name, then value)
.fx reset 2 levels                      (back to what it starts as)
```

| Kind | How to write it |
| --- | --- |
| number | `0.5`, `12` (a number outside what a setting takes is moved into it, and the game says so) |
| yes or no | `yes`, `no` (also `on`, `off`, `true`, `false`, `1`, `0`) |
| one of a list | its name (`bayer8`), its number in `.fx info` (`3`), or the start of its name when that is clear (`bay` is not, `clu` is `cluster`) |
| color | `#ff8000`, `#f80`, `1,0.5,0` (0 to 1) or `255,128,0` (0 to 255), or a name: black, white, gray, silver, red, green, blue, yellow, cyan, magenta, orange, pink, purple, brown, teal, navy, lime, gold, sky |
| point | `0.5,0.5` (x,y over the screen from 0 to 1, `0,0` is the bottom left) |

Every effect also has **`mix`** (0 to 1: how much of the effect is used, 0 is none, 1 is all of it); the ones that move in time have **`speed`** (how fast, 0 stops it, negative runs it backwards) and the ones that use random numbers have **`seed`** (another number, another pattern). These three can only be written by name (`.fx set 2 mix=0.5`). `.fx speed <x>` changes the speed of every animation at once.

Sizes in pixels (the size of a dither pixel, the width of an outline, the radius of a blur, ...) are measured on a screen 1080 pixels high and grow and shrink with the window, so an effect looks the same at every resolution.

## The menu (`]`)

A black panel on the right (`GUI_WIDTH`, `GUI_ALPHA` and `GUI_FONT_SIZE` in `.env.pre`); `]` or **Escape** closes it (while a line is being typed, Escape only leaves the line, the next one closes the menu); the mouse becomes a pointer while it is open and the view does not turn (you can still walk, unless you are typing in one of its lines). The panel has three tabs:

- **stack**: the effects on the screen, the top of the list is the top of the stack. Click an effect to open its settings. Buttons on every effect: switch on / off, up, down, copy, remove. A setting is a line to drag (click the number to type one, **right click** puts it back, **Shift + wheel** changes it a little), a yes / no to click, a list to click through (right click goes back), a color (click the swatch for red, green and blue lines, click the number to type a color) or a point (two lines). Also: expand / collapse all, clear, undo, redo and the speed of the animations.
- **add**: every effect with what it does; type in the search line or pick a category; click one to put it on top of the stack.
- **library**: every shader (the one on the screen has a bar next to it, a `*` means it was changed since it was saved). Click one to show it. Type a name and press Enter (or click save) to keep what is on the screen; yours can be renamed, copied and deleted (delete asks you to click twice); any shader, built in or yours, can be copied.

The mouse wheel scrolls a tab. The line at the bottom says what the pointer is over, and what the last action did.

## Commands


### `.fx`

| Command | What it does |
| --- | --- |
| `.fx list [category]` | the menu of effects (categories: color, retro, blur, edges, distort, overlay) |
| `.fx info <effect>` | what an effect does and all its settings |
| `.fx add <effect> [settings]` | put an effect on top of the stack (it is applied after the others); settings are name=value, or just the values in the order .fx info lists them: .fx add dither bayer8 4 2 |
| `.fx insert <n> <effect> [settings]` | put an effect at place n of the stack |
| `.fx stack` | the effects that are on the screen, the top one is applied last (on top of the others), 1 is applied first |
| `.fx set <n> <settings>` | change settings of effect n: .fx set 2 levels=4 type=bayer4 (or .fx set 2 levels 4) |
| `.fx reset <n> [setting]` | put one setting (or all) of effect n back to what it starts as |
| `.fx remove <n>` | take effect n out of the stack |
| `.fx move <n> <to>` | move effect n to place <to> |
| `.fx up <n> [steps] / .fx down <n> [steps]` | move an effect up (towards the top: applied after more of the others) or down |
| `.fx top <n> / .fx bottom <n>` | make effect n the last / the first one applied |
| `.fx swap <a> <b>` | swap two effects |
| `.fx dup <n>` | copy effect n (right after it) |
| `.fx on <n> / .fx off <n> / .fx toggle <n>` | switch an effect on or off without removing it |
| `.fx mix <n> <0-1>` | how much of effect n is used (0 none, 1 all) |
| `.fx clear` | take every effect out: the picture is shown as it is |
| `.fx undo [n] / .fx redo [n]` | take back / do again changes to the stack |
| `.fx speed [x]` | the speed of every animation (1 is normal, 0 freezes them) |
| `.fx cost` | how many full-screen passes the stack needs |

### `.shader`

| Command | What it does |
| --- | --- |
| `.shader list` | every shader (built-in ones first, then yours in alphabetical order); the one on the screen is marked with * |
| `.shader use <name \| n>` | show a shader (Backslash goes through them all, Shift+Backslash goes back) |
| `.shader next / .shader prev` | the next / previous one |
| `.shader save <name> [overwrite]` | keep what is on the screen as a new shader of your own (it joins the list and Backslash) |
| `.shader add <name \| n>` | put the effects of a shader on top of the stack |
| `.shader reset` | throw away your changes: the shader as it was saved |
| `.shader rename <name> <new>` | rename a shader of yours |
| `.shader copy <name> <new>` | copy any shader (also a built-in one) into one of yours |
| `.shader delete <name>` | delete a shader of yours for good (repeat the command to confirm) |
| `.shader info [name]` | what is in a shader |
| `.fx clear` | the way to "no shader": nothing on the screen (or .shader use default) |

`.help fx` and `.help shader` say the same in the game. Tab finishes command words, effect names, settings (`type=`), the choices of a setting and shader names.

## Built-in shaders

In the order Backslash goes through them (yours come after, in alphabetical order). Copy any of them (`.shader copy <name> <new>`) to start from it.

| # | Shader | What | Effects, in the order they are applied |
| --- | --- | --- | --- |
| 1 | `default` | the picture as it is | no effects |
| 2 | `edge` | the edges of everything in blue on black (the first edge shader) | edge |
| 3 | `dither` | only two colors, drawn with an 8x8 Bayer pattern (the first dither shader) | dither |
| 4 | `noise` | black and white grain: every pixel is compared with a random number (the first noise shader) | dither |
| 5 | `cinematic` | a film look: teal shadows, warm lights, wide bars, a little grain | contrast, splittone, vignette, grain, letterbox |
| 6 | `noir` | black and white, hard contrast, dark corners, grain | grayscale, contrast, vignette, grain |
| 7 | `sepia` | an old brown photograph | sepia, vignette, grain |
| 8 | `old-film` | an old film: brown, grainy, flickering, a little shaky | sepia, contrast, shake, pulse, grain, vignette |
| 9 | `dusk` | warm orange light fading to purple, with a soft glow | temperature, gradient, bloom, vignette |
| 10 | `dream` | soft, glowing and a little warm, with light leaking in | softfocus, bloom, temperature, saturation, lightleak |
| 11 | `crt` | an old tube screen: bent glass, scanlines, a red-green-blue mask, a little glow | chromatic, bloom, shadowmask, scanlines, curvature, vignette |
| 12 | `vhs` | a worn video tape | vhs, chromatic, scanlines |
| 13 | `gameboy` | four shades of green on a tiny screen | pixelate, palette, vignette |
| 14 | `terminal` | green letters on black | ascii, scanlines, curvature |
| 15 | `matrix` | falling-code green: letters that glow | ascii, bloom |
| 16 | `pixelart` | chunky pixels and a few colors | lowres, saturation |
| 17 | `pencil` | a pencil drawing on paper | sketch |
| 18 | `comic` | flat colors, black outlines and print dots | saturation, toon, halftone |
| 19 | `halftone` | dots of four inks, like a printed page | halftone |
| 20 | `crosshatch` | a pen drawing made of crossing lines | crosshatch |
| 21 | `stipple` | a drawing made of dots | stipple |
| 22 | `blueprint` | white lines on blue paper | edge, vignette |
| 23 | `ascii` | the picture drawn with letters | ascii |
| 24 | `nightvision` | green night vision goggles | nightvision |
| 25 | `thermal` | a heat camera | thermal |
| 26 | `xray` | an x-ray picture | xray |
| 27 | `infrared` | an infrared photo: plants glow white | infrared |
| 28 | `neon` | glowing neon outlines on dark | neon, bloom |
| 29 | `rain` | cold, grey and rainy, with distant lightning | temperature, saturation, rain, flash, vignette |
| 30 | `snowfall` | cold, quiet snow | temperature, saturation, snow, vignette |
| 31 | `fireflies` | glowing specks floating in the air | dust, bloom, vignette |
| 32 | `underwater` | under the surface: wobbling, blue-green, light patterns | underwater, blur, vignette |
| 33 | `drunk` | the world sways and swims | noisewarp, sway, chromatic, blur |
| 34 | `acid` | colors that never stop turning, and wavy | hue, saturation, wave, chromatic |
| 35 | `kaleido` | a slowly turning kaleidoscope | kaleidoscope |
| 36 | `vaporwave` | pink and cyan, glowing, with scanlines | saturation, gradient, bloom, chromatic, scanlines |
| 37 | `disco` | turning colors and a beat | hue, zoompulse, bloom, vignette |
| 38 | `tiny-planet` | the world wrapped around into a ball | polar |
| 39 | `fisheye` | a fisheye lens | fisheye, vignette |
| 40 | `toy-model` | only a strip is sharp, the colors are strong: everything looks like a toy | tiltshift |
| 41 | `glitch` | a broken digital picture | glitch, rgbsplit, scanlines |
| 42 | `earthquake` | the camera shakes hard | shake |
| 43 | `zoom-beat` | a thump that zooms and splits the colors, twice a second | zoompulse, chromatic |
| 44 | `dither-color` | a few colors per channel, with a 4x4 pattern | dither |
| 45 | `dither-print` | two colors drawn with round dots, like a newspaper | dither |
| 46 | `dither-lines` | two colors drawn with slanted lines | dither |

## The effects (103)

Blend modes (in `blend` and `gradient`): `normal`, `multiply`, `screen`, `overlay`, `softlight`, `hardlight`, `add`, `subtract`, `difference`, `dodge`, `burn`. The settings that say what to show where the picture is moved off the screen (`edge`): `clamp`, `mirror`, `repeat`, `black`.

### color: colors and tone: brightness, hue, palettes, tints

| Effect | What it does |
| --- | --- |
| [`tint`](#tint) | colors the whole picture |
| [`brightness`](#brightness) | makes everything lighter or darker |
| [`contrast`](#contrast) | pushes the colors away from (or towards) the middle grey |
| [`exposure`](#exposure) | like the exposure of a camera: every stop doubles the light |
| [`gamma`](#gamma) | brightens or darkens the middle tones and leaves black and white alone |
| [`levels`](#levels) | sets which brightness is black and which is white |
| [`saturation`](#saturation) | makes the colors stronger or weaker |
| [`vibrance`](#vibrance) | like saturation, but mostly for the colors that are weak |
| [`hue`](#hue) | turns all the colors around the color wheel (let it cycle for a rainbow shift) |
| [`temperature`](#temperature) | warm (orange) or cool (blue), and green or magenta |
| [`grayscale`](#grayscale) | takes the color out |
| [`sepia`](#sepia) | the brown tint of old photographs |
| [`invert`](#invert) | turns the colors into their opposites |
| [`duotone`](#duotone) | only two colors: one for the dark, one for the light, and the tones between |
| [`gradientmap`](#gradientmap) | colors the picture by brightness with a gradient of up to 5 colors |
| [`posterize`](#posterize) | only a few steps of color or brightness |
| [`threshold`](#threshold) | every pixel becomes one of two colors: light or dark |
| [`mixer`](#mixer) | mixes the red, green and blue channels into each other (a channel mixer) |
| [`swap`](#swap) | swaps the color channels around |
| [`balance`](#balance) | tints the dark, middle and light parts of the picture separately (grey 0.5 changes nothing) |
| [`splittone`](#splittone) | one color into the dark and another into the light, like in film grading |
| [`matte`](#matte) | lifts the black to a color, for a faded film look |
| [`selectivecolor`](#selectivecolor) | keeps one color and takes the color out of everything else |
| [`palette`](#palette) | only the colors of an old computer or console: every pixel becomes the nearest color of a fixed palette |

#### tint

Colors the whole picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffbf80` | the color |
| `strength` | number 0 to 1 | `0.6` | how much of the tint is used |
| `mode` | one of multiply, add, screen | `multiply` | how the color goes over the picture |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### brightness

Makes everything lighter or darker.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number -1 to 1 | `0.2` | how much to add (negative darkens) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### contrast

Pushes the colors away from (or towards) the middle grey.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 4 | `1.4` | above 1 more contrast, below 1 less |
| `pivot` | number 0 to 1 | `0.5` | the brightness that stays as it is |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### exposure

Like the exposure of a camera: every stop doubles the light.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `stops` | number -5 to 5 | `0.7` | how many stops lighter (negative: darker) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### gamma

Brightens or darkens the middle tones and leaves black and white alone.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `value` | number 0.1 to 5 | `1.5` | above 1 lighter middle tones, below 1 darker |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### levels

Sets which brightness is black and which is white.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `black` | number 0 to 1 | `0.1` | everything at or below this becomes black |
| `white` | number 0 to 1 | `0.9` | everything at or above this becomes white |
| `gamma` | number 0.1 to 5 | `1` | the middle tones |
| `out_black` | number 0 to 1 | `0` | the darkest the result can be |
| `out_white` | number 0 to 1 | `1` | the lightest the result can be |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### saturation

Makes the colors stronger or weaker.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 4 | `1.6` | 0 is grey, 1 is as it was, above 1 stronger |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### vibrance

Like saturation, but mostly for the colors that are weak.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number -1 to 2 | `0.8` | how much |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### hue

Turns all the colors around the color wheel (let it cycle for a rainbow shift).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `shift` | number -180 to 180 | `60` | degrees to turn the colors |
| `cycle` | number -360 to 360 | `0` | degrees per second the colors keep turning |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### temperature

Warm (orange) or cool (blue), and green or magenta.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `warmth` | number -1 to 1 | `0.4` | positive warmer, negative cooler |
| `tint` | number -1 to 1 | `0` | positive towards magenta, negative towards green |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### grayscale

Takes the color out.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `mode` | one of luma, average, lightness, red, green, blue, desaturate | `luma` | how the grey is worked out (red, green, blue: that channel only) |
| `strength` | number 0 to 1 | `1` | how much |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### sepia

The brown tint of old photographs.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number 0 to 1 | `1` | how much |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### invert

Turns the colors into their opposites.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `mode` | one of all, red, green, blue, brightness | `all` | which colors (brightness: only light and dark swap, the hue stays) |
| `strength` | number 0 to 1 | `1` | how much |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### duotone

Only two colors: one for the dark, one for the light, and the tones between.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `dark` | color (#rrggbb, r,g,b or a name like orange) | `#0d0040` | the color of the dark |
| `light` | color (#rrggbb, r,g,b or a name like orange) | `#ffcc66` | the color of the light |
| `bias` | number -1 to 1 | `0` | moves the middle towards the dark (negative) or the light (positive) |
| `contrast` | number 0.1 to 4 | `1` | how sharply dark turns to light |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### gradientmap

Colors the picture by brightness with a gradient of up to 5 colors.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color1` | color (#rrggbb, r,g,b or a name like orange) | `#00001a` | the darkest color |
| `color2` | color (#rrggbb, r,g,b or a name like orange) | `#800080` | the second color |
| `color3` | color (#rrggbb, r,g,b or a name like orange) | `#ff4c33` | the third color |
| `color4` | color (#rrggbb, r,g,b or a name like orange) | `#ffe666` | the fourth color |
| `color5` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the lightest color |
| `count` | whole number 2 to 5 | `4` | how many of the colors are used (they are spread evenly over the brightness) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### posterize

Only a few steps of color or brightness.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `levels` | whole number 2 to 32 | `5` | how many steps |
| `mode` | one of rgb, brightness | `rgb` | every color channel on its own, or only the brightness |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### threshold

Every pixel becomes one of two colors: light or dark.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `level` | number 0 to 1 | `0.5` | the brightness where it turns from dark to light |
| `dark` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the dark |
| `light` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the light |
| `softness` | number 0 to 0.5 | `0` | how soft the edge between them is |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### mixer

Mixes the red, green and blue channels into each other (a channel mixer).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `red_r` | number -2 to 2 | `1` | how much of the red goes into the new red |
| `red_g` | number -2 to 2 | `0` | how much of the green goes into the new red |
| `red_b` | number -2 to 2 | `0` | how much of the blue goes into the new red |
| `green_r` | number -2 to 2 | `0` | red into the new green |
| `green_g` | number -2 to 2 | `1` | green into the new green |
| `green_b` | number -2 to 2 | `0` | blue into the new green |
| `blue_r` | number -2 to 2 | `0` | red into the new blue |
| `blue_g` | number -2 to 2 | `0` | green into the new blue |
| `blue_b` | number -2 to 2 | `1` | blue into the new blue |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### swap

Swaps the color channels around.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `order` | one of rgb, rbg, grb, gbr, brg, bgr | `bgr` | which channel goes where (bgr: red and blue change places) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### balance

Tints the dark, middle and light parts of the picture separately (grey 0.5 changes nothing).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `shadows` | color (#rrggbb, r,g,b or a name like orange) | `#6680a6` | the tint of the dark parts |
| `midtones` | color (#rrggbb, r,g,b or a name like orange) | `#808080` | the tint of the middle |
| `highlights` | color (#rrggbb, r,g,b or a name like orange) | `#998066` | the tint of the light parts |
| `amount` | number 0 to 3 | `2` | how strong |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### splittone

One color into the dark and another into the light, like in film grading.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `shadow` | color (#rrggbb, r,g,b or a name like orange) | `#1a408c` | the color of the dark |
| `highlight` | color (#rrggbb, r,g,b or a name like orange) | `#ffbf66` | the color of the light |
| `balance` | number -1 to 1 | `0` | moves the middle towards the shadows (negative) or the highlights (positive) |
| `strength` | number 0 to 1 | `0.7` | how strong |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### matte

Lifts the black to a color, for a faded film look.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#261a4c` | the color black becomes |
| `amount` | number 0 to 1 | `0.45` | how much |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### selectivecolor

Keeps one color and takes the color out of everything else.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `hue` | number 0 to 360 | `0` | the color to keep, in degrees on the color wheel (0 red, 120 green, 240 blue) |
| `range` | number 1 to 180 | `45` | how far from that hue is kept |
| `softness` | number 0 to 90 | `25` | how soft the edge is |
| `strength` | number 0 to 1 | `1` | how much of the other colors is taken out |
| `boost` | number 0 to 3 | `1` | how strong the kept color is made |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### palette

Only the colors of an old computer or console: every pixel becomes the nearest color of a fixed palette.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `palette` | one of gameboy, cga1, cga0, ega, c64, pico8, sepia4, vaporwave, solarized, green, amber, 1bit, blueprint, sunset | `gameboy` | which palette |
| `strength` | number 0 to 1 | `1` | how much |
| `match` | one of rgb, perceptual | `rgb` | how the nearest color is found |
| `dither` | number 0 to 1 | `0.35` | a little pattern that hides the steps between colors |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

### retro: dithering, pixel looks, old screens and tapes

| Effect | What it does |
| --- | --- |
| [`dither`](#dither) | only a few colors, with the steps between them drawn as a pattern or as noise (many kinds of patterns) |
| [`pixelate`](#pixelate) | big pixels (squares, hexagons or bricks), with an optional gap between them like an LED screen |
| [`lowres`](#lowres) | looks like a low resolution picture with few colors (big pixels, steps of color, a little dither) |
| [`ascii`](#ascii) | draws the picture with letters, brighter parts get fuller ones (. : * o & 8 @ #) |
| [`scanlines`](#scanlines) | dark lines across the picture, like a tube screen |
| [`shadowmask`](#shadowmask) | the red, green and blue dots or stripes of a tube screen |
| [`curvature`](#curvature) | bends the picture like the glass of a tube screen, with dark corners |
| [`interlace`](#interlace) | every other line is dark or shifted, and which lines they are flips all the time |
| [`vhs`](#vhs) | an old video tape: wobbling lines, a rolling bar, smeared colors, noise |
| [`glitch`](#glitch) | a broken digital picture: blocks jump sideways, colors split, parts flip |
| [`chromatic`](#chromatic) | the colors of the picture are pulled apart, like a cheap lens (stronger towards the edges) |
| [`rgbsplit`](#rgbsplit) | the red and blue copies of the picture are shifted apart (an anaglyph or 3D glasses look) |

#### dither

Only a few colors, with the steps between them drawn as a pattern or as noise (many kinds of patterns).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `type` | one of bayer2, bayer4, bayer8, bayer16, cluster, dots, lines, checker, ign, r2, noise | `bayer8` | the pattern: bayer2/4/8/16 are the classic square patterns (bigger is finer), cluster/dots/lines are like print, checker is a chessboard, ign and r2 are smooth blue-noise-like patterns, noise is random like film grain |
| `levels` | whole number 2 to 32 | `2` | how many steps of brightness (2 is only dark and light) |
| `size` | number 1 to 32 | `2` | the size of one dither pixel (measured on a screen 1080 high) |
| `mode` | one of mono, color | `mono` | mono works on the brightness and uses the dark and light colors, color dithers every color channel on its own |
| `dark` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the dark (and of the first step in color mode) |
| `light` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the light |
| `contrast` | number 0.1 to 4 | `1` | below 1 brightens the dark parts so more of a dark picture survives (1 is no change) |
| `black` | number 0 to 0.99 | `0` | anything darker than this is plain dark, so an empty background does not speckle |
| `luma` | one of rec601, rec709, average, max, red, green, blue | `rec601` | how the brightness is worked out in mono mode |
| `spread` | number 0 to 2 | `1` | how strong the pattern is: 0 is a plain cut in the middle, 1 the whole pattern, above 1 more noisy |
| `scale` | number 2 to 64 | `8` | the size of one repeat of the pattern, in dither pixels (cluster, dots, lines and checker) |
| `angle` | number -180 to 180 | `45` | turns the pattern (cluster, dots, lines and checker) |
| `flicker` | number 0 to 120 | `0` | how many times a second the pattern changes (0 keeps it still) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### pixelate

Big pixels (squares, hexagons or bricks), with an optional gap between them like an LED screen.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `size` | number 1 to 256 | `8` | the size of one pixel (measured on a screen 1080 high) |
| `shape` | one of square, hex, brick | `square` | the shape of the pixels |
| `gap` | number 0 to 0.9 | `0` | how much of every pixel is gap (0 is none) |
| `gap_color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the gap |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### lowres

Looks like a low resolution picture with few colors (big pixels, steps of color, a little dither).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `height` | number 16 to 1080 | `180` | how many pixels the screen is high |
| `levels` | whole number 2 to 32 | `6` | how many steps of every color channel |
| `dither` | number 0 to 1 | `0.6` | a little pattern that hides the steps between colors |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### ascii

Draws the picture with letters, brighter parts get fuller ones (. : * o & 8 @ #).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `size` | number 4 to 48 | `8` | the size of one letter (measured on a screen 1080 high) |
| `mode` | one of color, mono, tint | `color` | color uses the color of the picture, mono is grey, tint is one color |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#33ff66` | the color of the letters in tint mode |
| `gain` | number 0.25 to 4 | `1.3` | makes the picture look brighter to the letters (more full ones) |
| `background` | number 0 to 1 | `0.3` | how much of the picture shows behind the letters |
| `invert` | yes or no | `no` | dark letters on a light picture |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### scanlines

Dark lines across the picture, like a tube screen.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number 0 to 1 | `0.35` | how dark the lines are |
| `spacing` | number 1 to 32 | `3` | the distance from one line to the next (measured on a screen 1080 high) |
| `thickness` | number 0.05 to 0.95 | `0.5` | how much of the space between the lines is dark |
| `softness` | number 0 to 1 | `0.3` | how soft the edges of the lines are |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the lines |
| `direction` | one of horizontal, vertical | `horizontal` | which way the lines run |
| `scroll` | number -500 to 500 | `0` | how fast the lines crawl (pixels a second, 0 keeps them still) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### shadowmask

The red, green and blue dots or stripes of a tube screen.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `size` | number 2 to 24 | `6` | the width of one red-green-blue group (measured on a screen 1080 high) |
| `type` | one of aperture, dots, slot | `aperture` | aperture is vertical stripes, dots is staggered dots, slot has gaps between the rows |
| `strength` | number 0 to 1 | `0.6` | how much of the mask is used |
| `boost` | number 0.5 to 3 | `1.15` | makes the picture brighter again (the mask darkens it) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### curvature

Bends the picture like the glass of a tube screen, with dark corners.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.3` | how much the screen bulges |
| `corner` | number 0 to 0.5 | `0.05` | how round the corners of the screen are |
| `border` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color outside the screen |
| `zoom` | number 0.5 to 2 | `1` | above 1 zooms in (hides the dark corners) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### interlace

Every other line is dark or shifted, and which lines they are flips all the time.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number 0 to 1 | `0.5` | how dark the lines of the other field are |
| `spacing` | number 1 to 8 | `1` | the height of one line (measured on a screen 1080 high) |
| `comb` | number 0 to 30 | `3` | how far the other lines are shifted sideways (pixels) |
| `rate` | number 0 to 240 | `30` | how many times a second the lines flip |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### vhs

An old video tape: wobbling lines, a rolling bar, smeared colors, noise.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `jitter` | number 0 to 2 | `0.6` | how much every line wobbles sideways |
| `tracking` | number 0 to 2 | `0.6` | how much the bar that rolls up the screen (and the bottom of the picture) is torn |
| `bleed` | number 0 to 8 | `2` | how much the colors smear sideways |
| `noise` | number 0 to 2 | `0.5` | how much static |
| `fade` | number 0 to 1 | `0.3` | how washed out and dim it is |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### glitch

A broken digital picture: blocks jump sideways, colors split, parts flip.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.3` | how much of the picture is broken |
| `blocks` | number 4 to 200 | `32` | how many rows the picture is cut into |
| `split` | number 0 to 40 | `6` | how far the red and blue are shifted apart in the broken parts (pixels) |
| `rate` | number 0 to 60 | `12` | how many times a second the glitch changes |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### chromatic

The colors of the picture are pulled apart, like a cheap lens (stronger towards the edges).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 10 | `2` | how far apart (as a percent of the screen) |
| `mode` | one of radial, linear | `radial` | radial grows away from the center, linear shifts in one direction |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle of the lens (radial) |
| `angle` | number -180 to 180 | `0` | the direction of the shift (linear) |
| `samples` | whole number 3 to 16 | `6` | how many steps between red and blue (3 is red, green and blue only) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### rgbsplit

The red and blue copies of the picture are shifted apart (an anaglyph or 3D glasses look).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `distance` | number 0 to 100 | `6` | how far apart (pixels, measured on a screen 1080 high) |
| `angle` | number -180 to 180 | `0` | the direction of the shift |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

### blur: blur, sharpen and glow

| Effect | What it does |
| --- | --- |
| [`blur`](#blur) | blurs the picture (a smooth gaussian blur or a flat box blur) |
| [`zoomblur`](#zoomblur) | a blur that streaks away from a point, like speed |
| [`spinblur`](#spinblur) | a blur that turns around a point |
| [`directionalblur`](#directionalblur) | a blur in one direction, like a camera that moved |
| [`tiltshift`](#tiltshift) | only a strip of the picture is sharp, the rest is blurred (makes everything look like a toy model) |
| [`sharpen`](#sharpen) | makes small details crisper |
| [`unsharp`](#unsharp) | makes the picture crisper by adding back what a blur takes away (an unsharp mask) |
| [`clarity`](#clarity) | adds punch to the middle tones (a big, gentle unsharp mask on the brightness) |
| [`bloom`](#bloom) | bright parts glow into the dark around them |
| [`glow`](#glow) | the whole picture glows softly, not only the bright parts |
| [`halation`](#halation) | a red-orange glow around bright parts, like film |
| [`softfocus`](#softfocus) | a dreamy soft picture that still has its details |
| [`median`](#median) | every pixel becomes the middle value of its neighbors: noise and small details vanish, edges stay (a painted look) |
| [`kuwahara`](#kuwahara) | a painted look: flat patches of color with sharp edges between them (a Kuwahara filter) |

#### blur

Blurs the picture (a smooth gaussian blur or a flat box blur) (2 passes).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 0 to 100 | `6` | how far the blur reaches (measured on a screen 1080 high) |
| `type` | one of gaussian, box | `gaussian` | gaussian is smooth, box is flat and a bit blocky |
| `x` | number 0 to 1 | `1` | how much of the blur goes sideways |
| `y` | number 0 to 1 | `1` | how much of the blur goes up and down |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### zoomblur

A blur that streaks away from a point, like speed.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number -1 to 1 | `0.15` | how long the streaks are (negative: the other way) |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the point they come from |
| `samples` | whole number 4 to 64 | `24` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### spinblur

A blur that turns around a point.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `angle` | number -90 to 90 | `8` | how many degrees it turns over |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the point it turns around |
| `samples` | whole number 4 to 64 | `24` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### directionalblur

A blur in one direction, like a camera that moved.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `distance` | number 0 to 200 | `24` | how long the streaks are (pixels, measured on a screen 1080 high) |
| `angle` | number -180 to 180 | `0` | the direction of the streaks |
| `samples` | whole number 4 to 64 | `24` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### tiltshift

Only a strip of the picture is sharp, the rest is blurred (makes everything look like a toy model).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `position` | number 0 to 1 | `0.5` | where the sharp strip is (0 bottom, 1 top) |
| `width` | number 0 to 1 | `0.12` | how wide the sharp strip is (a part of the screen height) |
| `falloff` | number 0.01 to 1 | `0.25` | how slowly it goes from sharp to blurred |
| `radius` | number 0 to 60 | `12` | how blurred the far parts are (pixels, measured on a screen 1080 high) |
| `angle` | number -90 to 90 | `0` | turns the strip |
| `saturation` | number 0 to 3 | `1.3` | makes the colors stronger, like a painted model |
| `samples` | whole number 8 to 64 | `32` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### sharpen

Makes small details crisper.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 5 | `1` | how much |
| `radius` | number 0.5 to 4 | `1` | how big the details are (pixels, measured on a screen 1080 high) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### unsharp

Makes the picture crisper by adding back what a blur takes away (an unsharp mask).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 1 to 60 | `6` | how big the details are (pixels, measured on a screen 1080 high) |
| `amount` | number 0 to 5 | `1` | how much |
| `threshold` | number 0 to 0.5 | `0` | leaves differences smaller than this alone (keeps noise down) |
| `luma_only` | yes or no | `no` | only the brightness is sharpened, the colors stay as they are |
| `samples` | whole number 8 to 64 | `24` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### clarity

Adds punch to the middle tones (a big, gentle unsharp mask on the brightness).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 1 to 60 | `30` | how big the details are (pixels, measured on a screen 1080 high) |
| `amount` | number 0 to 5 | `0.8` | how much |
| `threshold` | number 0 to 0.5 | `0` | leaves differences smaller than this alone (keeps noise down) |
| `luma_only` | yes or no | `yes` | only the brightness is sharpened, the colors stay as they are |
| `samples` | whole number 8 to 64 | `24` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### bloom

Bright parts glow into the dark around them (4 passes).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `threshold` | number 0 to 1 | `0.7` | how bright something has to be to glow |
| `knee` | number 0 to 1 | `0.3` | how soft the start of the glow is |
| `intensity` | number 0 to 5 | `1` | how strong the glow is |
| `radius` | number 1 to 150 | `16` | how far the glow reaches (pixels, measured on a screen 1080 high) |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the glow |
| `mode` | one of add, screen | `screen` | how the glow goes over the picture (screen cannot go past white) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### glow

The whole picture glows softly, not only the bright parts (4 passes).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `threshold` | number 0 to 1 | `0` | how bright something has to be to glow |
| `knee` | number 0 to 1 | `0.5` | how soft the start of the glow is |
| `intensity` | number 0 to 5 | `0.6` | how strong the glow is |
| `radius` | number 1 to 150 | `24` | how far the glow reaches (pixels, measured on a screen 1080 high) |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the glow |
| `mode` | one of add, screen | `screen` | how the glow goes over the picture (screen cannot go past white) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### halation

A red-orange glow around bright parts, like film (4 passes).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `threshold` | number 0 to 1 | `0.75` | how bright something has to be to glow |
| `knee` | number 0 to 1 | `0.2` | how soft the start of the glow is |
| `intensity` | number 0 to 5 | `1.2` | how strong the glow is |
| `radius` | number 1 to 150 | `26` | how far the glow reaches (pixels, measured on a screen 1080 high) |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#ff5926` | the color of the glow |
| `mode` | one of add, screen | `add` | how the glow goes over the picture (screen cannot go past white) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### softfocus

A dreamy soft picture that still has its details (2 passes).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 1 to 80 | `8` | how soft (pixels, measured on a screen 1080 high) |
| `strength` | number 0 to 1 | `0.6` | how much of the blurred picture is mixed in |
| `glow` | number 0 to 1 | `0.25` | how much the light parts glow |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### median

Every pixel becomes the middle value of its neighbors: noise and small details vanish, edges stay (a painted look).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 1 to 6 | `1` | how far the neighbors are (pixels, measured on a screen 1080 high) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### kuwahara

A painted look: flat patches of color with sharp edges between them (a Kuwahara filter).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | whole number 1 to 8 | `3` | the size of the patches (pixels, measured on a screen 1080 high) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

### edges: edges, outlines and drawn looks

| Effect | What it does |
| --- | --- |
| [`edge`](#edge) | finds the edges in the picture and draws them (the picture itself can stay or go) |
| [`outline`](#outline) | dark lines drawn over the picture where things end |
| [`toon`](#toon) | a cartoon look: flat steps of color and black outlines (cel shading) |
| [`emboss`](#emboss) | makes the picture look like it is stamped in metal or stone |
| [`sketch`](#sketch) | a pencil drawing on paper: lines where things end and light hatching in the dark |
| [`halftone`](#halftone) | dots of different size, like print in a newspaper or a comic (gray ink, 4 inks, or red green blue) |
| [`crosshatch`](#crosshatch) | a pen drawing: the darker, the more crossing lines |
| [`stipple`](#stipple) | a drawing made of dots: the darker the part, the bigger and closer the dots |
| [`neon`](#neon) | the edges of everything glow in the colors of the picture, on a dark picture |
| [`thermal`](#thermal) | false colors by brightness, like a heat camera |
| [`nightvision`](#nightvision) | night vision goggles: everything amplified and green, with noise and dark corners |
| [`xray`](#xray) | an x-ray picture: light and dark swap and everything is blue-white |
| [`infrared`](#infrared) | an infrared photo: leaves glow white (or red) and the sky goes dark |

#### edge

Finds the edges in the picture and draws them (the picture itself can stay or go).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `method` | one of sobel, prewitt, scharr, roberts, laplacian | `sobel` | how edges are found: sobel is the usual, prewitt is a bit rougher, scharr is exact on diagonals, roberts is thin, laplacian finds lines |
| `source` | one of luma, color | `luma` | luma finds edges of brightness only, color also finds edges between colors of the same brightness |
| `strength` | number 0 to 20 | `2` | how strong the edges are |
| `threshold` | number 0 to 1 | `0` | edges weaker than this are not drawn (0 draws all of them, even faint ones) |
| `softness` | number 0 to 1 | `0` | how soft the cut at the threshold is |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the edges |
| `background` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color where there is no edge |
| `keep` | number 0 to 1 | `0` | how much of the picture itself shows where there is no edge (1 draws the edges over the picture) |
| `width` | number 0.5 to 8 | `1` | how wide the edges are (pixels, measured on a screen 1080 high, never thinner than one pixel) |
| `skip_bright` | number 0 to 1 | `1` | parts brighter than this are left as they are (1 skips nothing) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### outline

Dark lines drawn over the picture where things end.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `method` | one of sobel, prewitt, scharr, roberts, laplacian | `sobel` | how edges are found: sobel is the usual, prewitt is a bit rougher, scharr is exact on diagonals, roberts is thin, laplacian finds lines |
| `source` | one of luma, color | `luma` | luma finds edges of brightness only, color also finds edges between colors of the same brightness |
| `strength` | number 0 to 20 | `3` | how strong the edges are |
| `threshold` | number 0 to 1 | `0.3` | edges weaker than this are not drawn (0 draws all of them, even faint ones) |
| `softness` | number 0 to 1 | `0.3` | how soft the cut at the threshold is |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the edges |
| `background` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color where there is no edge |
| `keep` | number 0 to 1 | `1` | how much of the picture itself shows where there is no edge (1 draws the edges over the picture) |
| `width` | number 0.5 to 8 | `1.5` | how wide the edges are (pixels, measured on a screen 1080 high, never thinner than one pixel) |
| `skip_bright` | number 0 to 1 | `1` | parts brighter than this are left as they are (1 skips nothing) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### toon

A cartoon look: flat steps of color and black outlines (cel shading).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `levels` | whole number 2 to 12 | `4` | how many steps of brightness |
| `softness` | number 0 to 1 | `0.1` | how soft the steps are |
| `saturation` | number 0 to 3 | `1.2` | makes the colors stronger |
| `edge` | number 0 to 20 | `3` | how strong the outlines are |
| `width` | number 0.5 to 8 | `1.5` | how wide the outlines are (pixels, measured on a screen 1080 high) |
| `edge_color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the outlines |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### emboss

Makes the picture look like it is stamped in metal or stone.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number 0 to 10 | `2` | how deep |
| `angle` | number -180 to 180 | `135` | the direction the light comes from |
| `depth` | number 0.5 to 6 | `1` | how thick the relief is (pixels, measured on a screen 1080 high) |
| `mode` | one of grey, color | `grey` | grey is only the relief, color puts the relief on the picture |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### sketch

A pencil drawing on paper: lines where things end and light hatching in the dark.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `lines` | number 0 to 10 | `3` | how strong the lines are |
| `hatch` | number 0 to 1 | `0.6` | how much shading (hatching) there is in the dark parts |
| `width` | number 0.5 to 6 | `1` | how wide the lines are (pixels, measured on a screen 1080 high) |
| `paper` | color (#rrggbb, r,g,b or a name like orange) | `#f5f0e0` | the color of the paper |
| `ink` | color (#rrggbb, r,g,b or a name like orange) | `#1f1f2e` | the color of the pencil |
| `color` | number 0 to 1 | `0` | how much of the colors of the picture shows through (0 is a pure drawing) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### halftone

Dots of different size, like print in a newspaper or a comic (gray ink, 4 inks, or red green blue).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `type` | one of gray, cmyk, rgb | `cmyk` | gray is one ink, cmyk is the 4 inks of a printer (cyan, magenta, yellow, black), rgb is light dots on black |
| `size` | number 3 to 40 | `9` | the distance between dots (pixels, measured on a screen 1080 high) |
| `angle` | number -90 to 90 | `0` | turns all the dot grids |
| `softness` | number 0 to 1 | `0.2` | how soft the dots are |
| `paper` | color (#rrggbb, r,g,b or a name like orange) | `#faf7ed` | the color of the paper (gray and cmyk) |
| `ink` | color (#rrggbb, r,g,b or a name like orange) | `#0d0d1a` | the color of the ink (gray) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### crosshatch

A pen drawing: the darker, the more crossing lines.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `spacing` | number 3 to 40 | `9` | the distance between lines (pixels, measured on a screen 1080 high) |
| `thickness` | number 0.05 to 0.9 | `0.3` | how thick the lines are (a part of the spacing) |
| `layers` | whole number 1 to 4 | `4` | how many directions of lines (every one starts in a darker place) |
| `lightness` | number 0 to 1 | `0.85` | the brightness where the first lines start (higher draws lines almost everywhere) |
| `angle` | number -90 to 90 | `0` | turns all the lines |
| `paper` | color (#rrggbb, r,g,b or a name like orange) | `#f5f0e0` | the color of the paper |
| `ink` | color (#rrggbb, r,g,b or a name like orange) | `#1a1a26` | the color of the ink |
| `color` | number 0 to 1 | `0` | how much of the colors of the picture shows through |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### stipple

A drawing made of dots: the darker the part, the bigger and closer the dots.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `size` | number 3 to 40 | `8` | the distance between dots (pixels, measured on a screen 1080 high) |
| `dot` | number 0.2 to 1.5 | `0.9` | how big the biggest dots are |
| `jitter` | number 0 to 1 | `0.8` | how much the dots are moved off a grid (0 is a grid, 1 is random) |
| `paper` | color (#rrggbb, r,g,b or a name like orange) | `#f5f0e0` | the color of the paper |
| `ink` | color (#rrggbb, r,g,b or a name like orange) | `#1a1a26` | the color of the dots |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### neon

The edges of everything glow in the colors of the picture, on a dark picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `gain` | number 0 to 10 | `3` | how bright the glowing lines are |
| `width` | number 0.5 to 8 | `1.5` | how wide the lines are (pixels, measured on a screen 1080 high) |
| `glow` | number 0 to 2 | `0.8` | how strong the soft glow around the lines is |
| `dim` | number 0 to 1 | `0.1` | how much of the picture itself stays |
| `saturation` | number 0 to 3 | `1.8` | how vivid the colors of the lines are |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### thermal

False colors by brightness, like a heat camera.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `palette` | one of iron, rainbow, viridis, magma | `iron` | the colors |
| `contrast` | number 0.2 to 4 | `1.2` | how much the brightness is spread out |
| `offset` | number -1 to 1 | `0` | moves everything towards hot (positive) or cold (negative) |
| `invert` | yes or no | `no` | hot is dark and cold is light |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### nightvision

Night vision goggles: everything amplified and green, with noise and dark corners.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `gain` | number 0.2 to 10 | `3` | how much the light is amplified |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#40ff59` | the color of the screen |
| `noise` | number 0 to 1 | `0.25` | how much noise |
| `vignette` | number 0 to 1 | `0.8` | how dark the corners are (goggles) |
| `radius` | number 0.2 to 1.2 | `0.55` | how far from the middle it starts getting dark (a part of the screen height) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### xray

An x-ray picture: light and dark swap and everything is blue-white.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `contrast` | number 0.2 to 4 | `1.5` | how much the brightness is spread out |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#8cd9ff` | the color of the film |
| `edges` | number 0 to 5 | `1.5` | how strong the bright outlines are |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### infrared

An infrared photo: leaves glow white (or red) and the sky goes dark.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `foliage` | number 0 to 1 | `1` | how much plants glow |
| `look` | one of mono, color | `mono` | mono is a black and white photo, color is false color film (plants turn red) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

### distort: bending, waving and moving the picture

| Effect | What it does |
| --- | --- |
| [`wave`](#wave) | the picture ripples like a flag or like heat over a road |
| [`ripple`](#ripple) | rings spread out from a point, like a stone in water |
| [`swirl`](#swirl) | twists the picture around a point |
| [`bulge`](#bulge) | pushes the picture out (a bulge) or pulls it in (a pinch) around a point |
| [`fisheye`](#fisheye) | the whole picture is bent like it is seen through a fisheye lens |
| [`lens`](#lens) | a round magnifying glass that you can put anywhere on the screen |
| [`transform`](#transform) | zooms, turns, moves and flips the whole picture |
| [`mirror`](#mirror) | one side of the picture is copied to the other, like a mirror |
| [`kaleidoscope`](#kaleidoscope) | the picture is cut into slices that are mirrored around a point, like a kaleidoscope |
| [`tile`](#tile) | the whole picture is repeated in rows and columns (and can slide) |
| [`polar`](#polar) | turns the picture into a ring (a tiny planet), or a ring into a flat picture |
| [`shear`](#shear) | slants the picture sideways or up and down |
| [`stretch`](#stretch) | stretches the middle of the picture and squeezes the edges (or the other way round), each direction on its own |
| [`shake`](#shake) | the camera shakes |
| [`sway`](#sway) | the picture slowly rocks and drifts, like a boat |
| [`heat`](#heat) | a shimmering haze, like the air over a fire or a hot road |
| [`noisewarp`](#noisewarp) | the picture flows and bends like it is under oil or water |
| [`slice`](#slice) | strips of the picture slide sideways (or up and down) by different amounts |
| [`jitter`](#jitter) | every little square of the picture is moved a bit at random, like frosted glass |
| [`zoompulse`](#zoompulse) | the picture zooms in and out in time, like a beat |
| [`underwater`](#underwater) | as if you look through water: wobbling, blue-green, with light patterns and dark depths |

#### wave

The picture ripples like a flag or like heat over a road.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 200 | `12` | how far the picture moves (pixels, measured on a screen 1080 high) |
| `frequency` | number 0.1 to 60 | `6` | how many waves fit in the screen height |
| `direction` | one of horizontal, vertical, both | `horizontal` | horizontal moves the picture sideways (waves go up the screen), vertical moves it up and down |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### ripple

Rings spread out from a point, like a stone in water.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 100 | `10` | how far the picture moves (pixels, measured on a screen 1080 high) |
| `wavelength` | number 0.01 to 1 | `0.08` | the distance from one ring to the next (a part of the screen height) |
| `decay` | number 0 to 10 | `2` | how fast the rings fade with the distance |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | where the rings start |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### swirl

Twists the picture around a point.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `angle` | number -720 to 720 | `180` | how many degrees the middle is turned |
| `radius` | number 0.05 to 2 | `0.5` | how far the twist reaches (a part of the screen height) |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle of the twist |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### bulge

Pushes the picture out (a bulge) or pulls it in (a pinch) around a point.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number -1 to 1 | `0.5` | positive bulges, negative pinches |
| `radius` | number 0.05 to 2 | `0.5` | how far it reaches (a part of the screen height) |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### fisheye

The whole picture is bent like it is seen through a fisheye lens.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `strength` | number -1 to 2 | `0.8` | positive is a fisheye, negative is the other way (pincushion) |
| `zoom` | number 0.5 to 3 | `1` | zooms in (hides the edges) |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle of the lens |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### lens

A round magnifying glass that you can put anywhere on the screen.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `radius` | number 0.02 to 1 | `0.2` | the size of the lens (a part of the screen height) |
| `magnification` | number 0.2 to 8 | `2` | how much it magnifies (below 1 it shrinks) |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | where the lens is |
| `rim` | number 0 to 40 | `3` | the width of the ring around the lens (pixels, measured on a screen 1080 high) |
| `rim_color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the ring |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### transform

Zooms, turns, moves and flips the whole picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `zoom` | number 0.1 to 10 | `1.5` | above 1 zooms in, below 1 zooms out |
| `rotate` | number -360 to 360 | `0` | degrees to turn the picture |
| `x` | number -1 to 1 | `0` | moves the picture sideways (a part of the screen width) |
| `y` | number -1 to 1 | `0` | moves the picture up (a part of the screen height) |
| `flip_x` | yes or no | `no` | mirrors the picture left to right |
| `flip_y` | yes or no | `no` | mirrors the picture top to bottom |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### mirror

One side of the picture is copied to the other, like a mirror.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `side` | one of left, right, top, bottom, quad | `left` | the side that is kept (quad keeps the bottom left and copies it to all 4 corners) |
| `position` | number 0 to 1 | `0.5` | where the mirror is |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### kaleidoscope

The picture is cut into slices that are mirrored around a point, like a kaleidoscope.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `segments` | whole number 2 to 32 | `6` | how many slices |
| `angle` | number -180 to 180 | `0` | turns the picture |
| `spin` | number -360 to 360 | `0` | degrees a second the picture keeps turning |
| `zoom` | number 0.2 to 5 | `1` | zooms in |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### tile

The whole picture is repeated in rows and columns (and can slide).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `columns` | number 1 to 20 | `3` | how many copies across |
| `rows` | number 1 to 20 | `3` | how many copies down |
| `mirror` | yes or no | `no` | every other copy is mirrored |
| `scroll_x` | number -2 to 2 | `0` | how fast the copies slide sideways (screens a second) |
| `scroll_y` | number -2 to 2 | `0` | how fast the copies slide up (screens a second) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### polar

Turns the picture into a ring (a tiny planet), or a ring into a flat picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `mode` | one of planet, unwrap | `planet` | planet wraps the picture around a point, unwrap does the opposite |
| `zoom` | number 0.2 to 5 | `1` | zooms in |
| `rotate` | number -180 to 180 | `0` | turns it |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle |
| `edge` | one of clamp, mirror, repeat, black | `repeat` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### shear

Slants the picture sideways or up and down.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `shear_x` | number -2 to 2 | `0.3` | slants the picture sideways (the top moves right when positive) |
| `shear_y` | number -2 to 2 | `0` | slants the picture up and down (the right side moves up when positive) |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### stretch

Stretches the middle of the picture and squeezes the edges (or the other way round), each direction on its own.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `x` | number 0.3 to 3 | `1` | below 1 stretches the middle sideways, above 1 squeezes it |
| `y` | number 0.3 to 3 | `1.8` | below 1 stretches the middle up and down, above 1 squeezes it |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### shake

The camera shakes.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 100 | `10` | how far the picture moves (pixels, measured on a screen 1080 high) |
| `rotation` | number 0 to 10 | `0.5` | how many degrees it turns |
| `rate` | number 0 to 120 | `24` | how many shakes a second |
| `smooth` | yes or no | `yes` | moves smoothly from one shake to the next (off: it jumps) |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### sway

The picture slowly rocks and drifts, like a boat.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `angle` | number 0 to 30 | `2` | how many degrees it rocks |
| `distance` | number 0 to 300 | `20` | how far it drifts (pixels, measured on a screen 1080 high) |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### heat

A shimmering haze, like the air over a fire or a hot road.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 60 | `6` | how far the picture moves (pixels, measured on a screen 1080 high) |
| `scale` | number 1 to 60 | `12` | how many shimmers fit in the screen height |
| `rise` | number 0 to 5 | `1` | how fast the haze rises |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### noisewarp

The picture flows and bends like it is under oil or water.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 200 | `20` | how far the picture moves (pixels, measured on a screen 1080 high) |
| `scale` | number 0.5 to 40 | `4` | how many bends fit in the screen height |
| `octaves` | whole number 1 to 6 | `3` | how much fine detail the bends have |
| `flow` | number 0 to 5 | `0.3` | how fast it flows |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### slice

Strips of the picture slide sideways (or up and down) by different amounts.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `direction` | one of horizontal, vertical | `horizontal` | which way the strips slide |
| `count` | whole number 2 to 200 | `24` | how many strips |
| `amount` | number 0 to 300 | `40` | how far a strip can slide (pixels, measured on a screen 1080 high) |
| `chance` | number 0 to 1 | `0.5` | how many of the strips slide |
| `rate` | number 0 to 60 | `8` | how many times a second they change |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### jitter

Every little square of the picture is moved a bit at random, like frosted glass.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 30 | `3` | how far a square moves (pixels, measured on a screen 1080 high) |
| `size` | number 1 to 32 | `1` | the size of the squares (pixels, measured on a screen 1080 high) |
| `rate` | number 0 to 120 | `0` | how many times a second they move again (0 keeps them still) |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### zoompulse

The picture zooms in and out in time, like a beat.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.06` | how much it zooms |
| `rate` | number 0 to 30 | `1.5` | how many pulses a second |
| `shape` | one of sine, beat, saw | `beat` | sine is smooth, beat is a sharp thump that fades, saw grows and snaps back |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the point it zooms into |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### underwater

As if you look through water: wobbling, blue-green, with light patterns and dark depths.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `wobble` | number 0 to 60 | `8` | how much the picture wobbles (pixels, measured on a screen 1080 high) |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#4cb2ff` | the color of the water |
| `strength` | number 0 to 1 | `0.5` | how much the water colors the picture |
| `caustics` | number 0 to 1 | `0.3` | how bright the moving light patterns are |
| `depth` | number 0 to 1 | `0.4` | how dark it gets towards the bottom |
| `edge` | one of clamp, mirror, repeat, black | `mirror` | what to show where the picture is moved away from the edge of the screen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

### overlay: things drawn over the picture: vignette, grain, crosshair, weather

| Effect | What it does |
| --- | --- |
| [`vignette`](#vignette) | the corners of the picture get dark |
| [`grain`](#grain) | film grain |
| [`static`](#static) | the snow of a tv without a signal |
| [`letterbox`](#letterbox) | black bars above and below (or left and right) so the picture has the shape of a film |
| [`border`](#border) | a frame around the picture |
| [`crosshair`](#crosshair) | a crosshair (or a dot, a ring, a square) on the screen |
| [`blend`](#blend) | covers the whole picture with a color, with any blend mode |
| [`gradient`](#gradient) | a gradient of two colors over the picture, with any blend mode (a sunset sky, a color tilt) |
| [`fadeto`](#fadeto) | fades the picture to a color: all of it, or only the top, the bottom, a side, the edges or the middle |
| [`pulse`](#pulse) | the brightness of the picture goes up and down in time |
| [`flash`](#flash) | a flash of color that fades away, again and again (like lightning or a camera) |
| [`strobe`](#strobe) | flashes the picture on and off at any rate (fast flashing can bother people who are sensitive to it) |
| [`godrays`](#godrays) | beams of light that stream from a bright point through the picture |
| [`lensflare`](#lensflare) | bright parts make rings and ghost images across the picture, like a camera lens |
| [`lightleak`](#lightleak) | warm colored light that leaks in from the edges, like an old camera |
| [`rain`](#rain) | rain falling over the picture |
| [`snow`](#snow) | snow falling over the picture |
| [`dust`](#dust) | tiny glowing specks of dust drifting slowly in the air |
| [`stars`](#stars) | twinkling stars (they only show in the dark parts of the picture) |

#### vignette

The corners of the picture get dark.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.6` | how dark the corners get |
| `radius` | number 0 to 1.5 | `0.5` | how far from the middle it starts getting dark (1 is the corner) |
| `softness` | number 0.01 to 1.5 | `0.6` | how slowly it gets dark |
| `roundness` | number 0 to 1 | `0.5` | 1 is a round vignette, 0 follows the shape of the screen |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the corners |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | the middle |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### grain

Film grain.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.15` | how strong |
| `size` | number 1 to 8 | `1.5` | the size of the grains (pixels, measured on a screen 1080 high) |
| `rate` | number 0 to 120 | `24` | how many times a second the grain changes (0 keeps it still) |
| `midtones` | yes or no | `yes` | more grain in the middle tones, less in the very dark and light |
| `colored` | yes or no | `no` | every color on its own, like color film |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### static

The snow of a tv without a signal.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `amount` | number 0 to 1 | `0.35` | how much of the picture is replaced by static |
| `size` | number 1 to 16 | `2` | the size of the specks (pixels, measured on a screen 1080 high) |
| `rate` | number 0 to 240 | `60` | how many times a second the static changes |
| `colored` | yes or no | `no` | colored static |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### letterbox

Black bars above and below (or left and right) so the picture has the shape of a film.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `ratio` | number 0.5 to 6 | `2.35` | the shape of the picture: width divided by height (2.35 is a wide film, 1.33 is an old tv) |
| `softness` | number 0 to 60 | `0` | how soft the edge of the bars is (pixels, measured on a screen 1080 high) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color of the bars |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### border

A frame around the picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `width` | number 0 to 400 | `20` | the width of the frame (pixels, measured on a screen 1080 high) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the frame |
| `style` | one of solid, double, fade | `solid` | solid is a plain frame, double is two thin lines, fade is a soft glow from the edge |
| `opacity` | number 0 to 1 | `1` | how much of the frame is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### crosshair

A crosshair (or a dot, a ring, a square) on the screen.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `style` | one of plus, x, dot, circle, square | `plus` | the shape |
| `size` | number 1 to 200 | `12` | the length of the arms, or the size of the ring (pixels, measured on a screen 1080 high) |
| `thickness` | number 0.5 to 20 | `2` | how thick the lines are |
| `gap` | number 0 to 50 | `4` | the gap in the middle (plus and x) |
| `outline` | number 0 to 6 | `1` | the width of the dark outline that keeps it visible on any picture |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color |
| `opacity` | number 0 to 1 | `1` | how much of it is seen |
| `invert` | yes or no | `no` | instead of a color it shows the opposite of the picture below it |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | where it is |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### blend

Covers the whole picture with a color, with any blend mode.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ff8033` | the color |
| `blend` | one of normal, multiply, screen, overlay, softlight, hardlight, add, subtract, difference, dodge, burn | `softlight` | how it goes over the picture |
| `opacity` | number 0 to 1 | `0.5` | how much of it is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### gradient

A gradient of two colors over the picture, with any blend mode (a sunset sky, a color tilt).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `type` | one of linear, radial | `linear` | a straight gradient or one that grows from a point |
| `start` | color (#rrggbb, r,g,b or a name like orange) | `#1a2680` | the first color |
| `end` | color (#rrggbb, r,g,b or a name like orange) | `#ff9940` | the second color |
| `angle` | number -180 to 180 | `90` | the direction from start to end, in degrees (linear): 90 is upwards |
| `center` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.5` | where it starts (radial) |
| `size` | number 0.1 to 4 | `1` | how far it takes to go from the first to the second color |
| `blend` | one of normal, multiply, screen, overlay, softlight, hardlight, add, subtract, difference, dodge, burn | `softlight` | how it goes over the picture |
| `opacity` | number 0 to 1 | `0.6` | how much of it is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### fadeto

Fades the picture to a color: all of it, or only the top, the bottom, a side, the edges or the middle.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#000000` | the color it fades to |
| `amount` | number 0 to 1 | `0.5` | how far it fades (1 is fully the color) |
| `where` | one of all, top, bottom, left, right, edges, center | `all` | which part fades |
| `size` | number 0.05 to 1.5 | `0.4` | how far the fade reaches into the picture (a part of the screen) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### pulse

The brightness of the picture goes up and down in time.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `rate` | number 0 to 30 | `1` | how many pulses a second |
| `depth` | number 0 to 1 | `0.3` | how dark it gets at the lowest |
| `shape` | one of sine, triangle, square | `sine` | the shape of the pulse |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### flash

A flash of color that fades away, again and again (like lightning or a camera).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `rate` | number 0 to 10 | `0.5` | how many flashes a second |
| `decay` | number 0.5 to 30 | `6` | how fast the flash fades (higher is shorter) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the flash |
| `strength` | number 0 to 1 | `0.8` | how strong the flash is |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### strobe

Flashes the picture on and off at any rate (fast flashing can bother people who are sensitive to it).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `rate` | number 0 to 1000 | `10` | how many flashes a second |
| `duty` | number 0 to 1 | `0.5` | how much of every flash the effect is on |
| `mode` | one of black, white, invert, color | `black` | what the flash shows |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ff0000` | the color of the flash (color mode) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### godrays

Beams of light that stream from a bright point through the picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `light` | point (x,y from 0 to 1, 0,0 is the bottom left) | `0.5,0.8` | where the light is |
| `threshold` | number 0 to 1 | `0.9` | how bright something has to be to make beams |
| `density` | number 0.1 to 1.5 | `0.9` | how far the beams reach |
| `decay` | number 0.8 to 1 | `0.96` | how fast the beams fade away from the light (1 is never) |
| `intensity` | number 0 to 4 | `0.6` | how strong the beams are |
| `tint` | color (#rrggbb, r,g,b or a name like orange) | `#fff2cc` | the color of the beams |
| `samples` | whole number 16 to 96 | `48` | how smooth (more is slower) |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### lensflare

Bright parts make rings and ghost images across the picture, like a camera lens.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `ghosts` | whole number 1 to 8 | `4` | how many ghost images |
| `dispersal` | number 0 to 1 | `0.3` | how far apart the ghosts are |
| `halo` | number 0 to 1 | `0.45` | how big the ring of light is |
| `distortion` | number 0 to 0.1 | `0.02` | how much the colors split |
| `threshold` | number 0 to 1 | `0.8` | how bright something has to be to make a flare |
| `intensity` | number 0 to 4 | `0.6` | how strong the flare is |
| `inner` | color (#rrggbb, r,g,b or a name like orange) | `#ffd999` | the color of the flare near the middle |
| `outer` | color (#rrggbb, r,g,b or a name like orange) | `#8099ff` | the color of the flare near the edges |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |

#### lightleak

Warm colored light that leaks in from the edges, like an old camera.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `color1` | color (#rrggbb, r,g,b or a name like orange) | `#ff731a` | the first color of the light |
| `color2` | color (#rrggbb, r,g,b or a name like orange) | `#ff1a66` | the second color of the light |
| `amount` | number 0 to 1 | `0.5` | how strong the light is |
| `scale` | number 0.3 to 5 | `1.2` | how big the patches are |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |

#### rain

Rain falling over the picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `density` | number 0 to 1 | `0.5` | how much rain |
| `fall` | number 0.1 to 5 | `1.5` | how fast the rain falls (screens a second) |
| `length` | number 20 to 400 | `90` | how long the streaks are (pixels, measured on a screen 1080 high) |
| `angle` | number -45 to 45 | `8` | how much the rain slants (wind) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#b2c7e6` | the color of the rain |
| `opacity` | number 0 to 1 | `0.6` | how much of the rain is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### snow

Snow falling over the picture.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `density` | number 0 to 1 | `0.35` | how much snow |
| `size` | number 1 to 30 | `6` | the size of the biggest flakes (pixels, measured on a screen 1080 high) |
| `fall` | number -2 to 2 | `0.15` | how fast the snow falls (screens a second, negative rises) |
| `wind` | number -2 to 2 | `0.05` | how fast the snow drifts sideways (screens a second) |
| `layers` | whole number 1 to 6 | `4` | how many depths of snow (the far ones are smaller and slower) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the flakes |
| `opacity` | number 0 to 1 | `0.9` | how much of the snow is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### dust

Tiny glowing specks of dust drifting slowly in the air.

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `density` | number 0 to 1 | `0.6` | how much snow |
| `size` | number 1 to 30 | `3` | the size of the biggest flakes (pixels, measured on a screen 1080 high) |
| `fall` | number -2 to 2 | `0.03` | how fast the snow falls (screens a second, negative rises) |
| `wind` | number -2 to 2 | `0.01` | how fast the snow drifts sideways (screens a second) |
| `layers` | whole number 1 to 6 | `5` | how many depths of snow (the far ones are smaller and slower) |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffe6b2` | the color of the flakes |
| `opacity` | number 0 to 1 | `0.5` | how much of the snow is seen |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |

#### stars

Twinkling stars (they only show in the dark parts of the picture).

| Setting | Kind | Starts as | What |
| --- | --- | --- | --- |
| `density` | number 0 to 1 | `0.08` | how many stars |
| `size` | number 0.5 to 8 | `2.5` | the size of the biggest stars (pixels, measured on a screen 1080 high) |
| `twinkle` | number 0 to 1 | `0.5` | how much the stars twinkle |
| `motion` | number -1 to 1 | `0` | how fast the sky drifts sideways (screens a second) |
| `sky` | number 0 to 1 | `0.8` | how much the stars hide behind bright parts of the picture |
| `color` | color (#rrggbb, r,g,b or a name like orange) | `#ffffff` | the color of the stars |
| `brightness` | number 0 to 3 | `1` | how bright the stars are |
| `mix` | number 0 to 1 | `1` | how much of the effect is used: 0 is none, 1 is all of it (every effect has it) |
| `speed` | number -20 to 20 | `1` | how fast it moves (0 stops it, negative runs it backwards) |
| `seed` | whole number 0 to 9999 | `0` | a different number gives a different random pattern |


## A shader file

The `.json` files in `shaders/custom` (made by `.shader save`, you can also write one by hand; the name of the file is the name of the shader) look like this, with one effect on every line, in the order they are applied:

```json
{
  "name": "cozy",
  "description": "warm and dark at the edges",
  "speed": 1.0,
  "effects": [
    {"effect": "temperature", "params": {"warmth": 0.4}},
    {"effect": "vignette", "params": {"amount": 0.7, "color": [0.1, 0.05, 0.0]}},
    {"effect": "grain", "params": {"amount": 0.05}, "enabled": false}
  ]
}
```

Only settings that differ from what they start as have to be written. A file with a wrong effect or setting still loads: what is wrong is left out and the console says what it was. The built-in shaders are the same kind of file, in `shaders/defaults.json` (`SHADER_DEFAULTS`).

## Notes

- Effects that draw something that moves are animated with the time of the game; `strobe` and `flash` can go at any rate you ask for, and fast flashing can bother people who are sensitive to it.
- An effect is compiled the first time it is used (a few milliseconds; `bloom` and the other effects of several passes take a little longer). Every effect is one or more full-screen passes, and `.fx cost` says how many the stack needs; the menu and the commands never limit how many effects there are, only your graphics card does.
- Not there yet: effects that need the depth of the scene (fog, depth of field, outlines of depth, ambient occlusion, a tint or a scan by depth) and effects that need the previous frame (trails, motion blur, ghosts, feedback), and shaders that belong to single blocks.
