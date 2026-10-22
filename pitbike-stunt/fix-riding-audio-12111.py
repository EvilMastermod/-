#!/usr/bin/env python3
"""MC 1.21.11 hotfix after original donor installation."""
from pathlib import Path
import json, math, wave, struct, subprocess, shutil
base=Path("project/src/main")
java=base/"java/dev/pitbike/stunt"
res=base/"resources"
p=java/"PitbikeStunt.java"
s=p.read_text(encoding="utf-8")
needle="    public static final Item[] BIKES ="
assert needle in s and "ENGINE_SOUND" not in s
s=s.replace(needle,'''    public static final net.minecraft.sound.SoundEvent ENGINE_SOUND =
            Registry.register(Registries.SOUND_EVENT, id("engine"),
                    net.minecraft.sound.SoundEvent.of(id("engine")));
'''+needle)
p.write_text(s,encoding="utf-8")

p=java/"entity/PitbikeEntity.java"
s=p.read_text(encoding="utf-8")
assert "velocityDirty = true;" in s
s=s.replace("        velocityDirty = true;\n","")
s=s.replace("return 1.05f;","return 0.70f;")
for before,after in (
    ("SoundEvents.BLOCK_ANVIL_LAND","SoundEvents.BLOCK_WOOD_HIT"),
    ("SoundEvents.BLOCK_ANVIL_USE","SoundEvents.BLOCK_WOOD_PLACE"),
    ("SoundEvents.BLOCK_PISTON_EXTEND","dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND"),
    ("SoundEvents.ENTITY_MINECART_RIDING","dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND"),
    ("playBikeSound(dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND, 0.16f,",
     "playBikeSound(dev.pitbike.stunt.PitbikeStunt.ENGINE_SOUND, 0.43f,")
):
    assert before in s,before
    s=s.replace(before,after)
# With +Z facing forward, a right turn decreases yaw and increases X.
assert "double turnDegrees = -physics.steer()" in s
p.write_text(s,encoding="utf-8")

p=java/"client/DonorMesh.java"
s=p.read_text(encoding="utf-8")
for before,after in (
    ('case "fork" -> steer = state.steer() * 0.82f;',
     'case "fork" -> steer = -state.steer() * 0.82f;'),
    ("compress = -state.fork() * 0.12f;", "compress = -state.fork() * 0.43f;"),
    ("rearLean = -state.shock() * 0.13f;", "rearLean = -state.shock() * 0.39f;"),
    ("rearLean = state.shock() * 0.06f;", "rearLean = state.shock() * 0.19f;")
):
    assert before in s,before
    s=s.replace(before,after)
p.write_text(s,encoding="utf-8")

p=java/"client/PitbikeRenderer.java"
s=p.read_text(encoding="utf-8")
assert "state.yaw=bike.getYaw();" in s
s=s.replace("state.yaw=bike.getYaw();","state.yaw=bike.getYaw(progress);")
p.write_text(s,encoding="utf-8")

pose = '''package dev.pitbike.stunt.mixin;
import dev.pitbike.stunt.entity.PitbikeEntity;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.render.entity.state.PlayerEntityRenderState;
import net.minecraft.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Poses rider hands on grips and legs on footrests, including remote riders. */
@Mixin(PlayerEntityModel.class)
public abstract class PlayerModelPoseMixin {
    @Inject(method="setAngles(Lnet/minecraft/client/render/entity/state/PlayerEntityRenderState;)V", at=@At("TAIL"))
    private void pitbikestunt$pose(PlayerEntityRenderState state, CallbackInfo ci) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client.world == null) return;
        Entity entity = client.world.getEntityById(state.id);
        if (entity == null || !(entity.getVehicle() instanceof PitbikeEntity bike)) return;
        PlayerEntityModel model = (PlayerEntityModel)(Object)this;
        float steer = bike.steer();
        float lean = Math.min(0.17f, Math.abs(bike.speed()) * 0.11f);
        ModelPart right = model.rightArm, left = model.leftArm;
        right.pitch = -1.23f - lean;
        left.pitch = -1.23f - lean;
        right.yaw = -0.38f - steer * 0.19f;
        left.yaw = 0.38f - steer * 0.19f;
        right.roll = -0.10f;
        left.roll = 0.10f;
        model.body.pitch = 0.20f + lean;
        model.rightLeg.pitch = -1.02f;
        model.leftLeg.pitch = -1.02f;
        model.rightLeg.roll = 0.12f;
        model.leftLeg.roll = -0.12f;
        if (bike.trick() == 2 || bike.trick() == 4) {
            right.pitch = -2.5f; left.pitch = -2.5f;
        } else if (bike.trick() == 3) {
            right.pitch = -2.4f;
        } else if (bike.trick() == 1) {
            model.leftLeg.pitch = 0.56f;
        } else if (bike.trick() == 5) {
            model.body.pitch = 0.91f;
            model.rightLeg.pitch = 0.65f;
            model.leftLeg.pitch = 0.65f;
        } else if (bike.trick() == 6) {
            model.rightLeg.pitch = -0.07f;
            model.leftLeg.pitch = -0.07f;
            model.body.pitch = 0.0f;
        }
        model.rightSleeve.setTransform(right.getTransform());
        model.leftSleeve.setTransform(left.getTransform());
        model.rightPants.setTransform(model.rightLeg.getTransform());
        model.leftPants.setTransform(model.leftLeg.getTransform());
        model.jacket.setTransform(model.body.getTransform());
    }
}
'''
p=java/"mixin/PlayerModelPoseMixin.java"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(pose,encoding="utf-8")
p=res/"pitbikestunt.mixins.json"
data=json.loads(p.read_text(encoding="utf-8"))
data["client"]=["PlayerModelPoseMixin"]
p.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

# Generate new engine sample: harmonic four-stroke burble; pitch reacts to RPM.
sounddir=res/"assets/pitbikestunt/sounds"
sounddir.mkdir(parents=True,exist_ok=True)
temp=Path("/tmp/pitbikestunt_engine.wav")
sr=24000
n=9600
samples=[]
for i in range(n):
    t=i/sr
    a=2*math.pi*50*t
    phase=(50*t)%1.
    exhaust=(1-phase)**9
    v=.42*math.sin(a)+.25*math.sin(2*a)+.18*math.sin(3*a)+.13*math.sin(5*a)+.08*math.sin(8*a)+.12*(exhaust-.09)
    fade=max(0,min(1,i/260.,(n-1-i)/260.))
    samples.append(max(-32767,min(32767,int(12900*v*fade))))
with wave.open(str(temp),"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
    w.writeframes(struct.pack("<%dh"%len(samples),*samples))
if shutil.which("ffmpeg") is None:
    raise RuntimeError("FFmpeg unavailable to encode Vorbis engine audio")
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(temp),
                "-c:a","libvorbis","-qscale:a","4",str(sounddir/"engine.ogg")],check=True)
res.joinpath("assets/pitbikestunt/sounds.json").write_text(
    json.dumps({"engine":{"sounds":[{"name":"pitbikestunt:engine","stream":False}]}},indent=2)+"\n",encoding="utf-8")
assert (sounddir/"engine.ogg").stat().st_size>1000
print("DONE: real engine OGG, silent anvil removed, smooth riding, visible suspension and rider pose")
