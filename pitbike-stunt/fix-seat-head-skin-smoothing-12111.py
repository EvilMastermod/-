#!/usr/bin/env python3
"""MC 1.21.11: raise rider to donor seat, lock torso to bike, free head and smooth riding.
Runs after wheelie/physics patch, so it only edits the finished 1.21.11 source.
"""
from pathlib import Path
import json, re

root=Path("project/src/main/java/dev/pitbike/stunt")
resources=Path("project/src/main/resources")

def replace_one(src, needle, replacement):
    count=src.count(needle)
    assert count==1,(needle,count)
    return src.replace(needle,replacement)

entity_file=root/"entity/PitbikeEntity.java"
s=entity_file.read_text(encoding="utf-8")
s=replace_one(s,"new Vec3d(0, 0.52, -0.35)", "new Vec3d(0, 1.09, -0.35)")
# Network updates arrive on the client less regularly than renders. Move to a
# short extrapolated target; suppress micro-snaps while still catching up after lag.
begin=s.index("    private int smoothTicks;")
end=s.index("    @Override protected void initDataTracker",begin)
network_smoothing="""    private boolean receivedRemoteTarget;
    private int ticksSinceRemoteUpdate;
    private double remoteTargetX, remoteTargetY, remoteTargetZ;
    private double remoteSpeedX, remoteSpeedY, remoteSpeedZ;
    private float remoteYaw, remotePitch;

    @Override protected void lerpPosAndRotation(int steps, double x, double y,
                                                 double z, double yaw, double pitch) {
        if (!getEntityWorld().isClient()) {
            super.lerpPosAndRotation(steps, x, y, z, yaw, pitch);
            return;
        }
        if (!receivedRemoteTarget) {
            receivedRemoteTarget = true;
            remoteTargetX=x; remoteTargetY=y; remoteTargetZ=z;
            remoteYaw=(float)yaw; remotePitch=(float)pitch;
            ticksSinceRemoteUpdate=0;
            return;
        }
        int elapsed=Math.max(1,Math.min(5,ticksSinceRemoteUpdate));
        remoteSpeedX=MathHelper.clamp((x-remoteTargetX)/elapsed,-1.35,1.35);
        remoteSpeedY=MathHelper.clamp((y-remoteTargetY)/elapsed,-0.9,0.9);
        remoteSpeedZ=MathHelper.clamp((z-remoteTargetZ)/elapsed,-1.35,1.35);
        remoteTargetX=x; remoteTargetY=y; remoteTargetZ=z;
        remoteYaw=(float)yaw; remotePitch=(float)pitch;
        ticksSinceRemoteUpdate=0;
    }

    private void smoothRemoteMovement() {
        if (!receivedRemoteTarget) return;
        ticksSinceRemoteUpdate++;
        // A small bounded look-ahead keeps the tire from stopping between packets.
        double ahead=Math.min(1.25,Math.max(0,ticksSinceRemoteUpdate-0.35));
        double wantedX=remoteTargetX+remoteSpeedX*ahead;
        double wantedY=remoteTargetY+remoteSpeedY*ahead;
        double wantedZ=remoteTargetZ+remoteSpeedZ*ahead;
        double dx=wantedX-getX(),dy=wantedY-getY(),dz=wantedZ-getZ();
        double sq=dx*dx+dy*dy+dz*dz;
        if(sq>144) {
            // Teleports and dimension transfers must not glide through terrain.
            setPosition(remoteTargetX,remoteTargetY,remoteTargetZ);
            setYaw(remoteYaw); setPitch(remotePitch);
            remoteSpeedX=remoteSpeedY=remoteSpeedZ=0;
            return;
        }
        double alpha=sq>2.25 ? .79 : .57;
        setPosition(getX()+dx*alpha,getY()+dy*alpha,getZ()+dz*alpha);
        setYaw(getYaw()+MathHelper.wrapDegrees(remoteYaw-getYaw())*.62f);
        setPitch(getPitch()+MathHelper.wrapDegrees(remotePitch-getPitch())*.62f);
    }

"""
s=s[:begin]+network_smoothing+s[end:]
assert "if (getEntityWorld().isClient()) { smoothRemoteMovement(); return; }" in s
entity_file.write_text(s,encoding="utf-8")
print("Raised passenger feet onto donor seat and added bounded remote-motion smoothing")

# Render state fix: orient body with bike while the head follows the player's camera.
render_mixin="""package dev.pitbike.stunt.mixin;

import dev.pitbike.stunt.entity.PitbikeEntity;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.render.entity.state.PlayerEntityRenderState;
import net.minecraft.entity.PlayerLikeEntity;
import net.minecraft.util.math.MathHelper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntityRenderer.class)
public abstract class PlayerRidingStateMixin {
    @Inject(
        method = "updateRenderState(Lnet/minecraft/entity/PlayerLikeEntity;Lnet/minecraft/client/render/entity/state/PlayerEntityRenderState;F)V",
        at = @At("TAIL"))
    private void pitbikestunt$lockBodyToBike(PlayerLikeEntity player,
                                             PlayerEntityRenderState state,
                                             float tickProgress, CallbackInfo ci) {
        if (!(player.getVehicle() instanceof PitbikeEntity bike)) return;
        // Fixed torso facing the bike, independent of the camera's yaw.
        state.bodyYaw = bike.getYaw(tickProgress);
        // Only the head reacts to camera look direction.
        state.relativeHeadYaw = MathHelper.clamp(
            MathHelper.wrapDegrees(player.getYaw(tickProgress)-state.bodyYaw),-85f,85f);
        state.limbSwingAmplitude=0f;
        state.limbSwingAnimationProgress=0f;
        state.handSwingProgress=0f;
        state.leaningPitch=0f;
        state.isInSneakingPose=false;
        state.capeVisible=false;
    }
}
"""
p=root/"mixin/PlayerRidingStateMixin.java"
p.write_text(render_mixin,encoding="utf-8")

# Override all walking poses while mounted. Preserve normal vanilla limb/cosmetic
# behaviour immediately upon dismount, even when PlayerEntityModel is reused.
pose="""package dev.pitbike.stunt.mixin;

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

@Mixin(PlayerEntityModel.class)
public abstract class PlayerModelPoseMixin {
    @Inject(
        method = "setAngles(Lnet/minecraft/client/render/entity/state/PlayerEntityRenderState;)V",
        at = @At("TAIL"))
    private void pitbikestunt$fixSeatedRider(PlayerEntityRenderState state, CallbackInfo ci) {
        PlayerEntityModel model=(PlayerEntityModel)(Object)this;
        // Model instances are shared between players. Always restore these flags.
        model.rightSleeve.visible=state.rightSleeveVisible;
        model.leftSleeve.visible=state.leftSleeveVisible;
        model.rightPants.visible=state.rightPantsLegVisible;
        model.leftPants.visible=state.leftPantsLegVisible;
        model.jacket.visible=state.jacketVisible;
        model.hat.visible=state.hatVisible;

        MinecraftClient client=MinecraftClient.getInstance();
        if (client.world==null) return;
        Entity player=client.world.getEntityById(state.id);
        if (player==null || !(player.getVehicle() instanceof PitbikeEntity bike)) return;

        // Repeated player walking/swimming/emote animations cannot move the torso.
        model.body.pitch=.12f;
        model.body.yaw=0f;
        model.body.roll=0f;
        model.body.originX=0f;
        model.body.originZ=0f;
        model.rightArm.pitch=-1.19f;
        model.leftArm.pitch=-1.19f;
        model.rightArm.yaw=-.27f;
        model.leftArm.yaw=.27f;
        model.rightArm.roll=-.10f;
        model.leftArm.roll=.10f;
        model.rightLeg.pitch=-.90f;
        model.leftLeg.pitch=-.90f;
        model.rightLeg.yaw=0f;
        model.leftLeg.yaw=0f;
        model.rightLeg.roll=.09f;
        model.leftLeg.roll=-.09f;

        // Activated stunt moves retain their distinctive poses. Normal riding
        // only moves the player's head, not the body, arms, or legs.
        switch (bike.trick()) {
            case 1 -> model.leftLeg.pitch=.55f; // flamingo
            case 2,4 -> {
                model.rightArm.pitch=-2.4f;
                model.leftArm.pitch=-2.4f;
            }
            case 3 -> model.rightArm.pitch=-2.4f; // one-hand
            case 5 -> {
                model.body.pitch=.83f;
                model.rightLeg.pitch=.62f;
                model.leftLeg.pitch=.62f;
            }
            case 6 -> {
                model.rightLeg.pitch=-.12f;
                model.leftLeg.pitch=-.12f;
                model.body.pitch=0f;
            }
            default -> { }
        }
        // No detached outer-layer meshes hovering beside the wheel or body.
        // Head's hat follows the head, while sleeves/pants/jacket are hidden
        // only when riding. Skin itself is always shown.
        model.hat.setTransform(model.head.getTransform());
        model.rightSleeve.visible=false;
        model.leftSleeve.visible=false;
        model.rightPants.visible=false;
        model.leftPants.visible=false;
        model.jacket.visible=false;
    }
}
"""
p=root/"mixin/PlayerModelPoseMixin.java"
p.write_text(pose,encoding="utf-8")
config=resources/"pitbikestunt.mixins.json"
data=json.loads(config.read_text(encoding="utf-8"))
assert "PlayerModelPoseMixin" in data["client"]
data["client"]=["PlayerModelPoseMixin","PlayerRidingStateMixin"]
config.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
print("Added fixed third-person torso, head-only look, aligned hands and clean skin overlays")
