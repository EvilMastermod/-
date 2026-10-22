#!/usr/bin/env python3
"""Tuned real server-side speeds for all six Pitbike Stunt bikes (Minecraft 1.21.11).
The game HUD uses velocity * 72 km/h, so numbers below represent actual limits.
Runs after unpacking/migration, before Gradle compilation.
"""
from pathlib import Path

root=Path("project/src")
variant=root/"main/java/dev/pitbike/stunt/entity/BikeVariant.java"
s=variant.read_text(encoding="utf-8")
targets = {
    "PITBIKE_125": ("Pitbike 125cc", 0.83, 0.0190, 0.052),
    "PITBIKE_140": ("Pitbike 140cc", 0.97, 0.0210, 0.056),
    "PITBIKE_160": ("Pitbike 160cc", 1.11, 0.0230, 0.060),
    "PITBIKE_190": ("Pitbike 190cc", 1.25, 0.0250, 0.065),
    "SUPERMOTO": ("Pitbike Supermoto", 1.18, 0.0240, 0.068),
    "STUNT_EDITION": ("Pitbike Stunt Edition", 1.04, 0.0240, 0.059),
}
import re
for key,(title,top,accel,brake) in targets.items():
    pat = rf'({key}\("{re.escape(title)}", )([0-9.]+), ([0-9.]+), ([0-9.]+),'
    match = list(re.finditer(pat,s))
    assert len(match)==1,(key, "missing/duplicate variant profile")
    s=re.sub(pat,rf'\g<1>{top:.3f}, {accel:.4f}, {brake:.3f},',s,count=1)
    print(f"{title}: {top*72:.1f} km/h in gear 4 (before optional config speed multiplier)")
variant.write_text(s,encoding="utf-8")

# Gear one starts with more usable speed, while gear four keeps the full top speed.
entity=root/"main/java/dev/pitbike/stunt/entity/PitbikeEntity.java"
s=entity.read_text(encoding="utf-8")
old="double gearFactor = 0.60 + gear() * 0.10;"
new="double gearFactor = 0.80 + gear() * 0.05;"
assert s.count(old)==1,("expected gearing expression missing", s.count(old))
entity.write_text(s.replace(old,new),encoding="utf-8")

# Independent regression checks: positive W throttle and each of the six new top speeds.
test=root/"test/java/dev/pitbike/stunt/physics/BikePhysicsSelfTest.java"
s=test.read_text(encoding="utf-8")
mark="        System.out.println(\"PASS: 11 independent physics checks\");"
assert s.count(mark)==1,"expected test completion marker missing"
checks='''        double[] expectedKmh = {59.76,69.84,79.92,90.00,84.96,74.88};
        dev.pitbike.stunt.entity.BikeVariant[] variants =
                dev.pitbike.stunt.entity.BikeVariant.values();
        check(variants.length == expectedKmh.length, "six distinct variant speeds");
        for (int k = 0; k < variants.length; k++) {
            var v = variants[k];
            check(Math.abs(v.maxSpeed * 72.0 - expectedKmh[k]) < 0.01,
                    "correct max speed for " + v.title);
            BikePhysics.State run = zero;
            BikePhysics.Setup profile = new BikePhysics.Setup(v.maxSpeed, v.acceleration,
                    v.braking, v.wheeliePower, 0.92);
            for (int tick = 0; tick < 200; tick++)
                run = BikePhysics.integrate(run, gas, profile, true, 0, 0);
            check(run.velocity() > 0 && run.velocity() <= v.maxSpeed + 0.00001,
                    "W accelerates forward without breaking speed limiter: " + v.title);
        }
        System.out.println("PASS: six speed profiles and forward acceleration");
'''
s=s.replace(mark,checks+mark)
test.write_text(s,encoding="utf-8")
print("Speed profiles, 1st-gear gearing and regression tests updated.")
