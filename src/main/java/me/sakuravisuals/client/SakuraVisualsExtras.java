package me.sakuravisuals.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.PlayerFaceRenderer;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;

public final class SakuraVisualsExtras implements ClientModInitializer {
    private static int trailTick;
    private static double lastX = Double.NaN;
    private static double lastZ = Double.NaN;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(SakuraVisualsExtras::tickTrail);
        HudElementRegistry.addLast(
                Identifier.fromNamespaceAndPath(SakuraVisualsClient.MOD_ID, "player_card_skin"),
                (graphics, deltaTracker) -> renderSkinCard(graphics)
        );
    }

    private static void tickTrail(Minecraft mc) {
        if (mc == null || mc.player == null || mc.level == null || !SakuraVisualsClient.CONFIG.playerTrail) {
            lastX = Double.NaN;
            lastZ = Double.NaN;
            return;
        }

        trailTick++;

        double x = mc.player.getX();
        double y = mc.player.getY();
        double z = mc.player.getZ();

        // Beam mode: a clean geometric neon outline behind the player.
        // No petals and no wide particle cloud are used here.
        if (Math.floorMod(SakuraVisualsClient.CONFIG.trailMode, 2) == 1) {
            if ((trailTick & 1) == 0) {
                double yaw = Math.toRadians(mc.player.getYRot());
                double backX = Math.sin(yaw);
                double backZ = -Math.cos(yaw);
                spawnColorBeam(mc, x, y, z, backX, backZ);
            }
            lastX = x;
            lastZ = z;
            return;
        }

        // Sakura petal mode only spawns while moving.
        if (trailTick % 3 != 0) return;
        if (Double.isNaN(lastX)) {
            lastX = x;
            lastZ = z;
            return;
        }

        double dx = x - lastX;
        double dz = z - lastZ;
        lastX = x;
        lastZ = z;
        if (dx * dx + dz * dz < 0.00004D) return;

        double len = Math.sqrt(dx * dx + dz * dz);
        double backX = len > 0.00001D ? -dx / len : 0.0D;
        double backZ = len > 0.00001D ? -dz / len : 0.0D;
        spawnPetalColumn(mc, x + backX * 0.25D, y, z + backZ * 0.25D);
    }

    private static void spawnPetalColumn(Minecraft mc, double x, double y, double z) {
        int count = 12;
        double radius = 0.16D;
        ColorParticleOption petal = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, 0xFFFFECF5);

        for (int i = 0; i < count; i++) {
            double t = i / (double) (count - 1);
            double yy = y + 0.05D + t * 1.80D;
            double phase = trailTick * 0.46D + i * 1.60D;
            double ox = Math.sin(phase) * radius;
            double oz = Math.cos(phase) * radius;
            mc.level.addParticle(petal, x + ox, yy, z + oz, 0.0D, 0.008D, 0.0D);
        }
    }

    private static void spawnColorBeam(Minecraft mc, double x, double y, double z, double backX, double backZ) {
        // Clean line/beam shaped like the reference: narrow at the player and wider behind.
        // The effect is made from a few continuous neon edge lines, not a cloud.
        DustParticleOptions main = new DustParticleOptions(SakuraVisualsClient.accent(), 0.34F);
        DustParticleOptions glow = new DustParticleOptions(SakuraVisualsClient.accentVeryLight(), 0.22F);

        double sideX = -backZ;
        double sideZ = backX;

        double nearDepth = 0.10D;
        double farDepth = 1.70D;
        double nearHalfWidth = 0.03D;
        double farHalfWidth = 0.50D;
        double bottomY = y + 0.06D;
        double topY = y + 1.76D;

        double nearCenterX = x + backX * nearDepth;
        double nearCenterZ = z + backZ * nearDepth;
        double farCenterX = x + backX * farDepth;
        double farCenterZ = z + backZ * farDepth;

        double nearLeftX = nearCenterX - sideX * nearHalfWidth;
        double nearLeftZ = nearCenterZ - sideZ * nearHalfWidth;
        double nearRightX = nearCenterX + sideX * nearHalfWidth;
        double nearRightZ = nearCenterZ + sideZ * nearHalfWidth;
        double farLeftX = farCenterX - sideX * farHalfWidth;
        double farLeftZ = farCenterZ - sideZ * farHalfWidth;
        double farRightX = farCenterX + sideX * farHalfWidth;
        double farRightZ = farCenterZ + sideZ * farHalfWidth;

        // Four main perspective edges.
        spawnLine(mc, main, nearLeftX, bottomY, nearLeftZ, farLeftX, bottomY, farLeftZ, 28);
        spawnLine(mc, main, nearRightX, bottomY, nearRightZ, farRightX, bottomY, farRightZ, 28);
        spawnLine(mc, main, nearLeftX, topY, nearLeftZ, farLeftX, topY, farLeftZ, 28);
        spawnLine(mc, main, nearRightX, topY, nearRightZ, farRightX, topY, farRightZ, 28);

        // Vertical far edge makes it read as one clean luminous panel/line effect.
        spawnLine(mc, glow, farLeftX, bottomY, farLeftZ, farLeftX, topY, farLeftZ, 24);
        spawnLine(mc, glow, farRightX, bottomY, farRightZ, farRightX, topY, farRightZ, 24);

        // One soft center line gives the beam a solid readable core without turning into a particle cloud.
        spawnLine(mc, glow,
                nearCenterX, y + 0.90D, nearCenterZ,
                farCenterX, y + 0.90D, farCenterZ,
                30);
    }

    private static void spawnLine(
            Minecraft mc,
            DustParticleOptions particle,
            double x0, double y0, double z0,
            double x1, double y1, double z1,
            int steps
    ) {
        int safeSteps = Math.max(2, steps);
        for (int i = 0; i < safeSteps; i++) {
            double t = i / (double) (safeSteps - 1);
            double px = x0 + (x1 - x0) * t;
            double py = y0 + (y1 - y0) * t;
            double pz = z0 + (z1 - z0) * t;
            mc.level.addParticle(particle, px, py, pz, 0.0D, 0.0D, 0.0D);
        }
    }

    static int playerCardBaseWidth(Minecraft mc) {
        if (mc == null || mc.player == null) return 170;
        return Math.max(170, mc.font.width(mc.player.getName().getString()) + 82);
    }

    static int playerCardBaseHeight() {
        return 51;
    }

    private static void renderSkinCard(GuiGraphics g) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || !SakuraVisualsClient.CONFIG.playerCard) return;

        String name = mc.player.getName().getString();
        float hp = mc.player.getHealth();
        float maxHp = Math.max(1.0F, mc.player.getMaxHealth());
        float ratio = Math.max(0.0F, Math.min(1.0F, hp / maxHp));

        int accent = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentLight();
        int width = playerCardBaseWidth(mc);
        int height = playerCardBaseHeight();
        int head = 32;
        float scale = SakuraVisualsClient.clampScale(SakuraVisualsClient.CONFIG.playerCardScale);

        var matrices = g.pose();
        matrices.pushMatrix();
        matrices.translate(SakuraVisualsClient.CONFIG.playerCardX, SakuraVisualsClient.CONFIG.playerCardY);
        matrices.scale(scale, scale);

        g.fill(0, 0, width, height, 0xEC120C18);
        g.fill(0, 0, 3, height, accent);
        g.fill(3, 0, width, 2, 0x66FFFFFF & light | 0x66000000);

        g.fill(7, 7, 7 + head + 4, 7 + head + 4, 0xFF2A1825);
        g.fill(8, 8, 8 + head + 2, 8 + head + 2, accent);
        PlayerFaceRenderer.draw(g, mc.player.getSkin(), 10, 10, head - 2);

        int tx = 48;
        g.drawString(mc.font, name, tx, 8, light, true);
        g.drawString(mc.font, String.format("HP %.1f / %.1f", hp, maxHp), tx, 21, 0xFFFFFFFF, true);

        int barW = Math.max(54, width - tx - 10);
        int fillW = (int) (barW * ratio);
        int barY = 36;
        g.fill(tx, barY, tx + barW, barY + 8, 0xFF291922);
        g.fill(tx, barY, tx + fillW, barY + 8, accent);
        g.fill(tx, barY, tx + fillW, barY + 3, light);

        SakuraVisualsClient.blossom(g, width - 14, 7);
        SakuraVisualsClient.blossom(g, width - 23, height - 12);

        matrices.popMatrix();
    }
}
