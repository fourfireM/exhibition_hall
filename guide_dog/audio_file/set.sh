#!/bin/bash

# 替换为你的设备名称或描述
SINK_NAME="alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo"
# 或者
# SINK_DESCRIPTION="USB Audio"

# 通过名称设置默认 sink (更可靠)
pactl set-default-sink "$SINK_NAME"

pactl set-sink-volume "$SINK_NAME" 200%

# 如果名称不起作用，尝试通过描述设置 (不太可靠，但可用)
#pactl list sinks | grep "$SINK_DESCRIPTION" | awk '{print $1}' | xargs -n1 pactl set-default-sink

exit 0
