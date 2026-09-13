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

        // The beam is a clean effect based on player direction, not a cloud of leaf particles.
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

        // Sakura petal mode only spawns while the player is actually moving.
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
        int count = 10;
        double radius = 0.15D;
        ColorParticleOption petal = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, 0xFFFFE3F0);

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
        // Triangular glowing wedge like the reference: narrow at the player and wider behind.
        // DUST only, so there are no giant leaf-shaped particles.
        DustParticleOptions core = new DustParticleOptions(SakuraVisualsClient.accent(), 0.55F);
        DustParticleOptions glow = new DustParticleOptions(SakuraVisualsClient.accentLight(), 0.32F);

        double sideX = -backZ;
        double sideZ = backX;
        int depthSteps = 7;
        int heightSteps = 5;

        for (int d = 0; d < depthSteps; d++) {
            double depthT = d / (double) (depthSteps - 1);
            double depth = 0.18D + depthT * 1.65D;
            double halfWidth = 0.04D + depthT * 0.62D;
            double centerX = x + backX * depth;
            double centerZ = z + backZ * depth;

            for (int h = 0; h < heightSteps; h++) {
                double heightT = h / (double) (heightSteps - 1);
                double yy = y + 0.08D + heightT * 1.62D;

                // Three clean stripes across the wedge instead of a chaotic particle cloud.
                for (int s = -1; s <= 1; s++) {
                    double lateral = halfWidth * s;
                    double px = centerX + sideX * lateral;
                    double pz = centerZ + sideZ * lateral;
                    mc.level.addParticle(core, px, yy, pz, 0.0D, 0.0D, 0.0D);
                }

                // Bright edges make the wedge read as a single beam.
                if (h == 0 || h == heightSteps - 1) {
                    mc.level.addParticle(glow,
                            centerX + sideX * halfWidth, yy, centerZ + sideZ * halfWidth,
                            0.0D, 0.0D, 0.0D);
                    mc.level.addParticle(glow,
                            centerX - sideX * halfWidth, yy, centerZ - sideZ * halfWidth,
                            0.0D, 0.0D, 0.0D);
                }
            }
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
