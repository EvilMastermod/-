from pathlib import Path
r=Path("project/src/main/java/dev/pitbike/stunt")
def edit(name,fn):
    p=r/name
    old=p.read_text()
    new=fn(old)
    assert new!=old,name
    p.write_text(new)
    print("Patched",name)
def sub(s,old,new):
    assert s.count(old)==1,(old,s.count(old))
    return s.replace(old,new)
def physics(s):
    s=sub(s,"    public static double clamp(", """    public static double wheelContactLift(double pitch) {
        double c=Math.cos(pitch), sn=Math.sin(pitch);
        if(pitch>=0) return Math.max(0,(6.6/16.0)*(1-c)+(12.6/16.0)*sn);
        return Math.max(0,(6.8/16.0)*(1-c)-(13.1/16.0)*sn);
    }
    public static double clamp(""")
    s=sub(s,"clamp(s.pitch + angularMomentum, -0.65, 1.45)","clamp(s.pitch + angularMomentum, -0.56, 0.98)")
    s=sub(s,"verticalImpact * 0.42 + Math.abs(terrainPitch) * 0.24","verticalImpact * 0.58 + Math.abs(terrainPitch) * 0.56")
    s=sub(s,"0, 0.35);\n        double fork","0, 0.44);\n        double fork")
    s=sub(s,"(i.brake ? 0.10 : 0), 0.24","(i.brake ? 0.12 : 0), 0.22")
    return sub(s,"(i.throttle ? 0.025 : 0), 0.17","(i.throttle ? 0.040 : 0), 0.18")
edit("physics/BikePhysics.java",physics)
def renderer(s):
    k="matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-state.yaw));"
    s=sub(s,k,k+"""
        // Compensate rotation of the donor mesh around the supporting wheel.
        matrices.translate(0.0, dev.pitbike.stunt.physics.BikePhysics.wheelContactLift(state.pitchAngle), 0.0);""")
    return sub(s,"state.wheelTravel=bike.wheelTravel();","state.wheelTravel=bike.wheelTravel() + bike.speed() * 2.6f * progress;")
edit("client/PitbikeRenderer.java",renderer)
def suspension(s):
    s=sub(s,"compress = -state.fork() * 0.43f;","compress = state.fork() * 0.62f;")
    s=sub(s,"rearLean = -state.shock() * 0.39f;","rearLean = state.shock() * 0.42f;")
    return sub(s,"rearLean = state.shock() * 0.19f;","rearLean = -state.shock() * 0.16f;")
edit("client/DonorMesh.java",suspension)
def entity(s):
    s=sub(s,"return 0.70f;","return 0.54f;")
    s=sub(s,"new Vec3d(0, 0.79, -0.08)","new Vec3d(0, 0.52, -0.35)")
    ctor="    public PitbikeEntity(EntityType<? extends PitbikeEntity> type, World world) { super(type, world); }"
    smooth="""    private int smoothTicks;
    private double targetX,targetY,targetZ;
    private float targetYaw,targetPitch;
    @Override protected void lerpPosAndRotation(int steps, double x, double y,
                                                 double z, double yaw, double pitch) {
        if (!getEntityWorld().isClient()) {
            super.lerpPosAndRotation(steps,x,y,z,yaw,pitch);
            return;
        }
        targetX=x; targetY=y; targetZ=z;
        targetYaw=(float)yaw; targetPitch=(float)pitch;
        smoothTicks=Math.max(2,Math.min(5,steps));
    }
    private void smoothRemoteMovement() {
        if(smoothTicks<=0) return;
        double t=1.0/smoothTicks;
        setPosition(getX()+(targetX-getX())*t,
            getY()+(targetY-getY())*t,
            getZ()+(targetZ-getZ())*t);
        setYaw(getYaw()+MathHelper.wrapDegrees(targetYaw-getYaw())*(float)t);
        setPitch(getPitch()+MathHelper.wrapDegrees(targetPitch-getPitch())*(float)t);
        smoothTicks--;
    }
"""
    s=sub(s,ctor,ctor+"\n"+smooth)
    return sub(s,"    @Override public void tick() {\n        super.tick();\n        if (getEntityWorld().isClient()) return;",
               "    @Override public void tick() {\n        super.tick();\n        if (getEntityWorld().isClient()) { smoothRemoteMovement(); return; }")
edit("entity/PitbikeEntity.java",entity)
def rider(s):
    pairs={
        "right.pitch = -1.23f - lean;":"right.pitch = -1.03f - lean;",
        "left.pitch = -1.23f - lean;":"left.pitch = -1.03f - lean;",
        "right.yaw = -0.38f - steer * 0.19f;":"right.yaw = -0.27f - steer * 0.16f;",
        "left.yaw = 0.38f - steer * 0.19f;":"left.yaw = 0.27f - steer * 0.16f;",
        "model.body.pitch = 0.20f + lean;":"model.body.pitch = 0.15f + lean;",
        "model.rightLeg.pitch = -1.02f;":"model.rightLeg.pitch = -0.66f;",
        "model.leftLeg.pitch = -1.02f;":"model.leftLeg.pitch = -0.66f;",
        "model.rightLeg.roll = 0.12f;":"model.rightLeg.roll = 0.08f;",
        "model.leftLeg.roll = -0.12f;":"model.leftLeg.roll = -0.08f;"
    }
    for a,b in pairs.items(): s=sub(s,a,b)
    return s
edit("mixin/PlayerModelPoseMixin.java",rider)
p=Path("project/src/test/java/dev/pitbike/stunt/physics/BikePhysicsSelfTest.java")
s=p.read_text()
needle='        System.out.println("PASS: 11 independent physics checks");'
checks="""        double u=0.7,d=-0.42;
        double ry=6.6/16.0,rz=-12.6/16.0,fy=6.8/16.0,fz=13.1/16.0;
        check(Math.abs(ry*Math.cos(u)+rz*Math.sin(u)+BikePhysics.wheelContactLift(u)-ry)<0.00001,"wheelie contact");
        check(Math.abs(fy*Math.cos(d)+fz*Math.sin(d)+BikePhysics.wheelContactLift(d)-fy)<0.00001,"stoppie contact");
        check(BikePhysics.wheelContactLift(0)==0,"flat terrain");
        System.out.println("PASS: three wheel-grounding checks");
"""
p.write_text(sub(s,needle,checks+needle))
print("Completed client smoothing, donor tire contact, shock and pose patches.")
