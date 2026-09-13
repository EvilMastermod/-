package me.sakuravisuals.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.PlayerFaceRenderer;
import net.minecraft.core.particles.ColorParticleOption;
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
        if ((trailTick & 1) != 0) return;

        double x = mc.player.getX();
        double y = mc.player.getY();
        double z = mc.player.getZ();
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
        double px = x + backX * 0.28D;
        double pz = z + backZ * 0.28D;

        if (Math.floorMod(SakuraVisualsClient.CONFIG.trailMode, 2) == 0) {
            spawnPetalColumn(mc, px, y, pz);
        } else {
            spawnColorLine(mc, px, y, pz);
        }
    }

    private static void spawnPetalColumn(Minecraft mc, double x, double y, double z) {
        int count = 8;
        double radius = 0.15D;
        ColorParticleOption light = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, SakuraVisualsClient.accentVeryLight());

        for (int i = 0; i < count; i++) {
            double t = i / (double) (count - 1);
            double yy = y + 0.05D + t * 1.80D;
            double phase = trailTick * 0.47D + i * 1.61D;
            double ox = Math.sin(phase) * radius;
            double oz = Math.cos(phase) * radius;
            mc.level.addParticle(light, x + ox, yy, z + oz, 0.0D, 0.009D, 0.0D);
        }
    }

    private static void spawnColorLine(Minecraft mc, double x, double y, double z) {
        int count = 24;
        ColorParticleOption line = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, SakuraVisualsClient.accentLight());
        ColorParticleOption glow = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, SakuraVisualsClient.accentVeryLight());

        for (int i = 0; i < count; i++) {
            double t = i / (double) (count - 1);
            double yy = y + 0.03D + t * 1.84D;
            mc.level.addParticle(line, x, yy, z, 0.0D, 0.0D, 0.0D);
            if ((i & 2) == 0) {
                mc.level.addParticle(glow, x + 0.025D, yy, z, 0.0D, 0.0D, 0.0D);
                mc.level.addParticle(glow, x - 0.025D, yy, z, 0.0D, 0.0D, 0.0D);
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
