from pathlib import Path

root = Path("project/src/main/java/dev/pitbike/stunt")
p = root / "entity/PitbikeEntity.java"
s = p.read_text()
before = "    @Override public boolean isCollidable() { return true; }"
assert before in s
s = s.replace(before, "    @Override public boolean canHit() { return true; }\n" + before)
before = """        if (!getWorld().isClient && !player.hasVehicle()) {
            dataTracker.set(KICKSTAND, false);
            player.startRiding(this);
        }
"""
after = """        if (!getWorld().isClient && !player.hasVehicle()) {
            dataTracker.set(KICKSTAND, false);
            if (player.startRiding(this, true)) {
                player.sendMessage(Text.literal("Pitbike: mounted. Shift to dismount."), true);
            } else {
                player.sendMessage(Text.literal("Pitbike: seat unavailable."), true);
            }
        }
"""
assert before in s
p.write_text(s.replace(before, after))

p = root / "item/BikeItem.java"
s = p.read_text()
before = """        context.getWorld().spawnEntity(bike);
        if (context.getPlayer() != null && !context.getPlayer().getAbilities().creativeMode)
            context.getStack().decrement(1);
"""
after = """        boolean spawned = context.getWorld().spawnEntity(bike);
        if (!spawned) return ActionResult.FAIL;
        if (context.getPlayer() != null) {
            if (!context.getPlayer().isSneaking() && !context.getPlayer().hasVehicle())
                context.getPlayer().startRiding(bike, true);
            if (!context.getPlayer().getAbilities().creativeMode)
                context.getStack().decrement(1);
        }
"""
assert before in s
p.write_text(s.replace(before, after))

p = root / "PitbikeStunt.java"
s = p.read_text()
assert ".dimensions(0.98f, 1.25f)" in s
p.write_text(s.replace(".dimensions(0.98f, 1.25f)", ".dimensions(1.25f, 1.35f)"))
print("Mounting and crosshair fixes applied")
