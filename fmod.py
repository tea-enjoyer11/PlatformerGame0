import os  # noqa
os.environ["PYFMODEX_DLL_PATH"] = "/home/user/Downloads/fmodstudioapi20223linux/api/core/lib/x86_64/libfmod.so"  # noqa
import pyfmodex  # noqa


# https://github.com/tyrylu/pyfmodex
# https://github.com/tyrylu/pyfmodex/tree/master/docs


system = pyfmodex.System()
system.init()
sound = system.create_sound("assets/sounds/grunt.wav")
channel = sound.play()

while channel.is_playing:
    pass
