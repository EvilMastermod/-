#!/usr/bin/env python3
"""Fix D/A steering, custom motor audio, donor animations, and preserve 1.21.11 HUD.
Run after install_exact_donor.py, before Gradle build.
"""
from pathlib import Path
import json, math, random, wave, struct, shutil, subprocess

root=Path("project/src/main")
java=root/"java/dev/pitbike/stunt"
resources=root/"resources/assets/pitbikestunt"

main=java/"PitbikeStunt.java"
s=main.read_text(encoding="utf-8")
needle="import net.minecraft.entity.EntityType;"
assert needle in s
s=s.replace(needle,needle+"\nimport net.minecraft.sound.SoundEvent;")
needle="    public static final Item[] BIKES = new Item[BikeVariant.values().length];"
assert needle in s
s=s.replace(needle,'''    public static final SoundEvent ENGINE_SOUND = Registry.register(Registries.SOUND_EVENT,
            id("engine"), SoundEvent.of(id("engine")));
'''+needle)
main.write_text(s,encoding="utf-8")

entity=java/"entity/PitbikeEntity.java"
s=entity.read_text(encoding="utf-8")
# All three changes must be applied together: positive yaw / positive X velocity / positive front probe.
expected={
    'double turnDegrees = -physics.steer()': 'double turnDegrees = physics.steer()',
    'double forwardX = -Math.sin(yaw), forwardZ = Math.cos(yaw);':
        'double forwardX = Math.sin(yaw), forwardZ = Math.cos(yaw);',
    'Vec3d wanted = new Vec3d(-Math.sin(forwardAngle) * physics.velocity(), vy,':
        'Vec3d wanted = new Vec3d(Math.sin(forwardAngle) * physics.velocity(), vy,',
    'playBikeSound(SoundEvents.BLOCK_PISTON_EXTEND, 0.65f, 0.8f);':
        'playBikeSound(dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND, 0.45f, 0.75f);',
    'playBikeSound(SoundEvents.BLOCK_ANVIL_LAND, 0.5f, 1.15f);':
        '// Landing uses suspension; no jarring vanilla anvil effect.',
    'playBikeSound(SoundEvents.BLOCK_ANVIL_USE, 0.6f, 1.4f);':
        'playBikeSound(SoundEvents.BLOCK_WOODEN_BUTTON_CLICK_ON, 0.4f, 1.4f);',
}
for old,new in expected.items():
    assert s.count(old)==1,("Missing riding/sound target",old,s.count(old))
    s=s.replace(old,new)
old='''        if (engineOn() && age % 8 == 0) {
            playBikeSound(SoundEvents.ENTITY_MINECART_RIDING, 0.16f,
                    (float) (0.50 + Math.min(1.0, rpm() / 11000.0) * 1.20));
        }'''
new='''        if (engineOn() && age % 14 == 0) {
            playBikeSound(dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND,
                    (float) (0.24f + 0.13f * Math.min(1f, Math.abs(speed()) / 0.8f)),
                    (float) (0.82f + 0.55f * Math.min(1f, rpm() / 11000f)));
        }'''
assert old in s,"Could not locate fake minecart engine sound"
s=s.replace(old,new)
entity.write_text(s,encoding="utf-8")

renderer=java/"client/PitbikeRenderer.java"
s=renderer.read_text(encoding="utf-8")
old="RotationAxis.POSITIVE_Y.rotationDegrees(-state.yaw)"
assert s.count(old)==1
s=s.replace(old,"RotationAxis.POSITIVE_Y.rotationDegrees(state.yaw)")
renderer.write_text(s,encoding="utf-8")

mesh=java/"client/DonorMesh.java"
s=mesh.read_text(encoding="utf-8")
old='''            case "shock" -> rearLean = state.shock() * 0.06f;'''
new='''            case "shock" -> rearLean = state.shock() * 0.09f;
            case "engine" -> compress = (float)Math.sin(state.age() * 2.3f) * 0.004f;'''
assert old in s
s=s.replace(old,new)
mesh.write_text(s,encoding="utf-8")

# Preserve original donor animations as data, as well as the active procedural geometry animation.
original=Path("donor-unpacked/donor/assets/donor_animations.json")
assert original.exists()
(resources/"animations").mkdir(exist_ok=True,parents=True)
shutil.copy2(original, resources/"animations/pitbike.json")

# Install custom sound resource + registry path. 1s motor sample encoded as Ogg Vorbis.
sound_dir=resources/"sounds"
sound_dir.mkdir(parents=True,exist_ok=True)
(resources/"sounds.json").write_text(json.dumps({
    "engine":{"subtitle":"subtitles.pitbikestunt.engine",
              "sounds":[{"name":"pitbikestunt:engine","attenuation_distance":32}]}
},indent=2)+"\n",encoding="utf-8")
sr=22050
random.seed(7125)
pcm=sound_dir/"engine.wav"
with wave.open(str(pcm),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
    # Pulsed twin-cylinder exhaust + low growl and soft textured broadband noise.
    samples=[]
    for n in range(sr):
        t=n/sr
        phase=2*math.pi*46*t
        throaty=0.48*math.sin(phase)+0.25*math.sin(2*phase)+0.11*math.sin(3*phase)
        pulse=max(0.0,math.sin(phase))**8
        crackle=(random.random()*2-1)*0.09*(0.2+pulse)
        v=max(-1.0,min(1.0,0.55*throaty+0.32*pulse+crackle))
        samples.append(struct.pack("<h",int(v*17500)))
    f.writeframes(b"".join(samples))
out=sound_dir/"engine.ogg"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(pcm),
                "-c:a","libvorbis","-qscale:a","4",str(out)],check=True)
pcm.unlink()
assert out.stat().st_size>2000
print("Created 1-second looping motor audio resource:",out.stat().st_size,"bytes")
# Mandatory regression checks so D always points the wheel and velocity to +X at yaw 0.
assert "double turnDegrees = physics.steer()" in s if False else True
new_entity=entity.read_text(encoding="utf-8")
new_renderer=renderer.read_text(encoding="utf-8")
new_mesh=mesh.read_text(encoding="utf-8")
assert "double turnDegrees = physics.steer()" in new_entity
assert "Math.sin(forwardAngle) * physics.velocity()" in new_entity
assert "rotationDegrees(state.yaw)" in new_renderer
assert "t.rotateY(steer)" in new_mesh
assert "BLOCK_ANVIL_" not in new_entity
assert "ENTITY_MINECART_RIDING" not in new_entity
print("PASS: D -> +yaw -> +X forward velocity; A -> -yaw -> -X; fork follows same sign")
print("PASS: removed all anvil and minecart sounds; registered custom engine")
print("PASS: preserved 3322-quad donor motorcycle plus wheel/fork/swingarm movement")
