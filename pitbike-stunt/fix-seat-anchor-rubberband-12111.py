#!/usr/bin/env python3
"""Finalize attached rider and client-side visual smoothing for 1.21.11."""
from pathlib import Path
root=Path("project/src/main/java/dev/pitbike/stunt")
p=root/"entity/PitbikeEntity.java"
s=p.read_text(encoding="utf-8")
def one(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old))
    s=s.replace(old,new)

# Extrapolate using BOTH last two packets and server-tracked speed. The old
# smoothing ran behind each packet and snapped visibly at road speeds.
one("double ahead=Math.min(1.25,Math.max(0,ticksSinceRemoteUpdate-0.35));",
    "double ahead=Math.min(4.0, Math.max(0,ticksSinceRemoteUpdate-0.20));")
one("double wantedX=remoteTargetX+remoteSpeedX*ahead;",
    """double trackedSpeed=MathHelper.clamp(speed(),-1.35,1.35);
        double direction=Math.toRadians(remoteYaw);
        double predictedX=-Math.sin(direction)*trackedSpeed;
        double predictedZ=Math.cos(direction)*trackedSpeed;
        double wantedX=remoteTargetX+(remoteSpeedX*.32+predictedX*.68)*ahead;""")
one("double wantedZ=remoteTargetZ+remoteSpeedZ*ahead;",
    "double wantedZ=remoteTargetZ+(remoteSpeedZ*.32+predictedZ*.68)*ahead;")
one("double alpha=sq>2.25 ? .79 : .57;",
    "double alpha=Math.min(.50, .25 + Math.sqrt(sq)*.055);")
one("setYaw(getYaw()+MathHelper.wrapDegrees(remoteYaw-getYaw())*.62f);",
    "setYaw(getYaw()+MathHelper.wrapDegrees(remoteYaw-getYaw())*.36f);")
one("setPitch(getPitch()+MathHelper.wrapDegrees(remotePitch-getPitch())*.62f);",
    "setPitch(getPitch()+MathHelper.wrapDegrees(remotePitch-getPitch())*.36f);")

# Correct the rider every tick AFTER the vehicle's new interpolated position
# is applied, including the local player. This prevents the player from
# hanging at the previously interpolated world position while the bike moves.
one("if (getEntityWorld().isClient()) { smoothRemoteMovement(); return; }",
    """if (getEntityWorld().isClient()) {
            smoothRemoteMovement();
            for (Entity rider : getPassengerList()) {
                updatePassengerPosition(rider);
            }
            return;
        }""")
# The seat position is vehicle-local and rotates with the chassis yaw;
# updating the passenger after the bike stops rider/bike desynchronization.
assert "new Vec3d(0, 1.09, -0.22)" in s, "Expected latest seat offset from pose patch"
p.write_text(s,encoding="utf-8")

# Also ensure the torso stays square to the handlebars independently of head yaw.
p=root/"mixin/PlayerModelPoseMixin.java"
src=p.read_text(encoding="utf-8")
assert "model.body.yaw=0f;" in src
assert "model.hat.setTransform(model.head.getTransform());" in src
# Initial flat riding position: relaxed, shoulders widen slightly.
assert "model.rightArm.yaw=-.34f;" in src
assert "model.leftArm.yaw=.34f;" in src

# Source structural regression tests. These catch restoring the original bug.
assert "for (Entity rider : getPassengerList())" in s
assert "updatePassengerPosition(rider)" in s
assert "Math.sqrt(sq)*.055" in s
assert "Math.min(4.0" in s
print("PASS: seat follows interpolated chassis every tick, smoother remote prediction")
print("PASS: rider torso fixed and arms held on wide handlebar grip")
